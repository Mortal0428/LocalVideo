from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

DataType = TypeVar("DataType")

class ApiResponse(BaseModel, Generic[DataType]):
    code: int = 200
    message: str = "success"
    data: Optional[DataType] = None
