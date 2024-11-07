from pydantic import BaseModel


class CommandRequest(BaseModel):
    client_id: int
    # name: str
    commandType: str
    cameraId: str
    duration: int
