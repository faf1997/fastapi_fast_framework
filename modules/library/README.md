# Library Module

Este módulo implementa un sistema básico de gestión de libros.

## Endpoints

Asegúrate de tener una **API Key válida** (ver logs de inicio del contenedor) y reemplazar `TU_API_KEY` en los ejemplos.

### 1. Listar Libros (GET)
```bash
curl -X GET http://localhost:8000/library/books \
     -H "x-api-key: TU_API_KEY"
```

### 2. Crear Libro (POST)
```bash
curl -X POST http://localhost:8000/library/books \
     -H "Content-Type: application/json" \
     -H "x-api-key: TU_API_KEY" \
     -d '{
           "name": "El Señor de los Anillos",
           "isbn": "978-0544003415",
           "pages": 1216,
           "active": true
         }'
```

### 3. Actualizar Libro (PUT)
Reemplaza `1` con el ID del libro que deseas actualizar.
```bash
curl -X PUT http://localhost:8000/library/books/1 \
     -H "Content-Type: application/json" \
     -H "x-api-key: TU_API_KEY" \
     -d '{
           "name": "El Señor de los Anillos - Edición Especial",
           "pages": 1250
         }'
```

### 4. Eliminar Libro (DELETE)
Reemplaza `1` con el ID del libro que deseas eliminar.
```bash
curl -X DELETE http://localhost:8000/library/books/1 \
     -H "x-api-key: TU_API_KEY"
```
