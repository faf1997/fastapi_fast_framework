from core.orm.base import BaseModel
from core.orm.fields import Char

class LibraryPublisher(BaseModel):
    _name = "library.publisher"
    _description = "Library Publisher"

    name = Char(string="Name", required=True)
