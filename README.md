# community-tab-demo
# Community API (FastAPI + PostgreSQL)

A JSON backend for a "community tab": posts organized into categories
(General, Work Culture, Ongoing Updates, ...), each with comments and likes.

## 1. Setup

```bash
cd community_api
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a PostgreSQL database, then copy `.env.example` to `.env` and fill in
your real connection string:

```bash
cp .env.example .env
```

Load the `.env` file before starting the app — either export it manually,
or add these two lines to the top of `main.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## 2. Run

```bash
uvicorn main:app --reload
```

On startup, the app creates the `categories`, `posts`, `comments`, and
`likes` tables if they don't exist, and seeds three default categories:
`general`, `work-culture`, `ongoing-updates`. Add more anytime via
`POST /categories`.

Interactive docs: http://localhost:8000/docs

## 3. Endpoints

| Method | Path                          | Purpose                          |
|--------|-------------------------------|-----------------------------------|
| GET    | `/categories`                 | List all categories               |
| POST   | `/categories`                 | Create a category                 |
| GET    | `/categories/{slug}/posts`    | List posts in a category          |
| POST   | `/categories/{slug}/posts`    | Create a post in a category       |
| GET    | `/posts/{id}`                 | Get a post with its comments      |
| PATCH  | `/posts/{id}`                 | Edit a post                       |
| DELETE | `/posts/{id}`                 | Delete a post                     |
| GET    | `/posts/{id}/comments`        | List comments on a post           |
| POST   | `/posts/{id}/comments`        | Add a comment                     |
| DELETE | `/comments/{id}`              | Delete a comment                  |
| POST   | `/posts/{id}/like`            | Toggle like on a post             |
| POST   | `/comments/{id}/like`         | Toggle like on a comment          |

Every response is JSON, matching what you asked for on the frontend/backend
contract.

## 4. Example requests

```bash
# Create a post in Work Culture
curl -X POST http://localhost:8000/categories/work-culture/posts \
  -H "Content-Type: application/json" \
  -d '{"author_id": 1, "author_name": "Asha", "title": "Remote days?", "content": "How many WFH days does everyone get?"}'

# Comment on post 1
curl -X POST http://localhost:8000/posts/1/comments \
  -H "Content-Type: application/json" \
  -d '{"author_id": 2, "author_name": "Rahul", "content": "We get 2 a week."}'

# Like post 1 (call again with the same user_id to unlike)
curl -X POST http://localhost:8000/posts/1/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
```

## 5. Notes / next steps

- **Auth**: `author_id` / `user_id` are currently passed in plain by the
  caller — there's no authentication here. Wire these up to your real login
  system (e.g. verify a JWT and pull the user ID from it) before this goes
  live, so people can't post or like as someone else.
- **Migrations**: `create_all()` is fine for local dev, but for schema
  changes down the line use [Alembic](https://alembic.sqlalchemy.org/)
  instead of relying on it.
- **Pagination**: `GET /categories/{slug}/posts` supports `?skip=&limit=`
  already; add the same to comments if a post gets a lot of them.
- **CORS**: if your frontend runs on a different origin, add
  `fastapi.middleware.cors.CORSMiddleware` to `main.py`.
