import asyncio
import time
from threading import Lock
from socketio import AsyncServer
from urllib.parse import parse_qs

from db.engine import get_db  # Import your async_session
from authentication.access_level import get_user, get_current_user # Import your get_user function
from user.models import UserType

# Initialize Socket.IO server
sio = AsyncServer(async_mode="asgi", cors_allowed_origins='*')

# Session management
session_users = {}  # Maps sid to user object
sid_role_map = {}   # Maps sid to user role

# Request and Emit Settings
request_map = {
    "live": set(),
    "plates_data": set()
}

last_live_emit_time = 0
LIVE_EMIT_INTERVAL = 1  # Minimum interval between live data emits (in seconds)
emit_lock = Lock()

# async def get_user_from_token(token: str):
#     """
#     Authenticate the token and return the user.
#     """
#     async with async_session() as db:
#         user = await get_user(db, token)
#         return user

@sio.event
async def connect(sid, environ):
    """Handle new client connections."""
    # Extract token from query parameters or cookies
    token = None
    token = environ.get('HTTP_AUTHORIZATION')

    if not token:
        query_string = environ.get('QUERY_STRING', '')
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

    if not token:
        await sio.emit('error', {'message': 'Authentication token required'}, to=sid)
        return False

    # Authenticate the token
    user = await get_current_user(db=None, token=token)
    if user is None:
        await sio.emit('error', {'message': 'Invalid or expired token.'}, to=sid)
        return False

    # if not user.is_active:
    #     await sio.emit('error', {'message': 'Inactive user.'}, to=sid)
    #     return False

    # role = user.user_type.value  # Assuming user_type is an Enum

    # Store the user's role and other info
    session_users[sid] = user.id
    sid_role_map[sid] = user.user_type.value
    print(f"[INFO] Client connected with SID {sid} and role {role}")
    return True

@sio.event
async def disconnect(sid):
    """Handle client disconnections."""
    print(f"[INFO] Client disconnected with SID {sid}")
    session_users.pop(sid, None)
    sid_role_map.pop(sid, None)
    for data_type in request_map:
        request_map[data_type].discard(sid)

@sio.event
async def handle_request(sid, data):
    """Handle client requests for data."""
    user = session_users.get(sid)
    if user is None:
        await sio.emit('error', {'message': 'User not authenticated'}, to=sid)
        await sio.disconnect(sid)
        return

    role = sid_role_map.get(sid)
    request_type = data.get("request_type")
    camera_id = data.get("camera_id")

    if not camera_id:
        await sio.emit('error', {'message': 'camera_id is required'}, to=sid)
        return

    # Update the request map if the role permits access
    if request_type == "live" and role == UserType.ADMIN.value:
        request_map["live"].add(sid)
        await sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "live"}, to=sid)
        print(f"[INFO] SID {sid} subscribed to live data")
    elif request_type == "plate" and role in [UserType.ADMIN.value, UserType.STAFF.value]:
        request_map["plates_data"].add(sid)
        await sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "plate"}, to=sid)
        print(f"[INFO] SID {sid} subscribed to plate data")
    else:
        await sio.emit('error', {'message': 'Unauthorized to access this data'}, to=sid)
        print(f"[WARN] SID {sid} unauthorized request for {request_type}")

async def emit_to_requested_sids(data_type, data):
    """Emit data to all sids that have requested the specified data_type."""
    global last_live_emit_time

    sids_to_notify = request_map.get(data_type, set())
    with emit_lock:
        # if data_type == "plates_data":
        #     await asyncio.gather(*[sio.emit(data_type, data, to=sid) for sid in sids_to_notify])
        #     print(f"[INFO] Emitted plate data to {len(sids_to_notify)} clients")

        if data_type == "live":
            current_time = time.time()
            # if current_time - last_live_emit_time >= LIVE_EMIT_INTERVAL:
            #     await asyncio.gather(*[sio.emit(data_type, data, to=sid) for sid in sids_to_notify])
            #     last_live_emit_time = current_time
            #     print(f"[INFO] Emitted live data to {len(sids_to_notify)} clients")
            if current_time - last_live_emit_time < LIVE_EMIT_INTERVAL:
                return  # Skip if within interval
            last_live_emit_time = current_time
        await asyncio.gather(*[sio.emit(data_type, data, to=sid) for sid in sids_to_notify if sid in sid_role_map])
        print(f"[INFO] Emitted {data_type} to {len(sids_to_notify)} clients")
