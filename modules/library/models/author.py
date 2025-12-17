from core.orm.base import BaseModel
from core.orm.fields import Char

class LibraryAuthor(BaseModel):
    _name = "library.author"
    _description = "Library Author"

    name = Char(string="Name", required=True)
