from core.orm.base import BaseModel
from core.orm.fields import Char, Boolean, Text

class McpDefaultPrompt(BaseModel):
    _name = 'mcp.default.prompt'
    _description = 'MCP Default Prompt'
    # _order = 'name' # Not supported in new core BaseModel yet

    name = Char(string='Name', required=True)
    prompt_text = Text(string='Prompt Text', required=True) # html -> text
    active = Boolean(string='Active', default=True)
    starter_message = Text(string='Mensaje iniciador', required=False) # html -> text
