
import uvicorn
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from tcp.test_data import emit_plates_data_periodically
import socketio
from tcp.socket_management import tcp_sio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    task = asyncio.create_task(emit_plates_data_periodically())
    yield
    # Shutdown logic
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

# Create the FastAPI instance with lifespan
app = FastAPI(lifespan=lifespan)

# Mount Socket.IO ASGIApp
app_socket = socketio.ASGIApp(
    tcp_sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

def main():
    """
    Main entry point for running the FastAPI app with Socket.IO.
    """
    uvicorn.run("main:app_socket", host="0.0.0.0", port=8000, log_level="debug")

if __name__ == "__main__":
    main()
