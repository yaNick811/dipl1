from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True  # Замените 'orm_mode' на 'from_attributes'

class BookBase(BaseModel):
    title: str
    author: str
    year: int

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True  # Замените 'orm_mode' на 'from_attributes'