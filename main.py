from typing import List

from fastapi import Depends, FastAPI, HTTPException

import crud
import models
import schemas
from database import engine, get_db

# Creates tables if they don't exist yet. For anything beyond local dev,
# switch to Alembic migrations instead of relying on this.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Community API")

DEFAULT_CATEGORIES = [
    {"name": "General", "slug": "general", "description": "General discussion"},
    {"name": "Work Culture", "slug": "work-culture", "description": "Talk about workplace culture"},
    {"name": "Ongoing Updates", "slug": "ongoing-updates", "description": "Latest updates and announcements"},
]


@app.on_event("startup")
def seed_categories():
    db = next(get_db())
    try:
        for cat in DEFAULT_CATEGORIES:
            if not crud.get_category_by_slug(db, cat["slug"]):
                crud.create_category(db, schemas.CategoryCreate(**cat))
    finally:
        db.close()


# ---------- Categories ----------

@app.get("/categories", response_model=List[schemas.CategoryOut])
def list_categories(db=Depends(get_db)):
    return crud.get_categories(db)


@app.post("/categories", response_model=schemas.CategoryOut, status_code=201)
def add_category(category: schemas.CategoryCreate, db=Depends(get_db)):
    if crud.get_category_by_slug(db, category.slug):
        raise HTTPException(400, "Category slug already exists")
    return crud.create_category(db, category)


# ---------- Posts ----------

@app.get("/categories/{slug}/posts", response_model=List[schemas.PostOut])
def list_posts(slug: str, skip: int = 0, limit: int = 20, db=Depends(get_db)):
    posts = crud.get_posts(db, slug, skip, limit)
    if posts is None:
        raise HTTPException(404, "Category not found")
    return posts


@app.post("/categories/{slug}/posts", response_model=schemas.PostOut, status_code=201)
def add_post(slug: str, post: schemas.PostCreate, db=Depends(get_db)):
    db_post = crud.create_post(db, slug, post)
    if db_post is None:
        raise HTTPException(404, "Category not found")
    return crud._post_with_counts(db, db_post)


@app.get("/posts/{post_id}", response_model=schemas.PostDetailOut)
def get_post_detail(post_id: int, db=Depends(get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    data = crud._post_with_counts(db, post)
    data["comments"] = crud.get_comments(db, post_id)
    return data


@app.patch("/posts/{post_id}", response_model=schemas.PostOut)
def edit_post(post_id: int, updates: schemas.PostUpdate, db=Depends(get_db)):
    post = crud.update_post(db, post_id, updates)
    if not post:
        raise HTTPException(404, "Post not found")
    return crud._post_with_counts(db, post)


@app.delete("/posts/{post_id}", status_code=204)
def remove_post(post_id: int, db=Depends(get_db)):
    if not crud.delete_post(db, post_id):
        raise HTTPException(404, "Post not found")


# ---------- Comments ----------

@app.get("/posts/{post_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(post_id: int, db=Depends(get_db)):
    if not crud.get_post(db, post_id):
        raise HTTPException(404, "Post not found")
    return crud.get_comments(db, post_id)


@app.post("/posts/{post_id}/comments", response_model=schemas.CommentOut, status_code=201)
def add_comment(post_id: int, comment: schemas.CommentCreate, db=Depends(get_db)):
    db_comment = crud.create_comment(db, post_id, comment)
    if db_comment is None:
        raise HTTPException(404, "Post not found")
    return {**schemas.CommentOut.model_validate(db_comment).model_dump(), "like_count": 0}


@app.delete("/comments/{comment_id}", status_code=204)
def remove_comment(comment_id: int, db=Depends(get_db)):
    if not crud.delete_comment(db, comment_id):
        raise HTTPException(404, "Comment not found")


# ---------- Likes ----------

@app.post("/posts/{post_id}/like", response_model=schemas.LikeOut)
def like_post(post_id: int, like: schemas.LikeCreate, db=Depends(get_db)):
    if not crud.get_post(db, post_id):
        raise HTTPException(404, "Post not found")
    liked, count = crud.toggle_post_like(db, post_id, like.user_id)
    return {"liked": liked, "like_count": count}


@app.post("/comments/{comment_id}/like", response_model=schemas.LikeOut)
def like_comment(comment_id: int, like: schemas.LikeCreate, db=Depends(get_db)):
    liked, count = crud.toggle_comment_like(db, comment_id, like.user_id)
    return {"liked": liked, "like_count": count}
