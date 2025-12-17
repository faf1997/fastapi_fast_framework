from fastapi import APIRouter, Depends, Request
from core.orm.registry import Registry
from core.orm.environment import Environment

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

