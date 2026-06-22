from pydantic import BaseModel
from datetime import datetime

class KbCategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    
    class Config:
        from_attributes = True

class KbArticleCreate(BaseModel):
    title: str
    slug: str
    category_id: int | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str = "published"

class KbArticleUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    category_id: int | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None

class KbArticleResponse(KbArticleCreate):
    id: int
    author_id: int | None
    view_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
