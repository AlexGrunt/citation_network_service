from typing import List
from urllib import request

from fastapi import FastAPI, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

from sqlalchemy.schema import CreateSchema

from uuid import UUID
from app.api import crud, models, schemas
from app.api.database import SessionLocal, engine
from app.core.config import SCHEMA_NAME


class SessionManager:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, _, _a, _b):
        self.db.close()


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    if not engine.dialect.has_schema(engine, SCHEMA_NAME):
        engine.execute(CreateSchema(SCHEMA_NAME))
    models.Base.metadata.create_all(bind=engine)


@app.post("/users/registration/", status_code=status.HTTP_200_OK)
def register_user(user: schemas.User):
    with SessionManager() as db:
        return schemas.User.from_orm(crud.try_add_user(db, user))


@app.get(
    "/users/get_user/", response_model=schemas.User, status_code=status.HTTP_200_OK
)
def get_user(login: str):
    with SessionManager() as db:
        return schemas.User.from_orm(crud.get_user_by_login(db, login))


@app.post("/users/login_user/", status_code=status.HTTP_200_OK)
def login_user(login: str, password: str):
    with SessionManager() as db:
        return schemas.User.from_orm(crud.try_login(db, login, password))


@app.put(
    "/users/change_password",
    response_model=schemas.User,
    status_code=status.HTTP_200_OK,
)
def change_password(User_id: UUID, new_password: str):
    with SessionManager() as db:
        return schemas.User.from_orm(crud.change_password(db, User_id, new_password))


@app.get("/author/", response_model=schemas.Author, status_code=status.HTTP_200_OK)
def get_author(author_id: UUID):
    with SessionManager() as db:
        return schemas.Author.from_orm(crud.get_author(db, author_id))


@app.get(
    "/authors/", response_model=List[schemas.Author], status_code=status.HTTP_200_OK
)
def get_authors(skip: int = 0, limit: int = 10):
    with SessionManager() as db:
        return [
            schemas.Author.from_orm(author)
            for author in crud.get_authors(db, skip, limit)
        ]


@app.delete("/author/", response_model=schemas.Author, status_code=status.HTTP_200_OK)
def delete_author(author_id: UUID):
    with SessionManager() as db:
        return schemas.Author.from_orm(crud.delete_author(db, author_id))


@app.put("/author/", response_model=schemas.Author, status_code=status.HTTP_200_OK)
def update_author(author_id: UUID, author: schemas.AuthorBase):
    with SessionManager() as db:
        return schemas.Author.from_orm(crud.update_author(db, author_id, author))


@app.post(
    "/author/", response_model=schemas.Author, status_code=status.HTTP_201_CREATED
)
def create_author(author: schemas.AuthorBase):
    with SessionManager() as db:
        return schemas.Author.from_orm(crud.create_author(db, author))


@app.get("/text/", response_model=schemas.Text, response_class=HTMLResponse, status_code=status.HTTP_200_OK)
def get_text(request: Request, text_id: UUID):
    with SessionManager() as db:
        text = crud.get_text(db, text_id)
        return templates.TemplateResponse(
            "texts.html",
            {
                "request" : request,
                "title": text.title,
                "year": text.year,
                "author": text.authors[0].name,
                "n_citation": text.n_citation,
                "abstract" : text.abstract
            },
        )


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})


@app.get("/texts/", response_model=List[schemas.Text], status_code=status.HTTP_200_OK)
def get_texts(request: Request, skip: int = 0, limit: int = 10):
    with SessionManager() as db:
        texts = crud.get_texts(db, skip, limit)

        return templates.TemplateResponse(
            "texts.html", {"request" : request, "texts": texts}
        )


@app.post("/text/", response_model=schemas.Text, status_code=status.HTTP_201_CREATED)
def create_text(text: schemas.TextBase):
    with SessionManager() as db:
        return schemas.Text.from_orm(crud.create_text(db, text))


@app.delete("/text/", response_model=schemas.Text, status_code=status.HTTP_200_OK)
def delete_text(text_id: UUID):
    with SessionManager() as db:
        return schemas.Text.from_orm(crud.delete_text(db, text_id))


@app.post(
    "/citation/", response_model=schemas.Citation, status_code=status.HTTP_201_CREATED
)
def create_citation(citation: schemas.Citation):
    with SessionManager() as db:
        return schemas.Citation.from_orm(crud.create_citation(db, citation))


@app.get(
    "/search/", response_model=List[schemas.Search], status_code=status.HTTP_200_OK
)
def get_search(request, limit=30):
    with SessionManager() as db:
        return [
            schemas.Search.from_orm(request)
            for request in crud.get_search(db, request, limit)
        ]
