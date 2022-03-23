from typing import List
from pydantic import BaseModel

class TransferItemsModel(BaseModel):
    source_path: str
    destination_path: str
    recursive: bool


class TransferModel(BaseModel):
    source_endpoint: str
    destination_endpoint: str
    transfer_items: List[TransferItemsModel]
