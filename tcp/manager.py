import asyncio
from typing import Dict, Optional
from twisted.internet import protocol
from threading import Lock

class TCPConnectionManager:
    def __init__(self):
        # Using an asyncio lock to manage concurrent access to the connections
        self.connections: Dict[int, protocol.ReconnectingClientFactory] = {}
        self.lock = Lock()

    async def add_connection(self, client_id: int, factory: protocol.ReconnectingClientFactory):
        with self.lock:
            if client_id not in self.connections:
                self.connections[client_id] = factory
                print(f"[INFO] Added connection for LPR {client_id}")
        print(f"-------all available connections are: {len(self.connections)}--------")
    async def remove_connection(self, client_id: int):
        with self.lock:
            if client_id in self.connections:
                del self.connections[client_id]
                print(f"[INFO] Removed connection for LPR {client_id}")

    async def get_connection(self, client_id: int) -> Optional[protocol.ReconnectingClientFactory]:
        with self.lock:
            print(f"-------all available connections are: {self.connections}--------")
            return self.connections.get(client_id)

    async def get_all_connections(self) -> Dict[int, protocol.ReconnectingClientFactory]:
        with self.lock:
            return self.connections


connection_manager = TCPConnectionManager()
