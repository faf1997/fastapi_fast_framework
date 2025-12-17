# Odoo-like FastAPI Core

Este proyecto es un framework backend modular inspirado en Odoo, construido con **FastAPI** y **PostgreSQL**.
**Versión del Core**: 1.0.0.0.0

## Características
- **ORM Personalizado**: Active Record con soporte para migraciones automáticas.
- **Sistema de Módulos**: Carga dinámica de módulos basada en manifiestos y dependencias.
- **Seguridad**: Sistema de permisos (ACL) por modelo y usuario.
- **Dockerizado**: Listo para desplegar con Docker Compose.

## Despliegue con Docker (Recomendado)

Para levantar la aplicación y la base de datos:

```bash
docker compose up --build -d
```
La API estará disponible en: [http://localhost:8000](http://localhost:8000)

## Gestión de Módulos

El sistema detecta automáticamente los módulos ubicados en la carpeta `modules/` al iniciar.

### Instalar un Módulo
1. Copia la carpeta de tu módulo (que debe contener `__manifest__.py`) dentro del directorio `modules/`.
2. Reinicia el servicio para que el sistema lo detecte y cree las tablas automáticamente.
   ```bash
   docker compose restart web
   ```

### Actualizar un Módulo
1. Realiza los cambios en el código de tu módulo (ej. agregar campos en un modelo).
2. Reinicia el servicio. El sistema ejecutará automáticamente la migración de esquema (agregar columnas nuevas) al arrancar.
   ```bash
   docker compose restart web
   ```

### Desinstalar un Módulo
1. Elimina la carpeta del módulo del directorio `modules/`.
2. Reinicia el servicio.
   > **Nota**: Actualmente, esto **no** elimina las tablas de la base de datos para preservar datos. Si deseas limpiar la DB, debes eliminar las tablas manualmente vía SQL.

## Ejecutar Tests

### Opción A: Dentro del Contenedor (Facil)
Si ya tienes el contenedor corriendo (paso anterior):

1.  Abre una terminal en el contenedor:
    ```bash
    docker compose exec web bash
    ```
2.  Ejecuta los tests:
    ```bash
    pytest tests/
    ```

### Opción B: Localmente
Requiere Python 3.10+ y PostgreSQL corriendo localmente.

1.  Crear entorno virtual e instalar dependencias:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  Configurar variables de entorno (o asegurar que Postgres tenga user/pass `postgres/postgres` y DB `odoo_fastapi`).
3.  Ejecutar:
    ```bash
    pytest tests/
    ```

## Documentación Adicional
- [Tutorial de Creación de Módulos](docs/tutorial.md)
# fastapi_fast_framework
