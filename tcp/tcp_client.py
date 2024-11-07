import json
import uuid
import base64
import asyncio
import socketio
from datetime import datetime
from twisted.internet import protocol, reactor, threads
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.engine import async_session


sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

## Event handler for Socket.IO
@sio.event
async def connect(sid, environ):
    print(f"Socket.IO Client connected: {sid}")
    await sio.emit('message', {'message': 'Hello from the Socket.IO server'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Socket.IO Client disconnected: {sid}")

@sio.event
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    await sio.emit('response', {'message': f"Received: {data}"}, to=sid)



class SimpleTCPClient(protocol.Protocol):
    def __init__(self, loop):
        self.auth_message_id = None
        self.loop = loop

    def connectionMade(self):
        """
        Called when a connection to the server is made.
        Authenticates the client by sending a token.
        """
        print(f"[INFO] Connected to {self.transport.getPeer()}")
        self.authenticate()
        self.incomplete_data = ""

    def authenticate(self):
        """
        Sends an authentication message to the server.
        """
        self.auth_message_id = str(uuid.uuid4())
        auth_message = self._create_auth_message(self.auth_message_id, self.factory.auth_token)
        self._send_message(auth_message)
        self.factory.authenticated = False
        print(f"[INFO] Authentication message sent with ID: {self.auth_message_id}")

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
        print(f"[INFO] Sending message: {message}")
        self.transport.write((message + '\n').encode('utf-8'))

    def dataReceived(self, data):

        self.incomplete_data += data.decode('utf-8')

        # Split messages by the newline character
        while '\n' in self.incomplete_data:
            full_message, self.incomplete_data = self.incomplete_data.split('\n', 1)
            if full_message:
                reactor.callFromThread(self._process_message,full_message)
                #self._handle_message(full_message)



    def _process_message(self, message):
        """
        Processes the received message from the server.
        This runs in a separate thread.
        """
        try:
            message = message.rstrip()
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
            self.factory.authenticated = True
            self.factory.protocol_instance = self
        else:
            print(f"[INFO] Acknowledgment for message: {reply_to}")

    def _handle_command_response(self, message):
        """
        Handles the command response from the server.
        """
        pass

    async def _broadcast_to_socketio(self, message):
        """
        Broadcasts a message to all Socket.IO clients.
        """
        await sio.emit('message', json.dumps(message))

    def _handle_plates_data(self, message):
        """
        Handles 'plates_data' message from the server.
        Processes the plate information (plate image, plate number, timestamp) and sends it to WebSocket clients.
        """
        message_body = message["messageBody"]

        # Extract data from the message body
        timestamp = message_body.get("timestamp")
        gate = message_body.get("gate")
        full_image = message_body.get("full_image")
        cars = message_body.get("cars", [])

        for car in cars:
            # Extract plate information
            plate = car.get("plate", {})
            plate_number = plate.get("plate", "Unknown")
            plate_image_base64 = plate.get("plate_image", "")

            # Additional information about the vehicle
            vehicle_class = car.get("vehicle_class", {})
            vehicle_type = car.get("vehicle_type", {})
            ocr_accuracy = car.get("ocr_accuracy", "Unknown")
            vision_speed = car.get("vision_speed", 0.0)

            # Construct the message to send via Socket.IO
            socketio_message = {
                "messageType": "plates_data",
                "timestamp": timestamp,
                "gate": gate,
                "plate_number": plate_number,
                "plate_image": plate_image_base64,  # Still base64 encoded
                "ocr_accuracy": ocr_accuracy,
                "vision_speed": vision_speed,
                "vehicle_class": vehicle_class,
                "vehicle_type": vehicle_type,
                "full_image": full_image
            }

            asyncio.run_coroutine_threadsafe(self._broadcast_to_socketio(socketio_message), self.loop)


    def _handle_live_data(self, message):
        """
        Handles 'live' message from the server.
        Decodes the base64 image and sends it to WebSocket clients.
        """
        message_body = message["messageBody"]
        live_image_base64 = message_body.get("live_image")
        gate = message_body.get("gate")

        if live_image_base64:
            # Send the image (in base64 format) to Socket.IO clients
            socketio_message = {
                "messageType": "live",
                "live_image": live_image_base64,
                "gate": gate
            }

            asyncio.run_coroutine_threadsafe(self._broadcast_to_socketio(socketio_message), self.loop)


    def _handle_unknown_message(self, message):
        """
        Handles unknown message types from the server.
        """
        pass

    def send_command(self, command_data):
        """
        Sends a command to the server if authenticated.
        """
        if self.factory.authenticated:
            command_message = self._create_command_message(command_data)
            self._send_message(command_message)
        else:
            print("[ERROR] Cannot send command: client is not authenticated.")

    def _create_command_message(self, command_data):
        """
        Creates a command message.
        """
        return json.dumps({
            "messageId": str(uuid.uuid4()),
            "messageType": "command",
            "messageBody": command_data
        })

    def connectionLost(self, reason):
        """
        Handles connection lost events.
        """
        print(f"[INFO] Connection lost: {reason}")
        self.factory.clientConnectionLost(self.transport.connector, reason)


class ReconnectingTCPClientFactory(protocol.ReconnectingClientFactory):
    def __init__(self, auth_token, loop):
        self.auth_token = auth_token
        self.authenticated = False
        self.protocol_instance = None
        self.loop = loop
        self.initialDelay = 2
        self.maxDelay = 2
        self.factor = 1
        self.jitter = 0

    def buildProtocol(self, addr):
        """
        Builds the protocol instance and resets reconnection delay.
        """
        self.resetDelay()
        client = SimpleTCPClient(self.loop)
        client.factory = self
        return client

    def clientConnectionLost(self, connector, reason):
        """
        Handles lost connection events and retries only when fully disconnected.
        """
        print(f"[INFO] Connection lost: {reason}. Reconnecting in 2 seconds...")
        self._attempt_reconnect(connector)

    def clientConnectionFailed(self, connector, reason):
        """
        Handles failed connection attempts and retries only when fully disconnected.
        """
        print(f"[ERROR] Connection failed: {reason}. Retrying in 2 seconds...")
        self._attempt_reconnect(connector)

    def _attempt_reconnect(self, connector):
        """
        Attempts reconnection only if the connector is in the correct state.
        """
        if connector.state == 'disconnected':
            print(f"[INFO] Reconnecting...")
            reactor.callLater(self.initialDelay, self.retry, connector)
        else:
            print(f"[ERROR] Cannot reconnect in current state: {connector.state}. Retrying later...")
            reactor.callLater(5, self._attempt_reconnect, connector)


def connect_to_server(server_ip, port, auth_token, loop):
    """
    Connects to the TCP server.
    """
    factory = ReconnectingTCPClientFactory(auth_token, loop)
    reactor.connectTCP(server_ip, port, factory)
    return factory


def send_command_to_server(factory, command_data):
    """
    Sends a command to the TCP server if authenticated.
    """
    if factory.authenticated and factory.protocol_instance:
        print(f"[INFO] Sending command to server: {command_data}")
        factory.protocol_instance.send_command(command_data)
    else:
        print("[ERROR] Cannot send command: Client is not authenticated or connected.")
