import socketio
import logging
import asyncio
from typing import Dict, List

logger = logging.getLogger(__name__)


# Create a new instance of an ASGI-compatible Socket.IO server
ALLOW_ORIGINS=[
        "https://fastapi-8vlc6b.chbk.app",
        "https://services.irn8.chabokan.net",
        "https://91.236.169.133"
    ],
tcp_sio = socketio.AsyncServer(
    async_mode='asgi',  # Use ASGI mode for FastAPI compatibility
    cors_allowed_origins="*",  # Allow all origins for CORS; adjust as needed
    # cors_allowed_origins=ALLOW_ORIGINS,  # Allow all origins for CORS; adjust as needed
    logger=True,
    engineio_logger=True
)

# Maps to manage client subscriptions
request_map = {
    "live": {},  # Format: {"sid": {cameraID1, cameraID2, ...}}
    "plates_data": {}  # Format: {"sid": {cameraID1, cameraID2, ...}}
}

sid_role_map = {}  # Maps SID to roles (e.g., {"sid1": "admin", "sid2": "operator"})


@tcp_sio.event
async def connect(sid, environ):
    """
    Event triggered when a client connects to the WebSocket.
    """
    print(f"New client connected: {sid}")
    asyncio.create_task(tcp_sio.emit("connection_ack", {"message": "Connected"}, to=sid))
    logger.info(f"Client connected: {sid}")
    request_map["live"][sid] = set()
    request_map["plates_data"][sid] = set()
    return True


@tcp_sio.event
async def disconnect(sid):
    """
    Event triggered when a client disconnects from the WebSocket.
    """
    logger.info(f"Client disconnected: {sid}")
    # Remove all subscriptions and role mappings for the client
    sid_role_map.pop(sid, None)
    request_map["live"].pop(sid, None)
    request_map["plates_data"].pop(sid, None)


@tcp_sio.event
async def subscribe(sid, data):
    """
    Allows clients to subscribe to specific events.
    """
    print(f"Received request from {sid}: {data}")
    role = sid_role_map.get(sid, "admin")
    request_type = data.get("request_type")
    camera_id = data.get("camera_id")
    if not camera_id:
        asyncio.create_task(tcp_sio.emit('error', {'message': 'camera_id is required'}, to=sid))


    asyncio.create_task(tcp_sio.emit("response", {"message": f"Handling {request_type} for {camera_id}"}, to=sid))
    # Update the request map based on the request type and role
    if request_type == "live":
        request_map["live"].setdefault(sid, set()).add(camera_id)
        logger.info(f"Client {sid} subscribed to live data for camera_id {camera_id}")
        asyncio.create_task(tcp_sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "live", "camera_id": camera_id}, to=sid))

    elif request_type == "plates_data":
        request_map["plates_data"].setdefault(sid, set()).add(camera_id)
        logger.info(f"Client {sid} subscribed to plate data for camera_id {camera_id}")
        asyncio.create_task(tcp_sio.emit('request_acknowledged', {"status": "subscribed", "data_type": "plate", "camera_id": camera_id}, to=sid))

    else:
        logger.warning(f"Client {sid} attempted unauthorized access to {request_type}")
        asyncio.create_task(tcp_sio.emit('error', {'message': 'Unauthorized to access this data'}, to=sid))



@tcp_sio.event
async def unsubscribe(sid, data):
    """
    Allows clients to unsubscribe from specific events.
    """
    request_type = data.get("request_type")
    camera_id = data.get("camera_id")

    if request_type in request_map and sid in request_map[request_type]:
        if camera_id in request_map[request_type][sid]:
            request_map[request_type][sid].remove(camera_id)
            logger.info(f"Client {sid} unsubscribed from {request_type} data for camera_id {camera_id}")
            asyncio.create_task(tcp_sio.emit('request_acknowledged', {"status": "unsubscribed", "data_type": request_type, "camera_id": camera_id}, to=sid))

        if not request_map[request_type][sid]:  # If no more subscriptions for this sid
            del request_map[request_type][sid]

    else:
        logger.warning(f"Client {sid} attempted to unsubscribe from {request_type} without a valid subscription")
        asyncio.create_task(tcp_sio.emit('error', {'message': 'You are not subscribed to this data type or camera_id'}, to=sid))


async def emit_to_requested_sids(event_name, data, camera_id=None):
    """
    Emits an event with data to all clients subscribed to the event.
    """
    if event_name not in request_map:
        logger.error(f"Invalid event name: {event_name}")
        return

    tasks = []
    for sid, camera_ids in request_map[event_name].items():
        if camera_id is None or camera_id in camera_ids:  # Check if the client is subscribed to the cameraID
            try:
                asyncio.create_task(tcp_sio.emit(event_name, data, to=sid))
                # tasks.append(asyncio.create_task(tcp_sio.emit(event_name, data, to=sid)))
                logger.info(f"Emitted {event_name} to SID {sid} for camera_id {camera_id}")
            except Exception as e:
                logger.error(f"Failed to emit {event_name} to SID {sid}: {e}")
    # Execute all emission tasks concurrently
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"Emitted {event_name} to all subscribed clients")
