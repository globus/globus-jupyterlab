from typing import List
from enum import Enum
from pydantic import BaseModel


class TransferItemsModel(BaseModel):
    source_path: str
    destination_path: str
    recursive: bool


class TransferModel(BaseModel):
    source_endpoint: str
    destination_endpoint: str
    DATA: List[TransferItemsModel]


class StatusEnum(str, Enum):
    success = "success"
    failure = "failure"


class AuthResponseModel(BaseModel):
    result: StatusEnum = StatusEnum.success
    status_code: int = 200
    code: str = "Success"
    message: str = "The action completed successfully"
