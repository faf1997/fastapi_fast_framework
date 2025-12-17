from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.orm.environment import Environment

class BookCreate(BaseModel):
    name: str
    isbn: Optional[str] = None
    pages: Optional[int] = 0
    active: Optional[bool] = True
    author_id: Optional[int] = None
    publisher_id: Optional[int] = None

class BookUpdate(BaseModel):
    name: Optional[str] = None
    isbn: Optional[str] = None
    pages: Optional[int] = None
    active: Optional[bool] = None
    author_id: Optional[int] = None
    publisher_id: Optional[int] = None


router = APIRouter(prefix="/library", tags=["Library"])

@router.get("/books")
def get_books(request: Request):
    # Access connection from middleware
    conn = request.state.conn
    user_id = request.state.user_id
    env = Environment(conn.cursor(), user_id, {}) 

    
    books = env['library.book'].search([])
    return [
        {"id": b.id, "name": b.name, "isbn": b.isbn, "pages": b.pages} 
        for b in books
    ]

@router.post("/books")
def create_book(book: BookCreate, request: Request):
    conn = request.state.conn
    user_id = request.state.user_id
    env = Environment(conn.cursor(), user_id, {})
    
    vals = book.model_dump(exclude_unset=True)
    new_book = env['library.book'].create(vals)
    return {"id": new_book.id, "name": new_book.name}

@router.put("/books/{book_id}")
def update_book(book_id: int, book: BookUpdate, request: Request):
    conn = request.state.conn
    user_id = request.state.user_id
    env = Environment(conn.cursor(), user_id, {})
    
    book_record = env['library.book'].browse([book_id])
    if not book_record:
        raise HTTPException(status_code=404, detail="Book not found")
        
    vals = book.model_dump(exclude_unset=True)
    book_record.write(vals)
    return {"success": True, "message": "Book updated"}

@router.delete("/books/{book_id}")
def delete_book(book_id: int, request: Request):
    conn = request.state.conn
    user_id = request.state.user_id
    env = Environment(conn.cursor(), user_id, {})
    
    book_record = env['library.book'].browse([book_id])
    if not book_record:
        raise HTTPException(status_code=404, detail="Book not found")
        
    book_record.unlink()
    return {"success": True, "message": "Book deleted"}


