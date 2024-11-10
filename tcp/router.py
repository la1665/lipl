import threading
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from db.engine import get_db
from lpr.model import DBLpr, DBClient
from tcp.schema import CommandRequest
from tcp.tcp_client import send_command_to_server
from tcp.manager import connection_manager


# servers = [
#     {"server_id": "server1", "ip": "185.81.99.23", "port": 45, "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ"},
#     {"server_id": "server2", "ip": "185.81.99.23", "port": 46, "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ"},
#     {"server_id": "server3", "ip": "185.81.99.23", "port": 47, "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ"},
#     {"server_id": "server4", "ip": "185.81.99.23", "port": 48, "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ"},
#     {"server_id": "server5", "ip": "185.81.99.23", "port": 49, "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ"},
# ]

tcp_factories = {}
tcp_factory_lock = threading.Lock()

tcp_router = APIRouter()


@tcp_router.post("/send-command")
async def send_command(request: CommandRequest, db:AsyncSession=Depends(get_db)):
    # global tcp_factories

    print(f"Received request from client: {request.client_id}")
    factory = await connection_manager.get_connection(request.client_id)
    if not factory:
            raise HTTPException(status_code=404, detail="TCP client for the requested camera not found")

    if not factory.authenticated:
        raise HTTPException(status_code=400, detail=f"TCP client: {request.client_id} is not authenticated or connected")


    # lpr = await db.execute(select(LPR).where(LPR.id == request.lpr_id))
    # lpr = lpr.unique().scalars().first()
    # if not lpr:
    #         raise HTTPException(status_code=404, detail="LPR server not found")

    # with tcp_factory_lock:
    #     if lpr.id not in tcp_factories:
    #         raise HTTPException(status_code=404, detail="TCP client for the requested LPR server not found")


        # factory = tcp_factories[lpr.id]

        # if not factory.authenticated:
        #     raise HTTPException(status_code=400, detail=f"TCP client for server {lpr.id} is not authenticated or connected")

    command_data = {
        "commandType": request.commandType,
        "cameraId": request.cameraId,
        "duration": request.duration
    }

    print(f"Sending command to server {request.client_id}: {command_data}")

    send_command_to_server(factory, command_data)

    return {"status": "Command sent", "command": command_data, "server_id": request.client_id}
