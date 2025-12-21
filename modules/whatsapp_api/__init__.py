from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)

def _create_filtered_numbers(env):
    partners = env['res.partner'].search([])
    for rec in partners:
        if rec.mobile:
            rec.filtered_number = ''.join([char for char in rec.mobile if char.isdigit()])