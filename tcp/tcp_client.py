import os
import json
import uuid
import hmac
import hashlib
import asyncio
import socketio
# from twisted.internet import asyncioreactor
# asyncioreactor.install(asyncio.get_event_loop())
from sqlalchemy.exc import SQLAlchemyError
from twisted.internet import protocol, reactor, ssl
from sqlalchemy.future import select

from db.engine import async_session
from tcp.socket_management import emit_to_requested_sids
from settings import settings
from traffic.model import Vehicle, Traffic
# Load environment variables from .env file

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client_key_path = os.getenv("CLIENT_KEY_PATH","/app/cert/client.key")
client_cert_path = os.getenv("CLIENT_CERT_PATH","/app/cert/client.crt")
ca_cert_path = os.getenv("CA_CERT_PATH","/app/cert/ca.crt")

class SimpleTCPClient(protocol.Protocol):
    def __init__(self):
        self.auth_message_id = None
        self.incomplete_data = ""
        self.authenticated = False  # Track authentication status locally


    def connectionMade(self):
        """
        Called when a connection to the server is made.
        Authenticates the client by sending a token.
        """
        print(f"[INFO] Connected to {self.transport.getPeer()}")
        self.authenticate()


    def authenticate(self):
        """
        Sends an authentication message to the server.
        """
        try:
            self.auth_message_id = str(uuid.uuid4())
            auth_message = self._create_auth_message(self.auth_message_id, self.factory.auth_token)
            self._send_message(auth_message)
            print(f"[INFO] Authentication message sent with ID: {self.auth_message_id}")
        except:
            print("Not Accesptable")

    def _create_auth_message(self, message_id, token):
        """
        Creates an authentication message.
        """
        return json.dumps({
            "messageId": message_id,
            "messageType": "authentication",
            "messageBody": {"token": token}
        })

    def _send_message(self, message):
        """
        Sends a message to the server.
        """
        if self.transport and self.transport.connected:
            print(f"[INFO] Sending message: {message}")
            self.transport.write((message + '\n').encode('utf-8'))
        else:
            print("[ERROR] Transport is not connected. Message not sent.")


    def dataReceived(self, data):
        """Accumulates and processes data received from the server."""
        print("data is receiving ...")
        self.incomplete_data += data.decode('utf-8')
        while '<END>' in self.incomplete_data:
            full_message, self.incomplete_data = self.incomplete_data.split('<END>', 1)
            if full_message:
                print(f"[DEBUG] Received message: {full_message}...")
                asyncio.create_task(self._process_message(full_message))
                # reactor.callInThread(self._process_message, full_message)

    async def _process_message(self, message):
        """
        Processes the received message from the server.
        This runs in a separate thread.
        """
        try:
            # message = message.rstrip()
            parsed_message = json.loads(message)
            message_type = parsed_message.get("messageType")

            handlers = {
                "acknowledge": self._handle_acknowledgment,
                "command_response": self._handle_command_response,
                "plates_data": self._handle_plates_data,
                "live": self._handle_live_data
            }

            handler = handlers.get(message_type, self._handle_unknown_message)
            handler(parsed_message)

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse message: {e}")

    def _handle_acknowledgment(self, message):
        """
        Handles acknowledgment from the server.
        """
        reply_to = message["messageBody"].get("replyTo")
        if reply_to == self.auth_message_id:
            print("[INFO] Authentication successful.")
            self.authenticated = True
            self.factory.authenticated = True
            # self.factory.protocol_instance = self
        else:
            print(f"[INFO] Acknowledgment for message: {reply_to} ...")

    async def _broadcast_to_socketio(self, event_name, data):
        """Efficiently broadcast a message to all subscribed clients for an event."""
        await emit_to_requested_sids(event_name, data)

    # def _handle_plates_data(self, message):
    #     message_body = message["messageBody"]
    #     socketio_message = {
    #         "messageType": "plates_data",
    #         "timestamp": message_body.get("timestamp"),
    #         "camera_id": message_body.get("camera_id"),
    #         "full_image": message_body.get("full_image"),
    #         "cars": [
    #             {
    #                 "plate_number": car.get("plate", {}).get("plate", "Unknown"),
    #                 "plate_image": car.get("plate", {}).get("plate_image", ""),
    #                 "ocr_accuracy": car.get("ocr_accuracy", "Unknown"),
    #                 "vision_speed": car.get("vision_speed", 0.0),
    #                 "vehicle_class": car.get("vehicle_class", {}),
    #                 "vehicle_type": car.get("vehicle_type", {}),
    #                 "vehicle_color": car.get("vehicle_color", {})
    #             }
    #             for car in message_body.get("cars", [])
    #         ]
    #     }
    #     reactor.callFromThread(
    #         asyncio.run, self._broadcast_to_socketio("plates_data", socketio_message)
    #     )

    async def _store_plate_data(self, plate_data):
        """
        Stores the plate data in the database.
        """
        async with async_session() as session:
            try:
                for car in plate_data.get("cars", []):
                    plate_number = car.get("plate", {}).get("plate", "Unknown")
                    vehicle = await self._get_or_create_vehicle(session, plate_number, car)
                    traffic_entry = Traffic(
                        vehicle_id=vehicle.id,
                        camera_id=plate_data.get("camera_id"),
                        timestamp=plate_data.get("timestamp"),
                        ocr_accuracy=car.get("ocr_accuracy", 0.0),
                        vision_speed=car.get("vision_speed", 0.0)
                    )
                    session.add(traffic_entry)
                await session.commit()
                print("[INFO] Successfully stored plate data.")
            except Exception as error:
                print(f"[ERROR] couldn't save Vehicle/Traffic: {error}")
                await session.rollback()


    async def _get_or_create_vehicle(self, session, plate_number, car_data):
        """
        Retrieves or creates a vehicle entry in the database.
        """
        result = await session.execute(
            select(Vehicle).where(Vehicle.plate_number == plate_number)
        )
        vehicle = result.scalars().first()
        if not vehicle:
            vehicle_class_dict = car_data.get("vehicle_class", {})
            vehicle_type_dict = car_data.get("vehicle_type", {})
            vehicle_color_dict = car_data.get("vehicle_color", {})

            # Function to safely convert to string or None
            def safe_convert(value):
                if value in [None, "null", "None"]:
                    return None
                return str(value)

            vehicle_class_value = safe_convert(vehicle_class_dict.get('class'))
            vehicle_type_value = safe_convert(vehicle_type_dict.get('class'))
            vehicle_color_value = safe_convert(vehicle_color_dict.get('class'))

            vehicle = Vehicle(
                plate_number=plate_number,
                vehicle_class=vehicle_class_value,
                vehicle_type=vehicle_type_value,
                vehicle_color=vehicle_color_value,
            )
            session.add(vehicle)
            # await session.flush()
            try:
                await session.flush()
                print(f"[INFO] Created new vehicle with plate number: {plate_number}")
            except Exception as e:
                print(f"[ERROR] Failed to create vehicle '{plate_number}': {e}")
                await session.rollback()
                raise e
        else:
            print(f"[INFO] Found existing vehicle with plate number: {plate_number}")
        return vehicle


    def _handle_plates_data(self, message):
        """
        Handles plate data from the server and broadcasts it via Socket.IO.
        """
        message_body = message["messageBody"]
        socketio_message = {
            "messageType": "plates_data",
            "timestamp": message_body.get("timestamp"),
            "camera_id": message_body.get("camera_id"),
            "full_image": message_body.get("full_image"),
            "cars": [
                {
                    "plate_number": car.get("plate", {}).get("plate", "Unknown"),
                    "plate_image": car.get("plate", {}).get("plate_image", ""),
                    "ocr_accuracy": car.get("ocr_accuracy", "Unknown"),
                    "vision_speed": car.get("vision_speed", 0.0),
                    "vehicle_class": car.get("vehicle_class", {}),
                    "vehicle_type": car.get("vehicle_type", {}),
                    "vehicle_color": car.get("vehicle_color", {})
                }
                for car in message_body.get("cars", [])
            ]
        }
        asyncio.create_task(self._store_plate_data(message_body))
        asyncio.create_task(self._broadcast_to_socketio("plates_data", socketio_message))
        # reactor.callFromThread(
        #     asyncio.run, self._broadcast_to_socketio("plates_data", socketio_message)
        # )

    def _handle_command_response(self, message):
        """
        Handles the command response from the server.
        """
        pass  # Implement as needed

    def _handle_live_data(self, message):
        message_body = message["messageBody"]
        live_data = {
            "messageType": "live",
            "live_image": message_body.get("live_image"),
            "camera_id": message_body.get("camera_id")
        }
        asyncio.create_task(self._broadcast_to_socketio("live", live_data))
        # asyncio.ensure_future(self._broadcast_to_socketio("live", live_data))

    def _handle_unknown_message(self, message):
        print(f"[WARN] Received unknown message type: {message.get('messageType')}")

    def send_command(self, command_data):
        if self.authenticated:
            command_message = self._create_command_message(command_data)
            self._send_message(command_message)
        else:
            print("[ERROR] Cannot send command: client is not authenticated.")

    def _create_command_message(self, command_data):
        """Creates and signs a command message with HMAC for integrity."""
        # hmac_key = os.getenv("HMAC_SECRET_KEY", "").encode()
        hmac_key = settings.HMAC_SECRET_KEY.encode()
        data_str = json.dumps(command_data)
        hmac_signature = hmac.new(hmac_key, data_str.encode(), hashlib.sha256).hexdigest()
        return json.dumps({
            "messageId": str(uuid.uuid4()),
            "messageType": "command",
            "messageBody": {
                "data": command_data,
                "hmac": hmac_signature
            }
        })

    def connectionLost(self, reason):
        print(f"[INFO] Connection lost: {reason}")
        if self.factory:
            self.factory.clientConnectionLost(self.transport.connector, reason)
        else:
            print("[ERROR] Connection lost without factory reference.")

class ReconnectingTCPClientFactory(protocol.ReconnectingClientFactory):
    def __init__(self, server_ip, port, auth_token):
        self.auth_token = auth_token
        self.authenticated = False
        self.protocol_instance = None
        self.initialDelay = 2
        self.maxDelay = 10  # Increased max delay for exponential backoff
        self.factor = 1.5  # Exponential backoff factor
        self.jitter = 0.1
        self.server_ip = server_ip
        self.port = port
        self.reconnecting = False  # Add reconnecting flag

    def buildProtocol(self, addr):
        self.resetDelay()
        self.reconnecting = False  # Reset the reconnecting flag on successful connection
        client = SimpleTCPClient()
        client.factory = self
        self.protocol_instance = client
        return client

    def clientConnectionLost(self, connector, reason):
        if not self.reconnecting:
            print(f"[INFO] Connection lost: {reason}. Reconnecting with SSL context...")
            self.reconnecting = True
            self._attempt_reconnect()

    def clientConnectionFailed(self, connector, reason):
        if not self.reconnecting:
            print(f"[ERROR] Connection failed: {reason}. Retrying with SSL context...")
            self.reconnecting = True
            self._attempt_reconnect()

    def _attempt_reconnect(self):
        """Reconnect with a new SSL context setup."""
        # Create a fresh ClientContextFactory for each reconnect attempt
        class ClientContextFactory(ssl.ClientContextFactory):
            print("Using ssl ...")
            def getContext(self):
                print("Using ssl context ...")
                context = ssl.SSL.Context(ssl.SSL.TLSv1_2_METHOD)
                context.use_certificate_file(settings.CLIENT_CERT_PATH)
                context.use_privatekey_file(settings.CLIENT_KEY_PATH)
                context.load_verify_locations(settings.CA_CERT_PATH)
                # context.use_certificate_file(settings.CLIENT_CERT_PATH)
                # context.use_privatekey_file(settings.CLIENT_KEY_PATH)
                # context.load_verify_locations(settings.CA_CERT_PATH)
                context.set_verify(ssl.SSL.VERIFY_PEER, lambda conn, cert, errno, depth, ok: ok)
                # context.set_verify(ssl.SSL.VERIFY_NONE, lambda conn, cert, errno, depth, ok: ok)
                print("Using ssl context completed ...")
                return context

        # Schedule the reconnect with a fresh SSL context
        reactor.callLater(self.initialDelay, reactor.connectSSL, self.server_ip, self.port, self, ClientContextFactory())

def connect_to_server(server_ip, port, auth_token):
    factory = ReconnectingTCPClientFactory(server_ip, port, auth_token)
    print(f"factory created ... {factory}")
    # reactor.connectTCP(server_ip, port, factory)
    print(f"Connecting to the factory: {factory}...")
    factory._attempt_reconnect()  # Start initial connection attempt
    return factory

def send_command_to_server(factory, command_data):
    if factory.authenticated and factory.protocol_instance:
        print(f"[INFO] Sending command to server: {command_data}")
        factory.protocol_instance.send_command(command_data)
    else:
        print("[ERROR] Cannot send command: Client is not authenticated or connected.")









#  [DEBUG] Received message: {"messageBody":{"camera_id":"1","cars":[{"box":{"bottom":135,"left":93,"right":165,"top":93},"direction":0,"meta_data":"null","ocr_accuracy":0.09002960473299026,"plate":{"city_code":0,"first":"14","letter":"j","plate":"14j67540","plate_type":"IR","second":"67540"},"radar_speed":0.0,"vehicle_class":{"class":1,"conf":0.9},"vehicle_color":{"class":"null","conf":0},"vehicle_type":{"class":0,"conf":0},"vision_speed":0.0}],"timestamp":"2024-11-22T14:32:47.644Z"},"messageId":"554a08c4-c136-41b9-88cc-65185a4deb88","messageType":"plates_data"}
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,718 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,718 INFO sqlalchemy.engine.Engine SELECT vehicles.id, vehicles.plate_number, vehicles.vehicle_class, vehicles.vehicle_type, vehicles.vehicle_color, vehicles.is_active, vehicles.created_at, vehicles.updated_at, vehicles.owner_id
# [2024-11-22 18:02:47] FROM vehicles
# [2024-11-22 18:02:47] WHERE vehicles.plate_number = $1::VARCHAR
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,719 INFO sqlalchemy.engine.Engine [cached since 141.5s ago] ('Unknown',)
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,721 INFO sqlalchemy.engine.Engine INSERT INTO vehicles (plate_number, vehicle_class, vehicle_type, vehicle_color, is_active, created_at, updated_at, owner_id) VALUES ($1::VARCHAR, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::BOOLEAN, now(), now(), $6::INTEGER) RETURNING vehicles.id, vehicles.created_at, vehicles.updated_at
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,721 INFO sqlalchemy.engine.Engine [cached since 141.5s ago] ('Unknown', 1, 0, None, True, None)
# [2024-11-22 18:02:47] 2024-11-22 18:02:47,722 INFO sqlalchemy.engine.Engine ROLLBACK
