from odoo import api, fields, models

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    creator_kind = fields.Selection(
        selection=[('res_user', 'User'), ('ai', 'AI')],
        string='Creator',
        default='res_user',
        required=True,
        index=True,
    )


    @api.model
    def create(self, vals):
        if 'creator_kind' not in vals:
            kind = self._context.get('creator_kind')
            if kind in ('res_user', 'ai'):
                vals['creator_kind'] = kind
            else:
                vals['creator_kind'] = 'ai' if self._context.get('creator_kind') == 'ai' else 'res_user'
        return super().create(vals)



    def get_activity_context(self):
        activities = ["\n===CONTEXTO DE ACTIVIDADES===\n"]
        for rec in self.filtered(lambda x: x.active and x.creator_kind == "ai"):
            data = f"resumen: {rec.summary}\nnota: {rec.note}\nfecha de creación: {rec.create_date}\n"
            activities.append(data)
        activities.append("\n===FIN DEL CONTEXTO DE ACTIVIDADES===\n")
        return "\n".join(activities)