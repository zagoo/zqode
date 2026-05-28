from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BizModel(BaseModel):
    """Project-wide Pydantic base.

    `protected_namespaces=()` opts every schema out of the Pydantic v2 'model_'
    prefix warning — we use ModelOut, model_name, model_id throughout because
    the FDD's domain vocabulary refers to LLM Models, not Pydantic models.
    """

    model_config = ConfigDict(protected_namespaces=())


class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "OK"
    data: Optional[T] = None


def ok(data: Optional[T] = None, message: str = "OK") -> ApiResponse[T]:
    return ApiResponse(code=0, message=message, data=data)


def err(code: int, message: str, data: Optional[T] = None) -> ApiResponse[T]:
    return ApiResponse(code=code, message=message, data=data)
