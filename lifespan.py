import logging
import asyncio
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from twisted.internet import reactor
from sqlalchemy.future import select

from db.engine import engine, Base, async_session
from utils.db_utils import create_default_admin, initialize_defaults
from lpr.model import DBLpr
from tcp.tcp_client import connect_to_server, send_command_to_server
from tcp.router import tcp_factories, tcp_factory_lock
from tcp.manager import connection_manager

logger = logging.getLogger(__name__)

# async def initialize_tcp_clients():
#     """
#     Initialize a TCP client for each server and store the factory.
#     """
#     async with async_session() as session:
#         print("fetching all clients: ... ")
#         result = await session.execute(select(DBLpr))
#         clients = result.unique().scalars().all()
#         print(f"Found clients: {len(clients)} ")

#     for client in clients:
#         factory = connect_to_server(server_ip=client.ip, port=client.port, auth_token=client.auth_token)
#         await connection_manager.add_connection(client.id, factory)
#     if not reactor.running:
#         reactor_thread = threading.Thread(target=reactor.run, args=(False,), daemon=True)
#         reactor_thread.start()

async def initialize_lpr_connections():
    """
    Initialize TCP clients for all LPRs and store their factory in the connection manager.
    """
    logger.info("Initializing LPR connections...")
    print("Initializing LPR connections...")
    try:
        async with async_session() as session:
            try:
                result = await session.execute(select(DBLpr))
                lprs = result.scalars().unique().all()
                logger.info(f"Found {len(lprs)} LPRs for initialization.")
                print(f"Found {len(lprs)} LPRs for initialization.")

                for lpr in lprs:
                    factory = connect_to_server(
                        server_ip=lpr.ip,
                        port=lpr.port,
                        auth_token=lpr.auth_token
                    )
                    await connection_manager.add_connection(lpr.id, factory)
                    logger.info(f"Initialized connection for LPR with ID: {lpr.id}, IP: {lpr.ip}, Port: {lpr.port}")
                    print(f"Initialized connection for LPR with ID: {lpr.id}, IP: {lpr.ip}, Port: {lpr.port}")
            except Exception as error:
                await session.rollback()
                print(f"Error: {error}")
    except Exception as error:
        logger.error(f"Failed to initialize LPR connections: {error}")
        print(f"Failed to initialize LPR connections: {error}")

def start_reactor():
    """
    Start the Twisted reactor in a separate thread.
    """
    try:
        logger.info("Starting Twisted reactor...")
        print("Starting Twisted reactor...")
        reactor.run(installSignalHandlers=False)
    except Exception as error:
        logger.error(f"Error starting Twisted reactor: {error}")
        print(f"Error starting Twisted reactor: {error}")

def stop_reactor():
    if reactor.running:
        print("[INFO] Stopping the Twisted reactor...")
        reactor.stop()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application lifespan starting - setting up database")
    print("[INFO] Starting lifespan")
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
        print("[INFO] Database tables dropped")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        print("[INFO] Database tables created")

    # Create default admin user and defaults
    async with async_session() as session:
        try:
            await create_default_admin(session)
            logger.info("Default admin user ensured")
            print("[INFO] Default admin user created")
            await initialize_defaults(session)
        except Exception as error:
            logger.critical(f"Failed to create initials: {error}")
            print(f"error: {error}")


    # Start the Twisted reactor in a separate thread
    await initialize_lpr_connections()
    # reactor_thread = threading.Thread(target=start_reactor, daemon=True)
    # reactor_thread.start()
    # await asyncio.sleep(5)
    logger.info("TCP clients initialized and authenticated")
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
    # time.sleep(5)
    # await asyncio.sleep(5)
    # logger.info("TCP clients initialized")
    # print("[INFO] TCP clients initialized")
    yield
    logger.info("Application lifespan ending - cleaning up resources")
    # Clean up resources
    await engine.dispose()
    logger.info("Database connection closed")
    # Close all TCP clients
    reactor.callFromThread(reactor.stop)

    print("[INFO] Lifespan ended")
