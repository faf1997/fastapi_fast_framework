from odoo import models, fields


class AssistIAWizard(models.TransientModel):
    _name = 'assist.ia.wizard'
    _description = 'Assist IA Wizard'

    ia_conversation_id = fields.Many2one(
        comodel_name='ia.conversation',
        string='Conversación'
    )

    agent_id = fields.Many2one(
        'mcp.agent',
        string='Agent',
        required=True,
        domain="[('active', '=', True)]",
        help="Select the IA agent to process your message."
    )

    message_ids = fields.Many2many(
        'ia.message',
        string='Conversaciones'
    )

    message = fields.Html(
        string='Mensaje'
    )


    def _create_message(self, message:str, message_type: str = 'user'):
        self.ensure_one()
        message_rec = self.env['ia.message'].create({
            'name': message,
            'conversation_id': self.ia_conversation_id.id if self.ia_conversation_id else False,
            'message_type': message_type,
        })
        self.message_ids = [(4, message_rec.id)]


    def send_ia_message(self):
        self.ensure_one()
        
        if not self.message:
            return {'type': 'ir.actions.act_window_close'}
        
        # Crear conversación si no existe
        if not self.ia_conversation_id:
            self.ia_conversation_id = self.env['ia.conversation'].create({
                'name': f'Conversación {fields.Datetime.now()}',
                # Otros campos necesarios para tu modelo ia.conversation
            })
        
        # Obtener mensajes anteriores de la conversación
        context_messages = ''
        if len(self.message_ids) > 0:
            context_messages = self.env['ia.conversation'].get_recordset_in_string_format(self.message_ids)#.sorted('id')

        # Concatenar mensajes completos
        full_message = f'{context_messages}\n===NUEVO MENSAJE==={self.message}===FIN NUEVO MENSAJE===' if context_messages else f"===NUEVO MENSAJE==={self.message}===FIN NUEVO MENSAJE==="

        # 1. Primero crear el mensaje del usuario
        self._create_message(self.message, 'user')
        
        # 2. Ejecutar MCP
        try:
            # Retrieve the agent name from the selected agent_id
            # agent_id is required, so self.agent_id should always be set.
            agent_id = self.agent_id.id
            
            mcp_response_message = self.env['mcp.launcher'].sudo().mcp_run(
                messages=full_message,
                agent_id=agent_id
            )
            
            # 3. Crear mensaje de respuesta de IA
            if mcp_response_message and mcp_response_message.get('should_reply', False):
                self._create_message(mcp_response_message.get('result'), 'ia')

        except Exception as e:
            # Manejar errores del MCP
            error_message = f"Error en MCP: {str(e)}"
            self._create_message(error_message, 'system')
        
        # 4. Limpiar el campo mensaje para el siguiente
        self.message = ''
        
        # 5. Recargar todos los mensajes de la conversación en el wizard
        conversation_messages = self.env['ia.message'].search([
            ('conversation_id', '=', self.ia_conversation_id.id)
        ], order='create_date asc')
        
        self.message_ids = [(6, 0, conversation_messages.ids)]
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Conversación {self.ia_conversation_id.name}',
            'res_model': 'assist.ia.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('mcp_tools.view_assist_ia_wizard_form').id,
            'res_id': self.id,
            'target': 'new',
            'order': 'id asc',
            'context': {
                'default_ia_conversation_id': self.ia_conversation_id.id,
                'default_message_ids': sorted(self.ia_conversation_id.message_ids.ids),
            }
        }


