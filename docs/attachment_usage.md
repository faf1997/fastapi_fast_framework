# Uso de Ir.Attachment

El modelo `ir.attachment` permite adjuntar archivos binarios a cualquier registro del sistema.

## Estructura del Modelo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | Char | Nombre del archivo (ej: nota.txt) |
| type | Selection | 'binary' o 'url' |
| datas | Binary | Contenido del archivo codificado en Base64 |
| url | Char | URL si el tipo es 'url' |
| res_model| Char | Nombre del modelo asociado (ej: res.partner) |
| res_id | Integer | ID del registro asociado |
| mimetype | Char | Tipo MIME (ej: text/plain) |

## API REST

El módulo `base` expone endpoints para gestionar archivos.

### Subir Archivo
**POST** `/attachment/upload`

**Body (Multipart):**
- `file`: Archivo a subir.
- `res_model` (opcional): Nombre del modelo.
- `res_id` (opcional): ID del registro.

**Respuesta:**
```json
{"id": 1, "name": "archivo.txt"}
```

### Descargar Archivo
**GET** `/attachment/{id}/download`

Retorna el flujo de bytes del archivo con el Content-Type adecuado.

### Actualizar Archivo
**PUT** `/attachment/{id}`

**Body (Multipart/Form):**
- `file` (opcional): Nuevo contenido.
- `name` (opcional): Nuevo nombre.
- `res_model` (opcional).

**Respuesta:**
```json
{"id": 1, "message": "Updated"}
```

### Eliminar Archivo
**DELETE** `/attachment/{id}`

**Respuesta:**
```json
{"message": "Deleted"}
```

## Ejemplos de Uso (Python Interno)

### Crear un adjunto (Binario)

```python
import base64

# Codificar contenido
content = b"Contenido del archivo..."
encoded_content = base64.b64encode(content).decode('utf-8')

# Crear registro
attachment = env['ir.attachment'].create({
    'name': 'archivo.txt',
    'type': 'binary',
    'datas': encoded_content,
    'res_model': 'res.partner',
    'res_id': partner_id,
    'mimetype': 'text/plain'
})
```

### Leer un adjunto

```python
attachment = env['ir.attachment'].browse([attachment_id])
decoded_content = base64.b64decode(attachment.datas)
print(decoded_content)
```

### Crear un adjunto (URL)

```python
env['ir.attachment'].create({
    'name': 'Enlace Externo',
    'type': 'url',
    'url': 'https://example.com',
    'res_model': 'res.partner',
    'res_id': partner_id
})
```
