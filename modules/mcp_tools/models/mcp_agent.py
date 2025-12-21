from core.orm.base import BaseModel
from core.orm.fields import Char, Many2many, Boolean, Text

class McpAgent(BaseModel):
    _name = 'mcp.agent'
    _description = 'MCP Agent'

    name = Char(string='Agent Name', required=True)
    llm_model_name = Char(string='LLM Model Name', required=True)
    provider_base_url = Char(string='Provider Base URL')
    provider_api_key = Char(string='Provider API Key')
    
    tool_ids = Many2many(
        comodel_name='mcp.tools',
        relation='mcp_agent_tools_rel',
        column1='agent_id',
        column2='tool_id',
        string='Allowed Tools'
    )
    
    active = Boolean(string='Active', default=True)
    
    default_prompt_ids = Many2many(
        comodel_name='mcp.default.prompt',
        relation='mcp_agent_prompt_rel',
        column1='agent_id',
        column2='prompt_id',
        string='Default Prompt'
    )
    
    default_prompt_text = Text(string='Default Prompt Preview') # html -> text
    
    def ensure_one(self):
        if len(self) != 1:
            raise ValueError("Expected singleton: %s" % self)

    def get_default_prompt(self, values: dict = None):
        """
        formato de values:
        {
            "nombre_del_valor_dinamico_1": "Valor del valor dinamico 1 en string",
            "nombre_del_valor_dinamico_2": "Valor del valor dinamico 2 en string",
            ...
        }
        """
        self.ensure_one()
        buffer = ["===INSTRUCCIONES CONFIDENCIALES==="]
        
        # Access default_prompt_ids. Since it's a many2many, accessing it returns a RecordSet
        prompt_ids = self.default_prompt_ids
        for rec in prompt_ids:
            if not rec.prompt_text:
                continue
            
            final_prompt_text = False
            if values:
                # Need to instantiate mcp.tools to call its methods, or call them statically if they don't use self
                # find_double_brace_values uses self only for regex, but it's an instance method.
                # replace_variables also instance method.
                # In Odoo `self.env['model']` gives an empty recordset on which we can call methods.
                mcp_tools = self.env["mcp.tools"]
                
                prompt_values = mcp_tools.find_double_brace_values(rec.prompt_text)
                if prompt_values:
                    final_prompt_text = mcp_tools.replace_variables(rec.prompt_text, values)

            buffer.append('Todas tus respuestas deben ser en formato json:\n \
                {"message": "mensaje de respuesta"# mensaje de respuesta debe ser un mensaje de respuesta al cliente, no debe haber repetición semantica con los mensajes anteriores enviados al cliente\n \
                "should_reply":"true o false"# should_reply debe ser True si el mensaje no repite semanticamente alguno de los mensajes anteriores enviados al cliente \n \
                    }')
            buffer.append(final_prompt_text or rec.prompt_text)
            
        buffer.append("===FIN DE LAS INSTRUCCIONES CONFIDENCIALES===")
        buffer.append("\n")
        full_prompt = '\n'.join(buffer)
        return full_prompt.strip() if full_prompt else ''

    def create(self, vals):
        if 'name' in vals and vals['name']:
             existing = self.search([('name', '=', vals['name'])])
             if existing:
                 raise ValueError("Agent Name must be unique.")
        return super().create(vals)

    def write(self, vals):
        if 'name' in vals:
            for rec in self:
                if vals['name'] != rec.name:
                     existing = self.search([('name', '=', vals['name']), ('id', '!=', rec.id)])
                     if existing:
                         raise ValueError("Agent Name must be unique.")
        return super().write(vals)