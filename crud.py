from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


# ---------- Categories ----------

def get_categories(db: Session):
    return db.query(models.Category).order_by(models.Category.name).all()


def get_category_by_slug(db: Session, slug: str):
    return db.query(models.Category).filter(models.Category.slug == slug).first()


def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# ---------- Posts ----------

def _post_with_counts(db: Session, post: models.Post) -> dict:
    like_count = db.query(func.count(models.Like.id)).filter(models.Like.post_id == post.id).scalar()
    comment_count = db.query(func.count(models.Comment.id)).filter(models.Comment.post_id == post.id).scalar()
    data = schemas.PostOut.model_validate(post).model_dump()
    data["like_count"] = like_count or 0
    data["comment_count"] = comment_count or 0
    return data


def get_posts(db: Session, category_slug: str, skip: int = 0, limit: int = 20):
    category = get_category_by_slug(db, category_slug)
    if not category:
        return None
    posts = (
        db.query(models.Post)
        .filter(models.Post.category_id == category.id)
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_post_with_counts(db, p) for p in posts]


def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def create_post(db: Session, category_slug: str, post: schemas.PostCreate):
    category = get_category_by_slug(db, category_slug)
    if not category:
        return None
    db_post = models.Post(category_id=category.id, **post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(db: Session, post_id: int, updates: schemas.PostUpdate):
    db_post = get_post(db, post_id)
    if not db_post:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int) -> bool:
    db_post = get_post(db, post_id)
    if not db_post:
        return False
    db.delete(db_post)
    db.commit()
    return True


# ---------- Comments ----------

def get_comments(db: Session, post_id: int):
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    result = []
    for c in comments:
        like_count = db.query(func.count(models.Like.id)).filter(models.Like.comment_id == c.id).scalar()
        data = schemas.CommentOut.model_validate(c).model_dump()
        data["like_count"] = like_count or 0
        result.append(data)
    return result


def create_comment(db: Session, post_id: int, comment: schemas.CommentCreate):
    post = get_post(db, post_id)
    if not post:
        return None
    db_comment = models.Comment(post_id=post_id, **comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: int) -> bool:
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        return False
    db.delete(db_comment)
    db.commit()
    return True


# ---------- Likes ----------

def toggle_post_like(db: Session, post_id: int, user_id: int):
    existing = (
        db.query(models.Like)
        .filter(models.Like.post_id == post_id, models.Like.user_id == user_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(models.Like(post_id=post_id, user_id=user_id))
        db.commit()
        liked = True
    like_count = db.query(func.count(models.Like.id)).filter(models.Like.post_id == post_id).scalar()
    return liked, like_count or 0


def toggle_comment_like(db: Session, comment_id: int, user_id: int):
    existing = (
        db.query(models.Like)
        .filter(models.Like.comment_id == comment_id, models.Like.user_id == user_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(models.Like(comment_id=comment_id, user_id=user_id))
        db.commit()
        liked = True
    like_count = db.query(func.count(models.Like.id)).filter(models.Like.comment_id == comment_id).scalar()
    return liked, like_count or 0
