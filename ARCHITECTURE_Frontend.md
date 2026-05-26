# ARCHITECTURE.md

## 1. Core Tech Stack & Architectural Vision
This project is built as a highly cohesive, loosely coupled Single Page Application (SPA). All code generation, modifications, and refactoring tasks must strictly adhere to the following tech stack. Alternative third-party libraries are strictly prohibited unless explicitly requested:

*   **Core Framework**: Vue 3 (Composition API with `<script setup>` syntax)
*   **Build Tool**: Vite
*   **Routing**: Vue Router (Centralized setup with module-based auto-aggregation)
*   **State Management**: Pinia (Decentralized, independent stores)
*   **Network Requests**: Axios (Base configuration wrapper + domain-isolated APIs)

### 🧱 Component Building Principles
*   **Logic Separation**: UI rendering must be decoupled from business logic. Complex state and methods must be extracted into composable functions (Hooks) inside `hooks/` directories.
*   **High Cohesion, Low Coupling**: Components must remain highly independent. Use standard `props` and `emits` for communication. Avoid implicit cross-module dependencies.

---

## 2. Directory Layout Constraints
When creating new files, pages, or modules, the AI must strictly follow this directory topology:

```text
src/
├── App.vue             # There is exactly one `<AppShell>` in the app and it lives here
├── assets/             # Global static assets (common styles, global images, base icons)
├── components/         # 🏢 Global base UI components (pure presentational, no business logic)
├── composables/        # ⚓ Global common hooks (e.g., useAuth, useTheme)
├── router/             # 🛣️ Routing hub
│   ├── index.ts        # Main router entry (auto-scans and aggregates 'modules/')
│   └── modules/        # Route segmentations per business domain
├── store/              # 🏪 State management hub
│   ├── index.ts        # Pinia initialization entry
│   └── shell.ts        # Global app-shell UI state
├── utils/              # 🔧 Global utilities
│   └── request.ts      # Axios base configuration (interceptors, env setups)
└── views/              # 📦 Core isolation zone for business modules (Domain-driven Views)
    ├── [module_name]/  # Target functional business module (e.g., user, order)
    │   ├── api/        # 🔌 Domain-isolated API requests
    │   │   └── index.ts
    │   ├── components/ # 🧩 Private components exclusive to this module
    │   ├── hooks/      # ⚓ Private business logic hooks exclusive to this module
    │   ├── store/      # 🏪 [Optional] Module-specific Pinia stores
    │   ├── [Page].vue  # 📄 Module view pages
    │   └── [Page].vue
    └── [new_module]/   # 🚀 New feature expansion (fully isolated, mirrors the structure above)
```

---

## 3. Progressive Development & "Zero-Interference" Safeguards
To guarantee that newly added features never break or interfere with existing production modules, the AI must implement the following isolation strategies:

### 🔌 3.1 Interface Isolation: Module-Based API Management
*   **Global Foundation**: `src/utils/request.ts` handles only global token injection, base Axios instantiation, and unified error handling responses.
*   **Local Autonomy**: Creating a massive, unified global `api.ts` file is strictly forbidden. All API endpoints must be declared locally within their respective business modules at `views/[module_name]/api/index.ts`.
*   **Dependency Direction**: Pages can only import APIs from their own module's `api/index.ts` or explicitly designated global shared services.

### 🛣️ 3.2 Routing Isolation: Dynamic Module Registration
*   `src/router/index.ts` must use Vite's `import.meta.glob` to automatically scan and register route configurations from the `modules/` directory.
*   **Adding Features**: To add a new domain, create a new `[module_name].ts` file inside `src/router/modules/`. **Modifying the main router file (`index.ts`) directly is prohibited**.

### 🧩 3.3 Component & State Isolation
*   **The Locality Principle**: Do not lift a component or a Pinia store to global directories (`src/components/` or `src/store/modules/`) unless it is explicitly confirmed to be reused across at least **3 separate** business modules.
*   **Destruction Safety**: The system architecture must guarantee that running `rm -rf src/views/[module_name]` along with removing its respective route file allows the project to compile with zero errors and leave no trace of dead code.

---

## 4. AI Execution Constraints
When a code generation or modification prompt is received, the AI must execute the following self-check sequence:
1.  **Identify Boundaries**: Determine which specific `[module_name]` the task belongs to. If it is a completely new feature, scaffold a new directory under `views/`.
2.  **Protect Global Scope**: Unless explicitly commanded to refactor, do not modify files in `src/components/`, other unrelated business modules, or global utility files.
3.  **Code Style Consistency**: Always use TypeScript with `<script setup lang="ts">` syntax. Ensure strong typing for Axios response schemas and component Props.
