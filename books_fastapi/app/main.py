from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import crud, models, schemas, security
from .database import SessionLocal, engine
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(security.get_db)):
    user = crud.get_user_by_username(db, username=username)
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
    crud.create_user(db, schemas.UserCreate(username=username, password=password))
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(security.get_db)):
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

@app.get("/", response_class=HTMLResponse)
async def book_list(request: Request, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    books = crud.get_books(db, user_id=current_user.id)
    return templates.TemplateResponse("book_list.html", {"request": request, "books": books})

@app.get("/add", response_class=HTMLResponse)
async def add_book_page(request: Request, current_user: schemas.User = Depends(security.get_current_user)):
    return templates.TemplateResponse("add_book.html", {"request": request})

@app.post("/add", response_class=HTMLResponse)
async def add_book(request: Request, title: str = Form(...), author: str = Form(...), year: int = Form(...), db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    book = schemas.BookCreate(title=title, author=author, year=year)
    crud.create_book(db, book, user_id=current_user.id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/edit/{book_id}", response_class=HTMLResponse)
async def edit_book_page(request: Request, book_id: int, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    book = crud.get_book(db, book_id=book_id)
    if book.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this book")
    return templates.TemplateResponse("edit_book.html", {"request": request, "book": book})

@app.post("/edit/{book_id}", response_class=HTMLResponse)
async def edit_book(request: Request, book_id: int, title: str = Form(...), author: str = Form(...), year: int = Form(...), db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    book = crud.get_book(db, book_id=book_id)
    if book.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this book")
    book_update = schemas.BookCreate(title=title, author=author, year=year)
    crud.update_book(db, book_id=book_id, book=book_update)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/delete/{book_id}", response_class=HTMLResponse)
async def delete_book_page(request: Request, book_id: int, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    book = crud.get_book(db, book_id=book_id)
    if book.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this book")
    return templates.TemplateResponse("delete_book.html", {"request": request, "book": book})

@app.post("/delete/{book_id}", response_class=HTMLResponse)
async def delete_book(request: Request, book_id: int, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    book = crud.get_book(db, book_id=book_id)
    if book.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this book")
    crud.delete_book(db, book_id=book_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)