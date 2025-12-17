# Tutorial: Cómo Crear un Módulo

Este tutorial te guiará paso a paso para crear un nuevo módulo en nuestro sistema, similar a Odoo 17.
Vamos a crear un módulo de ejemplo llamado `Library` para gestionar libros.

## 4. Seguridad (Nuevo)

Para que un usuario pueda acceder a tu módulo via API, asegúrate de:
1.  Tener una **API Key** válida (ver README).
2.  Tener permisos de acceso en `ir.model.access` para los modelos que intenta consultar.
    - Ejemplo SQL para dar permisos totales al usuario ID 2 sobre `library.book`:
      ```sql
      INSERT INTO ir_model_access (model_id, user_id, perm_read, perm_write, perm_create, perm_unlink) 
      VALUES ('library.book', 2, true, true, true, true);
      ```

      ```

## 5. Herencia y Extensión de Modelos
Puedes extender modelos existentes (como `res.users` o `library.book`) desde otro módulo usando `_inherit`.

### Ejemplo
```python
from core.orm.base import BaseModel
from core.orm.fields import Char

class ResUsersExtension(BaseModel):
    _inherit = 'res.users'
    
    github_profile = Char(string="GitHub Profile")
```
Esto agregará automáticamente el campo `github_profile` a la tabla `res_users` existente.

### Herencia Múltiple (Mixins)
También puedes heredar de múltiples modelos pasando una lista a `_inherit`. Esto es útil para composiciones tipo Mixin.

```python
class ModelExtension(BaseModel):
    _inherit = ['target.model', 'mixin.model']

    def method(self):
        # MRO: ModelExtension -> TargetModel -> MixinModel -> BaseModel
        return super().method()
```

## 6. Profundizando
e un Módulo
Cada módulo reside en su propia carpeta dentro del directorio `modules/`.
La estructura mínima es:
```
modules/
    library/              <-- Nombre técnico del módulo
        __manifest__.py   <-- Archivo de definición
        __init__.py       <-- Punto de entrada Python
        models/           <-- Directorio de modelos
            __init__.py
            book.py       <-- Definición del modelo Book
```

## Paso 1: Crear el Directorio del Módulo
Crea la carpeta `modules/library` y `modules/library/models`.

## Paso 2: Crear el Manifiesto (__manifest__.py)
Este archivo define los metadatos y dependencias.
Crea `modules/library/__manifest__.py`:
```python
{
    'name': 'Library Management',
    'version': '1.0',
    'description': 'Simple module to manage books',
    'depends': ['base'],  # Depende del módulo base (res.users, etc)
    'data': [],
}
```

## Paso 3: Inicializar el paquete Python (__init__.py)
Crea `modules/library/__init__.py` para que Python lo reconozca como paquete e importe los modelos:
```python
from . import models
```

Crea `modules/library/models/__init__.py`:
```python
from . import book
```

## Paso 4: Definir el Modelo (models/book.py)
Aquí definimos la estructura de la tabla y la lógica.
Crea `modules/library/models/book.py`:
```python
from core.orm.base import BaseModel
from core.orm.fields import Char, Integer, Boolean, Many2one

class Book(BaseModel):
    _name = "library.book"
    _description = "Book"

    name = Char(string="Title", required=True)
    active = Boolean(string="Active", default=True)
    pages = Integer(string="Pages")
    author_id = Many2one("res.partner", string="Author")

    def make_unavailable(self):
        # Ejemplo de lógica de negocio
        self.write({'active': False})
```

## Paso 5: Instalar / Actualizar
Simplemente reinicia el servidor. El sistema detectará el nuevo módulo, resolverá las dependencias y creará automáticamente la tabla `library_book` en PostgreSQL con las columnas definidas.

## Paso 6: Verificación
Puedes verificar que el modelo se cargó llamando al endpoint raíz `/` o inspeccionando la base de datos.
Para usarlo desde otro código:
```python
# En cualquier método de otro modelo
books = self.env['library.book'].search([])
new_book = self.env['library.book'].create({
    'name': 'Odoo Development',
    'pages': 200
})
```
