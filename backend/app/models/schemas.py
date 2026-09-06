from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    category: Optional[str]
    price: Optional[float]
    platform: Optional[str]
    sales_volume: int
    rating: Optional[float]
    description: Optional[str]
    source_doc: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class FiltersInfo(BaseModel):
    categories: list[str]
    price_min: float
    price_max: float
    platforms: list[str]


class RecommendedProduct(ProductOut):
    potential_score: float  # 潜力分 = 销量 × 评分 / 1000


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    status: str
    chunk_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    product: ProductOut
    score: float
    matched_chunk: str


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    deep_thinking: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
    conversation_id: str


# ---------- 认证 ----------
class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- 管理员 ----------
class AdminOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: int
    created_at: Optional[datetime]
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut
