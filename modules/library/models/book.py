from core.orm.base import BaseModel
from core.orm.fields import Char, Integer, Boolean, Many2one

class LibraryBook(BaseModel):
    _name = "library.book"
    _description = "Library Book"

    name = Char(string="Title", required=True)
    isbn = Char(string="ISBN")
    pages = Integer(string="Pages") 
    active = Boolean(string="Active", default=True)
    author_id = Many2one("library.author", string="Author")
    publisher_id = Many2one("library.publisher", string="Publisher")
    
