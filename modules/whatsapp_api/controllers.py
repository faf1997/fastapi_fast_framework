from fastapi import APIRouter, Request, HTTPException
from core.orm.environment import Environment
import json
import logging

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook_whatsapp", tags=["WhatsApp"])

def get_env(request: Request):
    conn = request.state.conn
    user_id = request.state.user_id # Might be None if public, handling below
    if not user_id:
        # Webhook is public usually, need admin or system user
        user_id = 1 
    return Environment(conn.cursor(), user_id, {})

@router.post("/messages-upsert")
async def messages_upsert(request: Request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    env = get_env(request)
    
    # Logic ported from whatsapp_webhook.py
    
    # Extract data
    data_dict = data
    # data_dict.get("data", ...) 
    
    message_content = data_dict.get("data", {}).get("message", {}).get("conversation", "")
    from_me = data_dict.get("data", {}).get("key", {}).get("fromMe", False)
    message_type = 'system' if from_me else 'customer'
    
    remote_jid = data_dict.get("data", {}).get("key", {}).get("remoteJid", "")
    remote_jid_alt = data_dict.get("data", {}).get("key", {}).get("remoteJidAlt", "")
    sender = data_dict.get("sender", "")
    
    customer_number = remote_jid.split('@')[0] if '@' in remote_jid else remote_jid
    
    # Search Partner
    # ResPartner filtered_number might be needed. 
    # Mock search: assuming filtered_number is populated.
    customers = env['res.partner'].search([('filtered_number', '=', customer_number)])
    
    # Create Message
    # Note: create_message in WhatsappMessage model was adapter. 
    # We can use create directly or the adapter method if ported.
    # Refactored WhatsappMessage has create_message adapter.
    
    vals = {
        'name': message_content,
        'message_type': 'ai' if '\u200b' in message_content else message_type,
        'message_id': data_dict.get("data", {}).get("key", {}).get("id", False),
        'from_me': from_me,
        'partner_ids': [(6, 0, customers.ids)] if customers else [],
        'remote_jid': remote_jid,
        'remote_jid_alt': remote_jid_alt,
        'sender': sender,
        'should_reply': data_dict.get("should_reply", False),
        'is_webhook': True # Trigger adapter logic in create_message
    }
    
    created_message = env['whatsapp.message'].create_message(vals)
    
    # Handle Attachments
    # WhatsappMessage.create_file returns attachment
    attachment = env['whatsapp.message'].create_file(data_dict)
    
    if attachment and created_message:
         # Write to message
         created_message.write({
             'file_ids': [(4, attachment.id)],
             'name': attachment.caption if (not created_message.name and attachment.caption) else created_message.name
         })
         
    if created_message and customers:
         for c in customers:
             # Add message to partner history
             # In Odoo: c.write({'whatsapp_message_ids': [(4, msg.id)]})
             # In this core: Many2many write might need explicit handling or simplified.
             # If `whatsapp_message_ids` is M2M, writing to it updates relation.
             # However, core ORM M2M write logic is basic.
             # Let's try.
             env['res.partner'].browse([c.id]).write({
                 'whatsapp_message_ids': [(4, created_message.id)]
             })

    return {'status': 'success'}
