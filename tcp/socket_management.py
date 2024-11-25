# tcp/socket_management.py

import os
import jwt
import asyncio
from socketio import AsyncServer
import time
from threading import Lock
from http.cookies import SimpleCookie

# Define Allowed Origins
ALLOWED_ORIGINS = [
    "https://fastapi-8vlc6b.chbk.app",
    "https://services.irn8.chabokan.net",
    "https://91.236.169.133"
]

# Initialize Socket.IO server with restricted CORS
sio = AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
    # cors_allowed_origins=ALLOWED_ORIGINS
)

# Session and Role Management
session_tokens = {}
sid_role_map = {}
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # Ensure to set this in your environment variables
TOKEN_CHECK_INTERVAL = 300  # 5 minutes

# Request and Emit Settings
request_map = {
    "live": {},       # Dictionary to store {sid: set(cameraIDs)} for "live" requests
    "plates_data": {} # Dictionary to store {sid: set(cameraIDs)} for "plates_data" requests
}
last_live_emit_time = 0
LIVE_EMIT_INTERVAL = 1  # 1 second
emit_lock = Lock()

def is_token_valid(sid):
    """Check if the token for a given sid is valid and unexpired."""
    token = session_tokens.get(sid)
    if not token:
        return False
    # try:
        # jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return True
    # except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
    #     return False

# async def conditional_token_check(sid):
#     """Periodically check if the token is still valid."""
#     while True:
#         await asyncio.sleep(TOKEN_CHECK_INTERVAL)
#         if not sio.manager.is_connected(sid):
#             break
#         if not is_token_valid(sid):
#             await sio.disconnect(sid)
#             break

@sio.event
async def connect(sid, environ):
    """Handle a new client connection."""
    client_ip = environ.get('REMOTE_ADDR', 'Unknown IP')
    auth_token = environ.get("HTTP_COOKIE", "")
    print(f"Raw cookie header from {sid}: {auth_token}")

    # Log the client IP for debugging
    print(f"Client IP for {sid}: {client_ip}")

    # Parse cookies to extract the auth_token
    cookie = SimpleCookie()
    cookie.load(auth_token)
    # auth_token_value = cookie.get("auth_token").value if "auth_token" in cookie else None
    auth_token_value = "test_1234"

    print(f"Extracted auth_token for {sid}: {auth_token_value}")
    # if auth_token_value is None:
    #     print(f"Invalid or expired token for {sid}")
    #     return False  # Reject connection if token is invalid or expired

    # try:
        # Decode and validate the auth_token to get the user role
    print(f"Token received for validation from {sid}: {auth_token_value}")

        # decoded_token = jwt.decode(auth_token_value, SECRET_KEY, algorithms=["HS256"])
        # print(f"Decoded token for {sid}: {decoded_token}")
    print(f"Decoded token for {sid}: {auth_token_value}")
        # role = decoded_token.get("role", "viewer")

        # Store session and role mappings
    session_tokens[sid] = auth_token_value
        # sid_role_map[sid] = role

        # Start periodic token check for this sid
        # asyncio.create_task(conditional_token_check(sid))

        # print(f"Connection accepted for {sid} with role: {role}")
    print(f"Connection accepted for {sid} with role: ADMIN")

        # Start the ping emitter task if not already running
        # if not hasattr(sio, 'ping_task'):
            # sio.ping_task = asyncio.create_task(emit_pings())

    return True  # Allow connection

    # except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
    #     print(f"Token validation failed for {sid}: {e}")
    #     return False  # Reject if token is expired or invalid

@sio.event
async def refresh_token(sid, new_token):
    """Handle token refresh to update the session token if valid."""
    try:
        # Validate the new token
        decoded_token = jwt.decode(new_token, SECRET_KEY, algorithms=["HS256"])
        session_tokens[sid] = new_token  # Update token if valid
        print(f"[INFO] Token for session {sid} successfully updated.")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        print(f"[ERROR] Invalid token for session {sid}. Disconnecting.")
        await sio.emit('error', {'message': 'Invalid or expired token.'}, to=sid)
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    session_tokens.pop(sid, None)
    sid_role_map.pop(sid, None)
    for data_type in request_map:
        request_map[data_type].pop(sid, None)
    print(f"Client {sid} disconnected and cleaned up.")


@sio.event
async def handle_request(sid, data):
    """Handle requests for live or plate data based on permissions."""
    if not is_token_valid(sid):
        await sio.emit('error', {'message': 'Invalid or expired token'}, to=sid)
        await sio.disconnect(sid)
        return

    role = sid_role_map.get(sid)
    request_type = data.get("request_type")
    cameraID = data.get("cameraID")

    if not cameraID:
        await sio.emit('error', {'message': 'cameraID is required'}, to=sid)
        return

    # Update the request map if the role permits access, using sets for multiple cameraIDs per sid
    # if request_type == "live" and role == "admin":
    if request_type == "live":
        if sid not in request_map["live"]:
            request_map["live"][sid] = set()  # Initialize as set if not present
        request_map["live"][sid].add(cameraID)  # Add the cameraID to the sid's set
        await sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "live"}, to=sid)

    # elif request_type == "plate" and role in ["admin", "operator"]:
    elif request_type == "plate":
        if sid not in request_map["plates_data"]:
            request_map["plates_data"][sid] = set()  # Initialize as set if not present
        request_map["plates_data"][sid].add(cameraID)  # Add the cameraID to the sid's set
        await sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "plate"}, to=sid)

    else:
        await sio.emit('error', {'message': 'Unauthorized to access this data'}, to=sid)

async def emit_to_requested_sids(data_type, data):
    """Emit data to all sids that have requested the specified data_type and matching cameraID."""
    global last_live_emit_time
    sids_to_notify = request_map.get(data_type, {})

    # Filter by cameraID in data
    if data_type == "plates_data":
        await asyncio.gather(
            *[
                sio.emit(data_type, data, to=sid)
                for sid, camera_ids in sids_to_notify.items()
                if data.get("camera_id") in camera_ids  # Only emit if the data's cameraID matches one in the sid's set
            ]
        )

    elif data_type == "live":
        current_time = time.time()
        if current_time - last_live_emit_time >= LIVE_EMIT_INTERVAL:
            await asyncio.gather(
                *[
                    sio.emit(data_type, data, to=sid)
                    for sid, camera_ids in sids_to_notify.items()
                    if data.get("camera_id") in camera_ids  # Only emit if the data's cameraID matches one in the sid's set
                ]
            )
            last_live_emit_time = current_time
