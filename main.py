import reactor_setup
import uvicorn
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from lifespan import lifespan
from auth.router import auth_router
from user.router import user_router
from lpr.router import building_router, gate_router, camera_settings_router, camera_router, lpr_setting_router, lpr_router
from tcp.router import tcp_router
from tcp.socket_management import tcp_sio
# from tcp.socket_test import tcp_sio, start_emitter, set_event_loop
# from tcp.test_data import emit_plates_data_periodically
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)
logger.info("Starting FastAPI application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=[
    #         "https://fastapi-8vlc6b.chbk.app",
    #         "https://services.irn8.chabokan.net",
    #         "https://91.236.169.133"
    #     ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware added")

app.include_router(auth_router, tags=["Auth"])
app.include_router(user_router, tags=["User"])
app.include_router(building_router, tags=["Buildings"])
app.include_router(gate_router, tags=["Gates"])
app.include_router(camera_settings_router, tags=["Camera Settings"])
app.include_router(camera_router, tags=["Cameras"])
app.include_router(lpr_setting_router, tags=["Lpr settings"])
app.include_router(lpr_router, tags=["Lprs"])
app.include_router(tcp_router, tags=["tcp"])
logger.info("All routers added")

logger.info("Starting Web Socket along with FastAPI application")

# Start the emitter during app startup
# @app.on_event("startup")
# async def startup_event():
#     loop = asyncio.get_running_loop()
#     set_event_loop(loop)
#     await start_emitter()

#app.mount("/", socketio.ASGIApp(sio))
app_socket = socketio.ASGIApp(
    tcp_sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)
logger.info("Starting Web Socket along with FastAPI application")


# # Start the emitter during app startup
# @app_socket.on_event("startup")
# async def start_emitter():
#     asyncio.create_task(emit_plates_data_periodically())  # Start emitting plates_data periodically


def main():
    """
    Main entry point for running the FastAPI app.
    """
    uvicorn.run("main:app_socket", host="0.0.0.0", port=8000, log_level="debug")
    # uvicorn.run("main:app_socket", host="0.0.0.0", port=8000, ssl_keyfile="./cert/client.key", ssl_certfile="./cert/client.crt", ssl_ca_certs="./cert/ca.crt")


if __name__ == "__main__":
    main()
