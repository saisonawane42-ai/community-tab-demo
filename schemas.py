from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- Categories ----------

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Comments ----------

class CommentCreate(BaseModel):
    author_id: int
    author_name: str
    content: str = Field(..., min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime
    like_count: int = 0


# ---------- Posts ----------

class PostCreate(BaseModel):
    author_id: int
    author_name: str
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    author_id: int
    author_name: str
    title: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    like_count: int = 0
    comment_count: int = 0


class PostDetailOut(PostOut):
    comments: List[CommentOut] = []


# ---------- Likes ----------

class LikeCreate(BaseModel):
    user_id: int


class LikeOut(BaseModel):
    liked: bool
    like_count: int
