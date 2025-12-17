from core.orm.base import BaseModel
from core.orm.fields import Integer
import logging
logger = logging.getLogger(__name__)

logger.info("DEBUG: Loading LibraryBookExtension")

class LibraryBookExtension(BaseModel):
    _inherit = "library.book"

    rating = Integer(string="Rating (1-5)")
