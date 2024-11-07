import asyncio
from typing import Dict, Optional
from twisted.internet import protocol


class TCPConnectionManager:
    def __init__(self):
        # Using an asyncio lock to manage concurrent access to the connections
        self.connections: Dict[int, protocol.ReconnectingClientFactory] = {}
        self.lock = asyncio.Lock()

    async def add_connection(self, client_id: int, factory: protocol.ReconnectingClientFactory):
        async with self.lock:
            self.connections[client_id] = factory
            print(f"[INFO] Added connection for LPR {client_id}")

    async def remove_connection(self, client_id: int):
        async with self.lock:
            if client_id in self.connections:
                del self.connections[client_id]
                print(f"[INFO] Removed connection for LPR {client_id}")

    async def get_connection(self, client_id: int) -> Optional[protocol.ReconnectingClientFactory]:
        async with self.lock:
            return self.connections.get(client_id)

    async def get_all_connections(self) -> Dict[int, protocol.ReconnectingClientFactory]:
        async with self.lock:
            return self.connections


connection_manager = TCPConnectionManager()
