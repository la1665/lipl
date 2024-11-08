import logging
import asyncio
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from twisted.internet import reactor
from sqlalchemy.future import select

from db.engine import engine, Base, async_session
from utils.db_utils import create_default_admin
from lpr.model import DBLpr, DBClient
# from tcp_connection.TCPClient import connect_to_server, send_command_to_server
# from tcp_connection.router import tcp_factories, tcp_factory_lock
# from tcp_connection.manager import connection_manager

logger = logging.getLogger(__name__)

# async def initialize_tcp_clients():
#     """
#     Initialize a TCP client for each server and store the factory.
#     """
#     async with async_session() as session:
#         print("fetching all clients: ... ")
#         result = await session.execute(select(Client))
#         clients = result.unique().scalars().all()
#         print(f"Found clients: {len(clients)} ")

#     for client in clients:
#         factory = connect_to_server(server_ip=client.ip, port=client.port, auth_token=client.auth_token)
#         await connection_manager.add_connection(client.id, factory)
#     if not reactor.running:
#         reactor_thread = threading.Thread(target=reactor.run, args=(False,), daemon=True)
#         reactor_thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application lifespan starting - setting up database")
    print("[INFO] Starting lifespan")
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    print("[INFO] Database tables created")

    # Create default admin user
    async with async_session() as session:
        try:
            await create_default_admin(session)
            logger.info("Default admin user ensured")
            print("[INFO] Default admin user created")
        except Exception as error:
            logger.critical(f"Failed to create default admin user: {error}")
            print(f"admin error: {error}")


    # Start the Twisted reactor in a separate thread
    # def start_reactor():
    #     reactor.run(installSignalHandlers=False)

    # Initialize TCP clients for all LPRs
    # async def initialize_tcp_clients():
    #     """
    #     Initialize a TCP client for each server and store the factory.
    #     """
    #     # global tcp_factories
    #     # Get the current asyncio loop
    #     loop = asyncio.get_running_loop()
    #     # async def setup_lpr_clients():
    #     async with async_session() as session:
    #         result = await session.execute(select(Client))
    #         clients = result.scalars().all()

    #     for client in clients:
    #         # with tcp_factory_lock:
    #             factory = connect_to_server(client.ip, client.port, client.auth_token, loop)
    #             await connection_manager.add_connection(client.id, factory)
                # tcp_factories[lpr.id] = factory
        # asyncio.run(setup_lpr_clients())

    # Initialize connections to all servers

    # await initialize_tcp_clients()
    # reactor_thread = threading.Thread(target=start_reactor,  daemon=True)
    # reactor_thread.start()


    # Allow some time for TCP clients to authenticate before FastAPI starts serving
    # time.sleep(2)

    # print("[INFO] TCP clients initialized")
    yield
    # Clean up resources
    await engine.dispose()
    logger.info("Database connection closed")
    # Close all TCP clients
    # def stop_reactor():
    #     if reactor.running:
    #         print("[INFO] Stopping the Twisted reactor...")
    #         reactor.stop()

    # reactor.callFromThread(stop_reactor)

    print("[INFO] Lifespan ended")
