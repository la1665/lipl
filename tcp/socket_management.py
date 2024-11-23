import os
import jwt
import asyncio
from fastapi import FastAPI
from socketio import AsyncServer
import time
from threading import Lock

from http.cookies import SimpleCookie

ALLOWED_ORIGINS = ["https://fastapi-8vlc6b.chbk.app", "https://services.irn8.chabokan.net", "https://91.236.169.133"]
sio = AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app_socket = FastAPI()

session_tokens = {}
sid_role_map = {}
SECRET_KEY = "your_secret_key"
TOKEN_CHECK_INTERVAL = 300

# Request and Emit Settings
request_map = {
    "live": {},       # Dictionary to store {sid: cameraID} for "live" requests
    "plates_data": {} # Dictionary to store {sid: cameraID} for "plates_data" requests
}
last_live_emit_time = 0
LIVE_EMIT_INTERVAL = 1
emit_lock = Lock()

def is_token_valid(sid):
    """Check if the token for a given sid is valid and unexpired."""
    token = session_tokens.get(sid)
    if not token:
        return False
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False

async def conditional_token_check(sid):
    while True:
        await asyncio.sleep(TOKEN_CHECK_INTERVAL)
        if not sio.manager.is_connected(sid):
            break
        if not is_token_valid(sid):
            await sio.disconnect(sid)
            break

@sio.event
async def connect(sid, environ):
    client_ip = environ.get('REMOTE_ADDR', 'Unknown IP')
    auth_token = environ.get("HTTP_COOKIE", "")
    print("Raw cookie header:", auth_token)

    # Log the client IP for debugging
    print("Client IP:", client_ip)

    # Validate CSRF token and retrieve associated auth_token if valid
    # auth_token =  auth_token.split("=")[-1]
    # Parse cookies to extract the auth_token
    from http.cookies import SimpleCookie
    cookie = SimpleCookie()
    cookie.load(auth_token)
    auth_token = cookie.get("auth_token").value if "auth_token" in cookie else None

    print("Extracted auth_token:", auth_token)
    if auth_token is None:
        print("Invalid or expired token")
        return False  # Reject connection if CSRF token is invalid or expired

    try:
        # Decode and validate the auth_token to get the user role
        print("Token received for validation:", auth_token)

        decoded_token = jwt.decode(auth_token, SECRET_KEY, algorithms=["HS256"])
        print("decode token:", decoded_token)
        role = decoded_token.get("role", "viewer")

        # Store session and role mappings
        session_tokens[sid] = auth_token
        sid_role_map[sid] = role

        # Start periodic token check for this sid
        asyncio.create_task(conditional_token_check(sid))

        print(f"Connection accepted for role: {role}")
        return True  # Allow connection

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        print("Token validation failed:", e)
        return False  # Reject if token is expired or invalid


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
    session_tokens.pop(sid, None)
    sid_role_map.pop(sid, None)
    for data_type in request_map:
        request_map[data_type].pop(sid, None)

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
    if request_type == "live" and role == "admin":
        if sid not in request_map["live"]:
            request_map["live"][sid] = set()  # Initialize as set if not present
        request_map["live"][sid].add(cameraID)  # Add the cameraID to the sid's set
        await sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "live"}, to=sid)

    elif request_type == "plate" and role in ["admin", "operator"]:
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

@sio.event
async def ping_pong(sid, data):
    """Custom ping-pong event to verify connection."""
    print(f"Received ping from sid {sid}: {data}")
    await sio.emit('pong', {'message': 'pong'}, to=sid)
    print(f"Sent pong to sid {sid}")

async def emit_pings():
    """Emit pings to all connected clients periodically."""
    while True:
        await asyncio.sleep(60)  # Send a ping every 60 seconds
        connected_sids = list(sio.manager.connected.keys())
        for sid in connected_sids:
            await sio.emit('ping', {'message': 'ping'}, to=sid)
            print(f"Sent ping to sid {sid}")

# Attach Socket.IO server to FastAPI app
sio.attach(app_socket)

# Example endpoint to verify server is running
@app_socket.get("/")
async def root():
    return {"message": "Socket.IO server is running."}
