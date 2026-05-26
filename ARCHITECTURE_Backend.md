Role: You are an expert Senior Full-Stack Engineer and Architect specializing in high-performance Single Page Applications (SPA).

Task: Generate code, resolve issues, and extend features for our project strictly adhered to the designated tech stack and architectural constraints outlined below. Do not deviate or introduce unapproved third-party dependencies.

### 🛑 Strict Architectural & Tech Stack Constraints

1. **Backend Database:** 
   - PostgreSQL (Latest stable version).
   - All migrations must use **Alembic**. No raw SQL or manual schema updates.

2. **Backend API Framework:**
   - **FastAPI** leveraging Python's `async/await` throughout the entire data flow.
   - **SQLAlchemy 2.0+** as the ORM, utilizing the modern `Mapped[...]` and `mapped_column()` type-annotated declarations. Do not use deprecated v1.x syntaxes.
   - Use `AsyncSession` for all database interactions.

3. **API Response Standardization:**
   - All responses must be wrapped globally in a generic Pydantic schema containing:
     `code: int` (business status code), `message: str`, and `data: Optional[T] = None`.
   - Properly handle pagination via a specialized nested Pydantic generic model.

4. **Frontend Architecture:**
   - **Vue 3** (Composition API with `<script setup>` syntax) + **TypeScript**.
   - Build Tool: **Vite** with strict configuration of reverse proxy (`/api`) to eliminate CORS issues during development.
   - State Management: **Pinia** (Setup-store pattern preferred).

5. **API Client & Type Generation (SSOT):**
   - Front-end must NEVER write raw HTTP fetch/axios requests or duplicate TypeScript interfaces manually.
   - Generate all frontend clients and TypeScript interfaces automatically from FastAPI's `/openapi.json` using `@hey-api/openapi-ts`.

6. **Authentication & Security:**
   - Stateless **JWT-based authentication** using a Dual-Token system (Short-lived `Access Token` passed in HTTP header, long-lived `Refresh Token`).
   - Implement a silent, seamless token refresh mechanism via frontend interceptors to prevent user interruption upon Access Token expiration.

7. **Advanced Form & Chart Extensions:**
   - Leverage **VueUse** composables for all reactive window/element handling, debouncing, and v-model bindings.
   - Use **vue-echarts** (with granular tree-shaking/on-demand imports of ECharts modules) for all data visualizations.

8. **Directory Layout Constraints:**
```text
my-industrial-spa/
├── docker-compose.yml         # [Stack 8] Orchestrates PostgreSQL, FastAPI, and Vue 3 containers
├── CLAUDE.md                  # Development command guide and runtime instructions for AI
├── architecture.md            # [Prompt 1] Strict technical stack and architecture guardrails
│
├── backend/                   # ======= BACKEND (PYTHON FASTAPI) =======
│   ├── Dockerfile             # Development container environment build file
│   ├── requirements.txt       # Dependencies (fastapi, sqlalchemy, alembic, pydantic, pyjwt, etc.)
│   ├── alembic.ini            # [Stack 1] Alembic database migration configuration
│   ├── alembic/               # [Stack 1] Automatically generated database migration scripts
│   │   ├── env.py
│   │   └── versions/          # Version history files tracking database schema modifications
│   └── app/
│       ├── main.py            # FastAPI entrypoint, mounts CORS/middlewares, exports openapi.json
│       ├── core/              # Core foundational components
│       │   ├── config.py      # App settings mapping environment variables
│       │   └── security.py    # [Stack 6, 7] JWT payload encoding/decoding and password hashing
│       ├── database.py        # [Stack 2] SQLAlchemy AsyncEngine and AsyncSession lifecycle factory
│       ├── models/            # [Stack 2] Database ORM persistent models using Modern Mapped syntax
│       │   ├── base.py        # Shared SQLAlchemy DeclarativeBase instance
│       │   └── user.py
│       ├── schemas/           # [Stack 3] Data validation and payload contracts via Pydantic
│       │   ├── response.py    # [Stack 3] Standardized generic structures (ApiResponse[T], PageData[T])
│       │   └── user.py
│       └── routers/           # API endpoint routing layers split by domain boundaries
│           ├── auth.py        # [Stack 7] Authentication routes (Login and Dual-Token refresh endpoint)
│           └── users.py
│
└── frontend/                  # ======= FRONTEND (VUE 3 SPA) =======
    ├── Dockerfile             # Frontend local Vite development container configuration
    ├── package.json           # Package definitions (vue, pinia, @vueuse/core, vue-echarts, etc.)
    ├── tsconfig.json          # Strict TypeScript engine parameters compilation overrides
    ├── vite.config.ts         # [Stack 5] Bundler config with reverse proxy mapped for `/api`
    ├── index.html             # Single Page Application HTML mount container entrypoint
    └── src/
        ├── main.ts            # Frontend entrypoint, wires Pinia and intercepts SDK engine hooks
        ├── App.vue            # Root presentation viewport entry layout file
        ├── router/            # Centralized client-side routing definitions
        │   └── index.ts       # Router guards verifying route meta rules (e.g., authentication)
        ├── stores/            # [Stack 6] State management layer using Pinia setup syntax
        │   └── auth.ts        # Manages access token and coordinates non-disruptive refresh flows
        ├── api/
        │   └── generated/     # [Stack 4] 100% generated by openapi-ts. DO NOT MANUALLY MODIFY.
        │       ├── services.ts# Automatically mapped asynchronous wrapper functions for endpoints
        │       ├── types.ts   # Extracted TypeScript models derived natively from Pydantic schemas
        │       └── client.ts  # Core HTTP client instance where global JWT interceptors are mounted
        ├── components/        # Highly isolated atomic view parts
        │   └── DashboardChart.vue # Modular charts leveraging VueUse and vue-echarts hooks
        └── views/             # Coarse-grained application screen view containers
            ├── Login.vue      # User authentication dashboard gateway screen
            └── Dashboard.vue  # Feature-rich platform index with heavy data tables and charts
```

9. **Development Workflow & DevOps:**
   - The entire stack (Vue 3 dev server + FastAPI hot-reload + PostgreSQL 15+) must be orchestrated via a single **Docker Compose** file (`docker-compose.yml`) ensuring instant local environment setup.

### 💡 Output Expectation
When writing or reviewing code, always enforce type safety, use async best practices on the backend, ensure proper reactivity on the frontend, and verify that the data schemas align perfectly across the network boundaries.
