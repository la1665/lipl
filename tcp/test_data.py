import asyncio
from tcp.socket_management import emit_to_requested_sids

# Define test data for plates_data
test_data_plates = {
    "camera_id": "2",
    "plate_number": "ABC123",
    "timestamp": "2024-11-25T12:00:00Z",
    "vehicle_class": "Sedan",
    "vehicle_color": "Blue",
    "vehicle_type": "Car",
    "ocr_accuracy": 0.98,
    "plate_image": "base64_encoded_image_data"
}

async def emit_plates_data_periodically():
    """
    Emit plates_data every second to subscribed clients.
    """
    while True:
        print("[TEST] Emitting plates_data...")
        await emit_to_requested_sids("plates_data", test_data_plates, camera_id="2")
        await asyncio.sleep(1)  # Wait for 1 second before emitting again

