from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from core.orm.registry import Registry
import base64
import io

router = APIRouter(prefix="/attachment", tags=["Attachment"])

def get_env(request: Request):
    # Helper to get authenticated env
    conn = request.state.conn
    user_id = request.state.user_id
    from core.orm.environment import Environment
    # Assuming Environment doesn't need much context for now
    return Environment(conn.cursor(), user_id, {})

@router.post("/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    res_model: str = Form(None),
    res_id: int = Form(0),
    request: Request = None
):
    env = get_env(request)
    content = await file.read()
    encoded = base64.b64encode(content).decode('utf-8')
    
    vals = {
        "name": file.filename,
        "type": "binary",
        "datas": encoded,
        "mimetype": file.content_type,
        "file_size": len(content),
        "res_model": res_model,
        "res_id": res_id
    }
    
    attachment = env['ir.attachment'].create(vals)
    return {"id": attachment.id, "name": attachment.name}

@router.get("/{attachment_id}/download")
async def download_attachment(attachment_id: int, request: Request):
    env = get_env(request)
    attachment = env['ir.attachment'].browse([attachment_id])
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    if attachment.type == 'url':
        return {"url": attachment.url}
        
    if not attachment.datas:
         raise HTTPException(status_code=404, detail="No content in attachment")
         
    # Decode
    try:
        data = base64.b64decode(attachment.datas)
    except:
        raise HTTPException(status_code=500, detail="Corrupted data")
        
    return StreamingResponse(
        io.BytesIO(data), 
        media_type=attachment.mimetype or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"}
    )

@router.put("/{attachment_id}")
async def update_attachment(
    attachment_id: int,
    file: UploadFile = File(None),
    name: str = Form(None),
    res_model: str = Form(None),
    res_id: int = Form(None),
    request: Request = None
):
    env = get_env(request)
    attachment = env['ir.attachment'].browse([attachment_id])
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    vals = {}
    if name:
        vals["name"] = name
    if res_model:
        vals["res_model"] = res_model
    if res_id is not None:
        vals["res_id"] = res_id
        
    if file:
        content = await file.read()
        encoded = base64.b64encode(content).decode('utf-8')
        vals["datas"] = encoded
        vals["mimetype"] = file.content_type
        vals["file_size"] = len(content)
        
    if vals:
        attachment.write(vals)
        
    return {"id": attachment.id, "message": "Updated"}

@router.delete("/{attachment_id}")
async def delete_attachment(attachment_id: int, request: Request):
    env = get_env(request)
    attachment = env['ir.attachment'].browse([attachment_id])
    
    if not attachment:
         raise HTTPException(status_code=404, detail="Attachment not found")
         
    attachment.unlink()
    return {"message": "Deleted"}
