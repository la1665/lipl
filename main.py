import uvicorn
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from lifespan import lifespan
from auth.router import auth_router
from user.router import user_router
from lpr.router import building_router, gate_router, camera_settings_router, camera_router, lpr_setting_router, lpr_router
from tcp.router import tcp_router
from tcp.socket_management import sio as tcp_sio
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)
logger.info("Starting FastAPI application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

#app.mount("/", socketio.ASGIApp(sio))
app_socket = socketio.ASGIApp(
    tcp_sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)
logger.info("Starting Web Socket along with FastAPI application")


def main():
    """
    Main entry point for running the FastAPI app.
    """
    uvicorn.run("main:app_socket", host="0.0.0.0", port=8000, ssl_keyfile="./cert/client.key", ssl_certfile="./cert/client.crt", ssl_ca_certs="./cert/ca.crt")


if __name__ == "__main__":
    main()
