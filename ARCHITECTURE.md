# FastAPI Odoo-like Core Architecture

This document outlines the architecture of the implemented FastAPI application, which mimics Odoo's modular structure.

```mermaid
graph TD
    Client[Client (Browser / API)] -->|HTTP Request| FastAPI[FastAPI App]

    subgraph "Web Layer"
        FastAPI --> Middleware[DB Session Middleware]
        Middleware -->|Auth check| Auth[Authentication Logic]
        Middleware -->|Get Connection| DBPool[DB Connection Pool]
        Middleware -->|Route Request| Router[Router Dispatch]
    end

    subgraph "Application Core"
        ModuleLoader[Module Loader] -->|Discovers & Loads| Modules
        Registry[Model Registry] -->|Stores| Models
        
        subgraph "ORM Layer"
            BaseModel[BaseModel]
            MetaModel[MetaModel]
            Fields[Fields]
            BaseModel -->|Uses| Registry
        end
    end

    subgraph "Modules System"
        Modules --> Base[Base Module]
        Modules --> Attachment[Attachment Module]
        Modules --> Library[Library Module]
        
        Base -->|Defines| User[res.users]
        Base -->|Defines| Partner[res.partner]
        Attachment -->|Defines| Attach[ir.attachment]
        
        User -.->|Inherits| BaseModel
        Attach -.->|Inherits| BaseModel
    end

    subgraph "Data Layer"
        DBPool -->|Acquires| Connection[psycopg2 Connection]
        Connection -->|Executes SQL| PostgreSQL[(PostgreSQL Database)]
    end

    Router -->|Calls| Controllers[Module Controllers]
    Controllers -->|Uses| Models[Module Models]
    Models -->|Inherits| BaseModel
    BaseModel -->|SQL Queries| Connection
```

## Component Description

### 1. Web Layer
- **FastAPI**: The main web framework handling HTTP requests.
- **Middleware**: A custom `db_session_middleware` manages database transactions per request.
    - Acquires a connection from the pool.
    - Performs authentication via `x-api-key`.
    - Commits transaction on success, rolls back on error.
    - Returns connection to the pool.

### 2. Application Core
- **Module Loader**: Scans the `modules/` directory, reads `__manifest__.py`, sorts modules by dependencies, and imports them.
- **ORM**: A custom Object-Relational Mapping system inspired by Odoo.
    - **Registry**: A singleton that keeps track of all available models.
    - **BaseModel**: The base class for all models, providing methods like `create`, `write`, `read`, `unlink`, and `search`.
    - **Fields**: Definitions for database columns (Char, Integer, Many2one, etc.).

### 3. Modules System
- The application is divided into independent modules (e.g., `base`, `attachment`).
- Each module defines **Models** (data structure) and **Controllers** (API endpoints).
- **Inheritance**: Models can extend existing models (in-place modification) using the `_inherit` attribute, similar to Odoo.

### 4. Data Layer
- **Database**: PostgreSQL.
- **Connection Handling**: Uses `psycopg2.pool.ThreadedConnectionPool` to manage database connections efficiently. Note that despite using FastAPI (Async), the database interactions are currently synchronous.
