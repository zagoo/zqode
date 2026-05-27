# Functional Design Document: LLM API Gateway Platform

**Document Status:** Final FDD after validation and refinement  
**Source FRD:** Uploaded `frd.md`  
**Language:** English  
**Platform:** Internal Enterprise LLM API Gateway Platform  

---

## 0. Domain Concept & Requirements Knowledge Base

### 0.1 Source Scope Summary

The source FRD defines an internal enterprise platform that exposes OpenAPI-compatible gateway endpoints to employees and forwards requests to external LLM providers. The platform enables employees to configure their preferred coding IDEs, plugins, or CLI tools with internal Gateway URLs and enterprise-issued API Keys. The gateway validates API Key status, user account status, quota availability, model/provider configuration, and then forwards requests to configured LLM providers. It records usage details, deducts quota based on actual token usage, and exposes analytics dashboards.

The platform is decomposed into the following functional areas:

| Area | UI | Purpose |
|---|---:|---|
| Platform Login | Yes | Enterprise email login using one-time random password delivery |
| Platform Administration | Yes | Configure providers, models, internal OpenAPI endpoints, users, roles, API Key validity extension, and quota reset strategy |
| Workbench / Developer Portal | Yes | User self-service API Key application, own-key lifecycle management, model/API discovery |
| API Service Layer | No | High-concurrency OpenAI/Anthropic-compatible runtime gateway |
| Data Analytics & Reporting | Yes | Usage, cost, ranking, prompt classification, detail, and summary analytics |

---

### 0.2 Business Concepts and Canonical Terminology

| Canonical Term | Definition |
|---|---|
| LLM API Gateway Platform | Internal enterprise platform that exposes gateway endpoints and proxies requests to external LLM providers |
| Enterprise OpenAPI | Internal Gateway endpoint configured and exposed to employees |
| LLM Provider | External LLM API service provider configured by System Administrator |
| Model | Provider model with input/output token pricing |
| API Key | User-owned gateway credential used by IDEs, plugins, CLI tools, or internal clients |
| API Key Secret | Full raw API Key value shown only once at creation time |
| API Key Mask | Display-safe masked form, such as `sk-...abcd` |
| User | Enterprise employee account identified by enterprise email |
| Role | Permission and policy bundle assigned to a User |
| System Administrator | Platform administrator role with full platform management access |
| Team Manager | Role with Workbench access and broader analytics access |
| Normal User | Standard user role with Workbench and personal analytics access |
| Cost Limit | Maximum allowed spend for a User in a quota/accounting period |
| Quota Balance | Current period consumed and remaining quota for a User |
| Quota Reset Policy | Rule defining whether and when quota resets |
| Inference Request | Runtime model request submitted through the gateway |
| Usage Log | Per-request business log containing API Key, timestamp, model, token counts, prompt, response, and status |
| Cost Record | Cost calculation record linked to a Usage Log |
| Consumption Statistics | Aggregated usage and cost metrics |
| Prompt Category | Automatically assigned category label for prompt analytics |

---

### 0.3 Actors and Roles

| Role | Description | Primary Capabilities |
|---|---|---|
| System Administrator | Full administrative operator | Login, platform administration, Workbench, API Key self-service, personal/ranking/prompt/detail/summary analytics |
| Team Manager | Managerial user | Login, Workbench, API Key self-service, model/API viewing, personal/ranking/prompt/detail/summary analytics |
| Normal User | Standard employee/developer | Login, Workbench, own API Key management, model/API viewing, personal/ranking/prompt analytics |
| Runtime API Caller | IDE/plugin/CLI/internal client using API Key | Gateway API invocation only; no platform UI session |

Runtime gateway access is not role-authenticated directly. It is API-Key-authenticated and then indirectly checks the owning User, API Key status, API Key expiry, User status, Model/Provider availability, and quota state.

---

### 0.4 Domain Entity Inventory

#### Identity and Access Entities

| Entity | Key Attributes | Notes |
|---|---|---|
| User | enterprise_email, role_id, cost_limit_source, account_status | Account identified by enterprise email |
| Role | role_name, permissions, default_cost_limit_amount, api_key_validity_days | Defines permissions and API Key validity policy |
| LoginChallenge | enterprise_email, random_password_hash, expires_at, status | One-time random password login challenge |
| PlatformSession | user_id, session_token_hash, expires_at, revoked_at | Platform UI session |
| PermissionAction | permission_action, module_id, description | Canonical action-level permission |

#### Provider and Model Entities

| Entity | Key Attributes | Notes |
|---|---|---|
| LLMProvider | provider_name, api_base_url, api_key_ciphertext, api_key_mask | Provider secret is never returned after create/update |
| Model | provider_id, model_name, input/output price per million tokens, currency | Pricing source for cost calculation |
| EnterpriseOpenAPI | api_name, api_type, gateway_url, usage_description | Internal API endpoint metadata |

#### API Key and Quota Entities

| Entity | Key Attributes | Notes |
|---|---|---|
| APIKey | owner_user_id, key_name, api_key_secret_hash, api_key_mask, expires_at, status | Raw secret shown only once |
| QuotaResetPolicy | reset_mode, reset_day_of_month, reset_time, timezone | Supports monthly reset or no automatic reset |
| QuotaPeriod | period_type, period_start_at, period_end_at | Accounting period |
| QuotaBalance | user_id, quota_period_id, cost_limit_amount, consumed_amount, remaining_amount | Runtime quota state |

#### Runtime and Analytics Entities

| Entity | Key Attributes | Notes |
|---|---|---|
| InferenceRequest | api_key_secret, gateway_url, model, prompt/messages | Runtime input from client |
| UsageLog | API Key, User, Model, prompt, response, tokens, status | Source of truth for analytics |
| CostRecord | usage_log_id, token counts, unit prices, cost fields | Cost calculation and quota deduction source |
| PromptClassificationResult | usage_log_id, prompt_category_id, status, confidence_score | Supports prompt category analytics |
| AnalyticsAggregate | aggregate_type, period, user, model, category, token/cost totals | Performance optimization for dashboards |

---

### 0.5 Core Process Flows

#### F01 — System Administrator Initialization

1. Deployment configuration contains initial administrator enterprise email.
2. First startup after database connection validates the email and allowed domain.
3. System ensures the built-in System Administrator role exists.
4. If a User with the configured email does not exist, insert User with role = System Administrator and account_status = ENABLED.
5. Operation is idempotent by unique enterprise email constraint.

#### F02 — Enterprise Email Login

1. User enters enterprise email.
2. System validates format and allowed enterprise domain.
3. System creates a one-time LoginChallenge and sends a random password to the enterprise email.
4. User enters random password.
5. System validates challenge, random password, account existence, and account status.
6. System creates platform session and returns User context and permissions.

#### F03 — Platform Administration

1. System Administrator logs in.
2. Administrator manages LLM Providers, Models, Enterprise OpenAPIs, Users, Roles, API Key validity extension, and Quota Reset Policy.
3. Mutations use idempotency keys for create operations and optimistic locking for update/delete operations.
4. Runtime-affecting mutations emit cache invalidation events.

#### F04 — API Key Application and Lifecycle

1. User opens Workbench.
2. User enters API Key name and expiry date.
3. System checks requested expiry does not exceed assigned Role's `api_key_validity_days`.
4. System generates a unique API Key Secret, stores irreversible hash and mask, and returns full secret once.
5. User can later list masked API Keys, enable/disable own keys, or soft-delete own keys.
6. System Administrator can view all API Keys and extend validity only.

#### F05 — Runtime Gateway Request

1. Client calls Enterprise OpenAPI Gateway URL using API Key.
2. Gateway validates API Key existence, status, expiry, owning User status, Model, Provider, and quota precheck.
3. Gateway creates UsageLog record with status `PROVIDER_IN_FLIGHT`.
4. Gateway forwards request to provider.
5. Gateway extracts actual provider token usage.
6. Gateway calculates cost using Model input/output unit prices.
7. Gateway updates UsageLog, inserts CostRecord, deducts QuotaBalance, and inserts outbox event in one transaction.
8. Gateway returns provider-compatible response to caller.

#### F06 — Analytics

1. UsageLog and CostRecord are source of truth.
2. Analytics Aggregation Worker creates aggregate records for dashboard performance.
3. Prompt Classification Worker classifies prompts asynchronously.
4. M05 dashboards expose personal usage, ranking, prompt category statistics, detail, and summary views according to permissions.

---

### 0.6 Functional Requirements Knowledge Graph

```text
Deployment Config
  └─ initializes ──> System Administrator User

Platform Login
  ├─ validates Enterprise Email domain
  ├─ creates LoginChallenge
  ├─ checks User.account_status
  └─ creates PlatformSession
       └─ authorizes M02, M03, M05 UI APIs

Platform Administration
  ├─ manages LLMProvider
  ├─ manages Model + Pricing
  ├─ manages EnterpriseOpenAPI
  ├─ manages User
  ├─ manages Role + Permissions
  ├─ extends APIKey expiry only
  └─ configures QuotaResetPolicy

Workbench
  ├─ reads Model catalog
  ├─ reads EnterpriseOpenAPI catalog
  ├─ creates APIKey
  ├─ lists own APIKeys
  ├─ enables/disables own APIKeys
  └─ deletes own APIKeys

API Service Layer
  ├─ validates APIKey
  ├─ validates User status
  ├─ checks QuotaBalance
  ├─ resolves EnterpriseOpenAPI route
  ├─ resolves Model and Provider
  ├─ forwards Provider request
  ├─ extracts token usage
  ├─ calculates CostRecord
  ├─ deducts QuotaBalance
  └─ writes UsageLog

Data Analytics
  ├─ reads UsageLog
  ├─ reads CostRecord
  ├─ reads PromptClassificationResult
  ├─ reads AnalyticsAggregate
  └─ renders dashboards
```

---

### 0.7 Design Assumptions and Ambiguities

| ID | Area | Assumption / Interpretation |
|---|---|---|
| A01 | User identity | Users are identified by enterprise email, normalized to lowercase |
| A02 | Role assignment | Each User has exactly one Role |
| A03 | User onboarding | Users are admin-created or provisioned before login; open self-registration is not introduced |
| A04 | Login | Login uses one-time random password sent by email, not persistent passwords |
| A05 | API Key storage | Raw API Key Secret is never stored recoverably; hash and mask are stored |
| A06 | API Key ownership | API Keys belong to individual Users only; no shared/team keys are introduced |
| A07 | Model pricing | Model prices are stored per million input tokens and per million output tokens |
| A08 | Cost basis | Provider response token usage is authoritative for cost deduction |
| A09 | Quota concurrency | Quota deduction must be atomic under concurrent gateway requests |
| A10 | Prompt classification | Automatic classification is required, but taxonomy and classifier engine are product decisions |
| A11 | Team Manager scope | Team Manager detail/summary analytics are allowed by permission, but no team hierarchy is invented |
| A12 | Ranking privacy | Other users' enterprise emails are hidden in ranking; current user appears as `You` |
| A13 | Admin API Key scope | Administrator can view all keys and extend validity only; no admin reveal/disable/delete is added |
| A14 | Streaming | Streaming support is not specified. If required later, token accounting must be adapted |

---

### 0.8 Research Findings & External References

The FDD was enriched using current architecture references for AI gateway design, RBAC, token metering, logging, idempotency, and high-availability worker patterns. These references guide implementation choices without expanding FRD scope.

| Reference | Design Use |
|---|---|
| Kong AI Gateway | Provider-agnostic gateway, centralized credentials, routing, usage analytics |
| Envoy AI Gateway | Secure/scalable LLM traffic management and observability |
| LiteLLM Gateway | Unified LLM proxy, virtual keys, spend tracking concepts |
| Cloudflare AI Gateway Analytics and Logging | Request, provider, prompt/response, token, cost, duration analytics/logging patterns |
| OpenAI API Reference | Usage normalization with input/output/total token fields |
| Anthropic API Docs | Usage normalization and token counting caveats |
| NIST RBAC | User-role-permission model |
| OWASP Authorization Cheat Sheet | Deny-by-default, least privilege, endpoint authorization checks |
| OWASP REST Security Cheat Sheet | HTTPS, endpoint-level access control, API-key security |
| OWASP Secrets Management Cheat Sheet | Secret storage, rotation, auditing, and least exposure |
| OWASP Logging Cheat Sheet | Structured application logging and sensitive-data handling |
| OpenTelemetry | Trace correlation, structured telemetry, vendor-neutral observability |
| AWS SQS / RabbitMQ / Celery concepts | Visibility timeout, at-least-once delivery, retries, DLQ, idempotent workers |
| Kubernetes lifecycle guidance | Health checks, readiness/liveness probes, graceful shutdown |
| Stripe Idempotency | Safe retry semantics for create/update operations |
| REST ETag optimistic concurrency | Version preconditions for update/delete operations |

Research-enriched principles applied:

1. Separate control plane, runtime plane, and analytics plane.
2. Keep provider credentials centralized and hidden from end users.
3. Normalize provider token usage into a common input/output/total token schema.
4. Use actual provider response token usage for cost deduction.
5. Enforce authorization on every backend interface, not only via UI visibility.
6. Store API Key Secrets as irreversible hashes and show raw secret once.
7. Use UsageLog and CostRecord as analytics source of truth.
8. Use structured logs with trace correlation.
9. Use idempotency keys for create operations and optimistic locking for updates/deletes.
10. Use idempotent queue consumers with retry, backoff, and DLQ handling.

---

## 1. Executive Summary & Module Map

### 1.1 Module Decomposition

| Module ID | Category | Module Name | UI | Scope Boundary |
|---|---|---|---:|---|
| M00 | Core Module | Core Platform Foundation | No | Bootstrap, shared conventions, permission namespace, idempotency and common response standards |
| M01 | Platform Authentication & Login | Enterprise Email Login | Yes | Enterprise email random-password login, account status validation, session lifecycle |
| M02 | Platform Administration | Platform Administration Console | Yes | Provider/model/OpenAPI/user/role/API Key expiry/quota policy management |
| M03 | Workbench / Developer Portal | Developer Workbench | Yes | User API Key self-service and model/API discovery |
| M04 | API Service Layer | LLM Gateway Runtime API | No | Runtime gateway validation, provider forwarding, quota deduction, usage logging |
| M05 | Data Analytics & Reporting | Analytics Dashboard | Yes | Consumption statistics, ranking, prompt category statistics, detail, and summary analytics |

---

### 1.2 Module Dependency Graph

```text
M00 Core Platform Foundation
  ├─ seeds permission namespace
  ├─ bootstraps initial System Administrator
  └─ defines shared conventions

M01 Platform Authentication & Login
  ├─ reads User and Role data from M02 domain
  └─ provides platform session to M02, M03, M05

M02 Platform Administration
  ├─ manages Provider, Model, EnterpriseOpenAPI, User, Role, QuotaResetPolicy
  ├─ extends APIKey expiry only
  └─ emits config.changed events consumed by BS06

M03 Workbench
  ├─ consumes M01 session
  ├─ reads Role, Model, EnterpriseOpenAPI data
  ├─ creates and manages own APIKeys
  └─ supplies APIKeys to M04 runtime

M04 API Service Layer
  ├─ validates APIKeys created by M03
  ├─ reads User, Model, Provider, EnterpriseOpenAPI, Quota data
  ├─ writes UsageLog and CostRecord
  └─ emits outbox events consumed by M05 workers

M05 Analytics
  ├─ reads UsageLog, CostRecord, PromptClassificationResult, AnalyticsAggregate
  └─ renders dashboards according to permissions
```

---

### 1.3 Cross-Module Data Ownership

| Object | Owner | Read By | Mutated By |
|---|---|---|---|
| User | M02 | M01, M03, M04, M05 | M00 bootstrap, M02 |
| Role | M02 | M01, M02, M03, M04, M05 | M00 seed, M02 |
| PermissionAction | M00 | All modules | M00 migration/seed |
| LLMProvider | M02 | M04 | M02 |
| Model | M02 | M03, M04, M05 | M02 |
| EnterpriseOpenAPI | M02 | M03, M04 | M02 |
| APIKey | M03 | M02, M03, M04, M05 | M03; M02 extends expiry only |
| QuotaResetPolicy | M02 | BS05, M04 | M02 |
| QuotaBalance | M04 / BS05 | M04, M05 | M04, BS05 |
| UsageLog | M04 | M05, BS02, BS03, BS04 | M04 |
| CostRecord | M04 | M05, BS04 | M04 |
| PromptClassificationResult | BS03 | M05, BS04 | BS03 |
| AnalyticsAggregate | BS04 | M05 | BS04 |

---

### 1.4 Global Interface Contract Standards

#### API Namespaces

| Namespace | Purpose |
|---|---|
| `/api/v1/auth/*` | Platform login and current user APIs |
| `/api/v1/admin/*` | System Administrator management APIs |
| `/api/v1/workbench/*` | Workbench / Developer Portal APIs |
| `/api/v1/analytics/*` | Analytics and reporting APIs |
| `{enterprise_openapi.gateway_url}` | Runtime LLM gateway endpoints |

#### Authentication Schemes

| API Group | Authentication |
|---|---|
| Login challenge/session creation | No prior session; validates email and random password |
| Platform UI APIs | `Authorization: Bearer <platform_session_token>` |
| Admin APIs | Platform session plus required permission action |
| Workbench APIs | Platform session plus own-resource checks |
| Analytics APIs | Platform session plus analytics permissions |
| Gateway Runtime APIs | API Key in `Authorization: Bearer <api_key_secret>` or `x-api-key` |

#### Required Headers

| Header | Usage |
|---|---|
| `Authorization` | Platform bearer token or gateway API Key |
| `x-api-key` | Alternate API Key header for gateway runtime |
| `X-Request-ID` | Optional caller-supplied request correlation ID |
| `Idempotency-Key` | Required for create operations |
| `If-Match` | Required for update/delete operations using optimistic locking |
| `Content-Type: application/json` | Required for JSON body APIs |

#### Platform API Response Envelope

Successful platform UI API response:

```json
{
  "request_id": "req_01HX0000000000000000000000",
  "data": {},
  "pagination": null,
  "error": null
}
```

Error response:

```json
{
  "request_id": "req_01HX0000000000000000000000",
  "data": null,
  "pagination": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {}
  }
}
```

Runtime gateway success responses preserve provider-compatible OpenAI/Anthropic-style response bodies and do not use the platform envelope.

#### Common HTTP Status Codes

| Status | Meaning |
|---:|---|
| 200 | Successful read/update/gateway request |
| 201 | Resource created |
| 204 | Successful delete with no body |
| 400 | Invalid request format |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but forbidden or resource ownership violation |
| 404 | Resource not found or inaccessible |
| 409 | Duplicate resource or idempotency conflict |
| 412 | Optimistic locking version mismatch |
| 422 | Semantically invalid request |
| 429 | Quota exceeded or gateway backpressure |
| 500 | Unexpected server error |
| 502 | Upstream provider error or unusable provider response |
| 503 | Dependency unavailable |
| 504 | Upstream provider timeout |

#### Common Error Codes

```text
VALIDATION_ERROR
AUTH_REQUIRED
INVALID_SESSION
PERMISSION_DENIED
RESOURCE_NOT_FOUND
VERSION_CONFLICT
IDEMPOTENCY_CONFLICT
DUPLICATE_RESOURCE
RESOURCE_IN_USE
USER_DISABLED
INVALID_LOGIN_CHALLENGE
INVALID_RANDOM_PASSWORD
EMAIL_DELIVERY_FAILED
API_KEY_INVALID
API_KEY_DISABLED
API_KEY_EXPIRED
API_KEY_OWNERSHIP_VIOLATION
API_KEY_VALIDITY_EXCEEDED
QUOTA_EXCEEDED
MODEL_NOT_FOUND
PROVIDER_NOT_CONFIGURED
PROVIDER_REQUEST_FAILED
TOKEN_USAGE_MISSING
COST_CALCULATION_FAILED
ANALYTICS_QUERY_INVALID
DEPENDENCY_UNAVAILABLE
```

---

### 1.5 Shared DTO Contracts

#### UserDTO

```json
{
  "user_id": "usr_01HX0000000000000000000000",
  "enterprise_email": "user@example.com",
  "role_id": "rol_01HX0000000000000000000000",
  "role_name": "Normal User",
  "cost_limit_amount": "100.000000",
  "cost_limit_source": "ROLE_DEFAULT",
  "account_status": "ENABLED",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

`account_status`: `ENABLED`, `DISABLED`  
`cost_limit_source`: `ROLE_DEFAULT`, `USER_CUSTOM`

#### RoleDTO

```json
{
  "role_id": "rol_01HX0000000000000000000000",
  "role_name": "Normal User",
  "permissions": ["workbench.api_key.create", "analytics.personal.read"],
  "default_cost_limit_amount": "100.000000",
  "api_key_validity_days": 90,
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

#### ProviderDTO

```json
{
  "provider_id": "prv_01HX0000000000000000000000",
  "provider_name": "Example Provider",
  "api_base_url": "https://api.provider.example",
  "api_key_mask": "sk-...abcd",
  "api_description": "Provider description",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

#### ModelDTO

```json
{
  "model_id": "mdl_01HX0000000000000000000000",
  "provider_id": "prv_01HX0000000000000000000000",
  "provider_name": "Example Provider",
  "model_name": "provider-model-name",
  "input_price_per_million_tokens": "3.000000",
  "output_price_per_million_tokens": "15.000000",
  "currency": "USD",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

#### EnterpriseOpenAPIDTO

```json
{
  "openapi_id": "eoa_01HX0000000000000000000000",
  "api_name": "OpenAI Compatible Gateway",
  "api_type": "OPENAI_COMPATIBLE",
  "gateway_url": "https://gateway.example.com/openai/v1/chat/completions",
  "usage_description": "Use this endpoint with OpenAI-compatible clients.",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

`api_type`: `OPENAI_COMPATIBLE`, `ANTHROPIC_COMPATIBLE`

#### APIKeyDTO

```json
{
  "api_key_id": "key_01HX0000000000000000000000",
  "owner_user_id": "usr_01HX0000000000000000000000",
  "owner_enterprise_email": "user@example.com",
  "key_name": "My IDE Key",
  "api_key_mask": "sk-...abcd",
  "application_date": "2026-05-27T00:00:00Z",
  "expires_at": "2026-08-25T00:00:00Z",
  "status": "ENABLED",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

`status`: `ENABLED`, `DISABLED`, `DELETED`

#### QuotaResetPolicyDTO

```json
{
  "policy_id": "qrp_01HX0000000000000000000000",
  "reset_mode": "MONTHLY",
  "reset_day_of_month": 1,
  "reset_time": "00:00:00",
  "timezone": "UTC",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "version": 1
}
```

`reset_mode`: `MONTHLY`, `NONE`

#### UsageMetricDTO

```json
{
  "input_tokens": 1000,
  "output_tokens": 500,
  "total_tokens": 1500,
  "input_cost": "0.003000",
  "output_cost": "0.007500",
  "total_cost": "0.010500",
  "currency": "USD"
}
```

---

### 1.6 Interface Contract Catalog

#### M00 — Core Platform Foundation

| ID | Interface | Type | Purpose |
|---|---|---|---|
| M00-IC-001 | `CoreBootstrap.initializeSystemAdministrator()` | Internal startup method | Idempotently create initial System Administrator from deployment configuration |

#### M01 — Platform Authentication & Login

| ID | Method / Path | Purpose |
|---|---|---|
| M01-IC-001 | `POST /api/v1/auth/login/challenges` | Create LoginChallenge and send random password |
| M01-IC-002 | `POST /api/v1/auth/login/sessions` | Verify random password and create session |
| M01-IC-003 | `GET /api/v1/auth/me` | Return current User context and permissions |
| M01-IC-004 | `POST /api/v1/auth/logout` | Revoke current session |

#### M02 — Platform Administration Console

| ID | Method / Path | Purpose |
|---|---|---|
| M02-IC-001 | `GET /api/v1/admin/providers` | List providers |
| M02-IC-002 | `POST /api/v1/admin/providers` | Create provider |
| M02-IC-003 | `GET /api/v1/admin/providers/{provider_id}` | Get provider |
| M02-IC-004 | `PATCH /api/v1/admin/providers/{provider_id}` | Update provider |
| M02-IC-005 | `DELETE /api/v1/admin/providers/{provider_id}` | Soft-delete provider |
| M02-IC-006 | `GET /api/v1/admin/models` | List models |
| M02-IC-007 | `POST /api/v1/admin/models` | Create model |
| M02-IC-008 | `GET /api/v1/admin/models/{model_id}` | Get model |
| M02-IC-009 | `PATCH /api/v1/admin/models/{model_id}` | Update model |
| M02-IC-010 | `DELETE /api/v1/admin/models/{model_id}` | Soft-delete model |
| M02-IC-011 | `GET /api/v1/admin/enterprise-openapis` | List Enterprise OpenAPIs |
| M02-IC-012 | `POST /api/v1/admin/enterprise-openapis` | Create Enterprise OpenAPI |
| M02-IC-013 | `GET /api/v1/admin/enterprise-openapis/{openapi_id}` | Get Enterprise OpenAPI |
| M02-IC-014 | `PATCH /api/v1/admin/enterprise-openapis/{openapi_id}` | Update Enterprise OpenAPI |
| M02-IC-015 | `DELETE /api/v1/admin/enterprise-openapis/{openapi_id}` | Soft-delete Enterprise OpenAPI |
| M02-IC-016 | `GET /api/v1/admin/users` | List users |
| M02-IC-017 | `POST /api/v1/admin/users` | Create user |
| M02-IC-018 | `GET /api/v1/admin/users/{user_id}` | Get user |
| M02-IC-019 | `PATCH /api/v1/admin/users/{user_id}` | Update user |
| M02-IC-020 | `DELETE /api/v1/admin/users/{user_id}` | Soft-delete user |
| M02-IC-021 | `GET /api/v1/admin/roles` | List roles |
| M02-IC-022 | `POST /api/v1/admin/roles` | Create role |
| M02-IC-023 | `GET /api/v1/admin/roles/{role_id}` | Get role |
| M02-IC-024 | `PATCH /api/v1/admin/roles/{role_id}` | Update role |
| M02-IC-025 | `DELETE /api/v1/admin/roles/{role_id}` | Soft-delete role |
| M02-IC-026 | `GET /api/v1/admin/api-keys` | List all API Keys, masked only |
| M02-IC-027 | `PATCH /api/v1/admin/api-keys/{api_key_id}/expiry` | Extend API Key expiry only |
| M02-IC-028 | `GET /api/v1/admin/quota-reset-policy` | Get quota reset policy |
| M02-IC-029 | `PUT /api/v1/admin/quota-reset-policy` | Update quota reset policy |

#### M03 — Workbench / Developer Portal

| ID | Method / Path | Purpose |
|---|---|---|
| M03-IC-001 | `POST /api/v1/workbench/api-keys` | Create own API Key and show secret once |
| M03-IC-002 | `GET /api/v1/workbench/api-keys` | List own API Keys |
| M03-IC-003 | `PATCH /api/v1/workbench/api-keys/{api_key_id}/status` | Enable/disable own API Key |
| M03-IC-004 | `DELETE /api/v1/workbench/api-keys/{api_key_id}` | Soft-delete own API Key |
| M03-IC-005 | `GET /api/v1/workbench/models` | View model catalog |
| M03-IC-006 | `GET /api/v1/workbench/enterprise-openapis` | View Enterprise OpenAPI catalog |

#### M04 — API Service Layer

| ID | Interface | Purpose |
|---|---|---|
| M04-IC-001 | Configured OpenAI-compatible Gateway URL, `POST` | Runtime OpenAI-compatible request |
| M04-IC-002 | Configured Anthropic-compatible Gateway URL, `POST` | Runtime Anthropic-compatible request |
| M04-IC-003 | `GatewayAuthService.validateApiKey(api_key_secret)` | Internal API Key validation |
| M04-IC-004 | `QuotaService.precheck(user_id, model_id)` | Internal quota precheck |
| M04-IC-005 | `QuotaService.deductActualCost(...)` | Internal atomic cost deduction |
| M04-IC-006 | `UsageLogService.recordGatewayRequest(...)` | Internal UsageLog persistence |

#### M05 — Data Analytics & Reporting

| ID | Method / Path | Purpose |
|---|---|---|
| M05-IC-001 | `GET /api/v1/analytics/personal-consumption` | Personal usage and quota ratio |
| M05-IC-002 | `GET /api/v1/analytics/consumption-ranking` | Masked Top 30% ranking plus current user |
| M05-IC-003 | `GET /api/v1/analytics/prompt-categories` | Prompt category statistics |
| M05-IC-004 | `GET /api/v1/analytics/consumption-details` | Detail drilldown for System Administrator and Team Manager |
| M05-IC-005 | `GET /api/v1/analytics/consumption-summary` | All-user summary for System Administrator and Team Manager |

---

### 1.7 Permission Action Namespace

#### Platform Administration Permissions

```text
platform.provider.create
platform.provider.read
platform.provider.update
platform.provider.delete
platform.model.create
platform.model.read
platform.model.update
platform.model.delete
platform.openapi.create
platform.openapi.read
platform.openapi.update
platform.openapi.delete
platform.user.create
platform.user.read
platform.user.update
platform.user.delete
platform.role.create
platform.role.read
platform.role.update
platform.role.delete
platform.api_key.read_all
platform.api_key.extend_expiry
platform.quota_policy.read
platform.quota_policy.update
```

#### Workbench Permissions

```text
workbench.api_key.create
workbench.api_key.read_own
workbench.api_key.update_status_own
workbench.api_key.delete_own
workbench.model.read
workbench.openapi.read
```

#### Analytics Permissions

```text
analytics.personal.read
analytics.ranking.read
analytics.prompt_category.read
analytics.detail.read
analytics.summary.read
```

---

## 2. Module Designs

### 2.1 M00 — Core Platform Foundation

#### 2.1.1 Scope

M00 provides shared platform primitives: initial administrator bootstrap, permission namespace seeding, common error/response conventions, idempotency support, optimistic locking standards, and shared logging schema.

#### 2.1.2 Primary Functions

1. Initialize first System Administrator from deployment configuration.
2. Seed canonical permission action namespace.
3. Provide common platform API response and error envelope.
4. Define ID, timestamp, pagination, versioning, and optimistic locking standards.
5. Store system configuration such as allowed enterprise domains, default currency, session duration, and random password expiry.
6. Provide common idempotency record handling.
7. Define shared logging schema and sensitive-data masking rules.

#### 2.1.3 Interface Design

**M00-IC-001 — `CoreBootstrap.initializeSystemAdministrator()`**

Processing:

```text
Read INITIAL_ADMIN_ENTERPRISE_EMAIL
  → validate email format and allowed domain
  → open transaction
  → ensure built-in System Administrator role exists
  → find User by enterprise_email
  → insert User if missing
  → commit
  → log result
```

Idempotency is guaranteed by unique `users.enterprise_email`.

#### 2.1.4 Data Design

##### SystemConfig

| Attribute | Type | Constraints |
|---|---|---|
| config_key | varchar(128) | PK |
| config_value | text/json | required unless secret reference |
| config_type | enum | `STRING`, `NUMBER`, `BOOLEAN`, `JSON`, `SECRET_REF` |
| is_secret | boolean | required |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

##### PermissionAction

| Attribute | Type | Constraints |
|---|---|---|
| permission_action | varchar(128) | PK |
| module_id | varchar(16) | required |
| description | varchar(512) | required |
| is_system_defined | boolean | required |
| created_at | timestamp | required |

##### IdempotencyRecord

| Attribute | Type | Constraints |
|---|---|---|
| idempotency_key | varchar(128) | composite key with scope/user |
| scope | varchar(128) | required |
| request_hash | varchar(128) | required |
| response_body | jsonb | nullable |
| status_code | integer | nullable |
| expires_at | timestamp | required |
| created_at | timestamp | required |

#### 2.1.5 Permission Design

| Actor | Bootstrap Admin | Read System Config | Manage Permission Namespace |
|---|---:|---:|---:|
| Platform Runtime | Execute | Read | Seed only |
| System Administrator | No direct execution | Indirect only | No direct editing |
| Team Manager | No | No | No |
| Normal User | No | No | No |

#### 2.1.6 Logging Design

Events:

```text
core.bootstrap.start
core.bootstrap.admin_exists
core.bootstrap.admin_created
core.bootstrap.invalid_config
core.bootstrap.failed
core.permission.seeded
core.idempotency.conflict
```

Never log raw emails, random passwords, provider API keys, user API Key Secrets, session tokens, or authorization headers.

---

### 2.2 M01 — Platform Authentication & Login

#### 2.2.1 Scope

M01 supports enterprise email login through one-time random password delivery. It validates enterprise email domain, login challenge state, random password, User existence, and User account status before issuing a platform session.

#### 2.2.2 Primary Functions

1. Display enterprise email login page.
2. Validate enterprise email format and allowed domain suffix.
3. Generate LoginChallenge and one-time random password.
4. Send random password to enterprise email.
5. Verify random password.
6. Reject disabled Users.
7. Create authenticated platform session.
8. Return current user context and permissions.
9. Logout/revoke session.

#### 2.2.3 UI/UX Interaction Logic

##### Login Email Screen

| Field | Type | Required | Placeholder | Validation |
|---|---|---:|---|---|
| enterprise_email | email input | Yes | `name@company.com` | Email format and allowed domain |
| send_code_button | button | Yes | `Send random password` | Enabled only when email format is valid |

Validation messages:

| Rule | Message |
|---|---|
| Empty email | `Enterprise email is required.` |
| Invalid format | `Enter a valid enterprise email address.` |
| Disallowed domain | `Use your enterprise email address.` |

API binding: M01-IC-001.

##### Random Password Verification Screen

| Field | Type | Required | Placeholder | Validation |
|---|---|---:|---|---|
| random_password | password/text | Yes | `Enter random password` | Required; expected length/format |
| enterprise_email_display | read-only text | Yes | masked email | Not editable unless user goes back |
| submit_button | button | Yes | `Log in` | Enabled when password present |

API binding: M01-IC-002.

Success routing:

```text
System Administrator → Platform Administration landing page
Team Manager        → Workbench landing page
Normal User         → Workbench landing page
```

Exception handling:

| Error | UI Handling |
|---|---|
| INVALID_LOGIN_CHALLENGE | Show expired challenge message and offer resend |
| INVALID_RANDOM_PASSWORD | Inline password error |
| USER_DISABLED | Page-level disabled account message |
| EMAIL_DELIVERY_FAILED | Toast retry message |
| Network failure | Toast with retry action |

##### Session Menu

Loads M01-IC-003 on application boot or route refresh. Logout calls M01-IC-004.

#### 2.2.4 Interface Design

##### M01-IC-001 — Create Login Challenge

`POST /api/v1/auth/login/challenges`

Request:

```json
{ "enterprise_email": "user@example.com" }
```

Processing:

```text
Normalize email
  → validate domain
  → load User
  → reject disabled User
  → generate random password
  → store random_password_hash with expiry
  → emit auth.email.delivery.requested event
  → return challenge metadata
```

Response:

```json
{
  "challenge_id": "lch_...",
  "enterprise_email_mask": "u***@example.com",
  "expires_at": "2026-05-27T00:05:00Z"
}
```

##### M01-IC-002 — Create Login Session

`POST /api/v1/auth/login/sessions`

Request:

```json
{
  "challenge_id": "lch_...",
  "enterprise_email": "user@example.com",
  "random_password": "123456"
}
```

Processing:

```text
Lock LoginChallenge
  → verify status, expiry, email, password hash
  → increment failed attempt count on mismatch
  → load User and Role
  → reject disabled User
  → mark challenge CONSUMED
  → create session
  → return token, UserDTO, permissions
```

##### M01-IC-003 — Get Current User

`GET /api/v1/auth/me`

Returns current `UserDTO` and permission actions. Rejects disabled users.

##### M01-IC-004 — Logout

`POST /api/v1/auth/logout`

Revokes current session. Safe to retry.

#### 2.2.5 Data Design

##### LoginChallenge

| Attribute | Type | Constraints |
|---|---|---|
| challenge_id | UUID/varchar | PK |
| enterprise_email | varchar(320) | indexed |
| random_password_hash | varchar(255) | required |
| status | enum | `PENDING`, `CONSUMED`, `EXPIRED`, `LOCKED` |
| attempt_count | integer | required |
| expires_at | timestamp | required |
| consumed_at | timestamp | nullable |
| created_at | timestamp | required |
| request_ip_hash | varchar(128) | nullable |
| user_agent_hash | varchar(128) | nullable |

##### PlatformSession

| Attribute | Type | Constraints |
|---|---|---|
| session_id | UUID/varchar | PK |
| user_id | UUID/varchar | FK User |
| session_token_hash | varchar(255) | required for stateful sessions |
| issued_at | timestamp | required |
| expires_at | timestamp | required |
| revoked_at | timestamp | nullable |
| last_seen_at | timestamp | nullable |

#### 2.2.6 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Request login challenge | Yes | Yes | Yes |
| Verify login challenge | Yes | Yes | Yes |
| Read own session context | Yes | Yes | Yes |
| Logout own session | Yes | Yes | Yes |
| Login while disabled | No | No | No |

Random password scope is one LoginChallenge. Platform session scope is platform UI APIs only. API Keys are not accepted for platform UI APIs.

#### 2.2.7 Logging Design

Events:

```text
auth.challenge.requested
auth.challenge.rejected_invalid_domain
auth.challenge.email_sent
auth.challenge.email_failed
auth.login.success
auth.login.invalid_password
auth.login.challenge_expired
auth.login.user_disabled
auth.session.revoked
```

Never log random password, random password hash, session token, authorization header, or raw enterprise email in operational logs.

---

### 2.3 M02 — Platform Administration Console

#### 2.3.1 Scope

M02 provides System Administrator management of providers, models, Enterprise OpenAPIs, users, roles, API Key validity extension, and quota reset policy. M02 does not handle runtime gateway requests.

#### 2.3.2 Primary Functions

1. LLM Provider CRUD.
2. Model CRUD and pricing management.
3. Enterprise OpenAPI CRUD.
4. User CRUD, account status, role assignment, and cost limit source/override.
5. Role CRUD, permissions, default cost limit, and API Key validity duration.
6. View all API Keys, masked only.
7. Extend API Key validity only.
8. Configure quota reset policy.
9. Emit audit logs and `config.changed` events after runtime-affecting commits.

#### 2.3.3 UI/UX Interaction Logic

Shared admin layout:

```text
Left navigation:
  Provider Management
  Model Management
  Enterprise OpenAPI Management
  User Management
  Role Management
  API Key List
  Quota Reset Policy
```

Global states:

| State | Rendering |
|---|---|
| Loading | Skeleton rows/cards |
| Empty | Resource-specific empty message and create CTA |
| Permission denied | 403 full-page state |
| Network failure | Retry banner |
| Save success | Toast notification |
| Validation failure | Inline errors |
| Version conflict | Reload prompt preserving unsaved input where possible |

##### Provider Management

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| provider_name | text | Yes | 1-128 chars, unique |
| api_base_url | URL | Yes | HTTPS URL |
| api_key | password/secret | Required on create, optional on update | Non-empty on create |
| api_description | textarea | No | Max length bounded |

API bindings: M02-IC-001 to M02-IC-005.

##### Model Management

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| provider_id | select | Yes | Existing active provider |
| model_name | text | Yes | Unique within provider |
| input_price_per_million_tokens | decimal | Yes | Non-negative |
| output_price_per_million_tokens | decimal | Yes | Non-negative |
| currency | text/select | Yes | Configured currency code |

API bindings: M02-IC-006 to M02-IC-010.

##### Enterprise OpenAPI Management

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| api_name | text | Yes | Unique |
| api_type | select | Yes | `OPENAI_COMPATIBLE`, `ANTHROPIC_COMPATIBLE` |
| gateway_url | URL | Yes | HTTPS Gateway URL |
| usage_description | textarea/markdown | No | Max length bounded |

API bindings: M02-IC-011 to M02-IC-015.

##### User Management

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| enterprise_email | email | Yes on create | Valid, allowed domain, unique |
| role_id | select | Yes | Role exists |
| cost_limit_source | radio/select | Yes | `ROLE_DEFAULT` or `USER_CUSTOM` |
| cost_limit_amount | decimal | Conditional | Required if custom; non-negative |
| account_status | switch/select | Yes | `ENABLED` or `DISABLED` |

Disabling a User shows warning: `This user will no longer be able to log in or use existing API Keys.`

API bindings: M02-IC-016 to M02-IC-020.

##### Role Management

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| role_name | text | Yes | Unique |
| permissions | checkbox group | Yes | Valid PermissionAction values |
| default_cost_limit_amount | decimal | Yes | Non-negative |
| api_key_validity_days | integer | Yes | Positive integer |

API bindings: M02-IC-021 to M02-IC-025.

##### API Key List Management

Display columns:

```text
owner enterprise email
key name
key mask
application date
expiry date
status
action: Extend expiry only
```

Fields for extension:

| Field | Type | Required | Validation |
|---|---|---:|---|
| new_expires_at | datetime | Yes | Later than current expiry |
| reason | textarea | Yes | Length bounded |

API bindings: M02-IC-026 and M02-IC-027.

Admin UI must not expose raw key reveal, key regeneration, key disable, or key deletion.

##### Quota Reset Policy

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| reset_mode | select | Yes | `MONTHLY` or `NONE` |
| reset_day_of_month | integer/select | Conditional | 1-28 when monthly |
| reset_time | time | Conditional | Required when monthly |
| timezone | select | Conditional | Valid timezone |

API bindings: M02-IC-028 and M02-IC-029.

#### 2.3.4 Interface Processing Pattern

Admin mutation flow:

```text
Validate platform session
  → check required permission action
  → validate request body
  → check Idempotency-Key for create or If-Match for update/delete
  → open transaction
  → apply domain mutation
  → increment version
  → insert config.changed outbox event if runtime-affecting
  → commit
  → write audit log
  → return DTO
```

#### 2.3.5 Data Design

##### LLMProvider

| Attribute | Type | Constraints |
|---|---|---|
| provider_id | UUID/varchar | PK |
| provider_name | varchar(128) | unique, required |
| api_base_url | varchar(2048) | required |
| api_key_ciphertext | text | required |
| api_key_mask | varchar(64) | required |
| api_description | text | nullable |
| status | enum | `ACTIVE`, `DELETED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

##### Model

| Attribute | Type | Constraints |
|---|---|---|
| model_id | UUID/varchar | PK |
| provider_id | UUID/varchar | FK Provider |
| model_name | varchar(256) | required |
| input_price_per_million_tokens | decimal(20,6) | non-negative |
| output_price_per_million_tokens | decimal(20,6) | non-negative |
| currency | char(3) | required |
| status | enum | `ACTIVE`, `DELETED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

Unique: `(provider_id, model_name)`.

##### EnterpriseOpenAPI

| Attribute | Type | Constraints |
|---|---|---|
| openapi_id | UUID/varchar | PK |
| api_name | varchar(128) | unique, required |
| api_type | enum | `OPENAI_COMPATIBLE`, `ANTHROPIC_COMPATIBLE` |
| gateway_url | varchar(2048) | unique, required |
| usage_description | text | nullable |
| status | enum | `ACTIVE`, `DELETED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

##### User

| Attribute | Type | Constraints |
|---|---|---|
| user_id | UUID/varchar | PK |
| enterprise_email | varchar(320) | unique, required |
| role_id | UUID/varchar | FK Role |
| cost_limit_source | enum | `ROLE_DEFAULT`, `USER_CUSTOM` |
| custom_cost_limit_amount | decimal(20,6) | nullable, required if custom |
| account_status | enum | `ENABLED`, `DISABLED` |
| deleted_at | timestamp | nullable |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

Effective cost limit:

```text
if cost_limit_source = USER_CUSTOM:
  effective_limit = custom_cost_limit_amount
else:
  effective_limit = role.default_cost_limit_amount
```

##### Role

| Attribute | Type | Constraints |
|---|---|---|
| role_id | UUID/varchar | PK |
| role_name | varchar(128) | unique, required |
| default_cost_limit_amount | decimal(20,6) | non-negative |
| api_key_validity_days | integer | positive |
| status | enum | `ACTIVE`, `DELETED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

##### RolePermission

Primary key: `(role_id, permission_action)`.

| Attribute | Type | Constraints |
|---|---|---|
| role_id | UUID/varchar | FK Role |
| permission_action | varchar(128) | FK PermissionAction |
| created_at | timestamp | required |

##### QuotaResetPolicy

| Attribute | Type | Constraints |
|---|---|---|
| policy_id | UUID/varchar | PK |
| reset_mode | enum | `MONTHLY`, `NONE` |
| reset_day_of_month | integer | nullable |
| reset_time | time | nullable |
| timezone | varchar(64) | nullable |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

#### 2.3.6 Permission Design

| M02 Action | Required Permission | System Administrator | Team Manager | Normal User |
|---|---|---:|---:|---:|
| Provider CRUD | `platform.provider.*` | Yes | No | No |
| Model CRUD | `platform.model.*` | Yes | No | No |
| Enterprise OpenAPI CRUD | `platform.openapi.*` | Yes | No | No |
| User CRUD | `platform.user.*` | Yes | No | No |
| Role CRUD | `platform.role.*` | Yes | No | No |
| View all API Keys | `platform.api_key.read_all` | Yes | No | No |
| Extend API Key expiry | `platform.api_key.extend_expiry` | Yes | No | No |
| Quota policy read/update | `platform.quota_policy.*` | Yes | No | No |

Safety invariants:

```text
The built-in System Administrator role cannot be deleted while any System Administrator user exists.
The last enabled System Administrator user cannot be disabled or deleted.
The last role granting platform.user.update and platform.role.update cannot be deleted if doing so would block future administration.
```

#### 2.3.7 Logging Design

Events:

```text
admin.provider.created / updated / deleted
admin.model.created / updated / deleted
admin.openapi.created / updated / deleted
admin.user.created / updated / disabled / deleted
admin.role.created / updated / deleted
admin.api_key.expiry_extended
admin.quota_policy.updated
admin.permission.denied
```

Never log provider API key plaintext, user API Key Secret, session token, or authorization header.

---

### 2.4 M03 — Workbench / Developer Portal

#### 2.4.1 Scope

M03 allows System Administrators, Team Managers, and Normal Users to create and manage their own API Keys and to view model and Enterprise OpenAPI catalogs.

#### 2.4.2 Primary Functions

1. Create API Key for current account.
2. Show full API Key Secret once.
3. List current user's API Keys with masked values.
4. Enable/disable own API Keys.
5. Soft-delete own API Keys.
6. View model catalog and pricing.
7. View Enterprise OpenAPI catalog and usage descriptions.
8. Enforce Role API Key validity limit.

#### 2.4.3 UI/UX Interaction Logic

##### Workbench Home

Cards:

| Card | Content | CTA |
|---|---|---|
| API Keys | Current user's key count by status | Manage API Keys |
| Model Catalog | Available configured models | View Models |
| Enterprise OpenAPIs | Available gateway endpoints | View APIs |
| Usage Reminder | Link to personal analytics | View Consumption |

##### Apply for API Key

Fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| key_name | text | Yes | 1-128 chars after trim |
| expires_at | datetime/date | Yes | Future date; not beyond Role `api_key_validity_days` |

Success modal:

```text
API Key created
Copy this key now. It will only be shown once.
<api_key_secret>
Buttons: Copy, I have saved it
```

Security behavior:

1. Raw secret is only shown in the creation success modal.
2. Closing the modal requires confirmation if the secret was not copied.
3. Later UI displays only `api_key_mask`.
4. Page refresh never re-displays the secret.

API binding: M03-IC-001.

##### My API Keys

Columns:

```text
key_name
api_key_mask
application_date
expires_at
status
actions
```

State rules:

```text
ENABLED  → show Disable and Delete
DISABLED → show Enable and Delete
DELETED  → hidden from default list or read-only under deleted filter
Expired  → show Expired badge; cannot be enabled unless admin extends expiry
```

API bindings: M03-IC-002, M03-IC-003, M03-IC-004.

##### Model Catalog

Filters: provider, search, page size.  
Columns: Provider name, Model name, input price/million tokens, output price/million tokens, currency.  
API binding: M03-IC-005.

##### Enterprise OpenAPI Catalog

Filters: API type, search.  
Columns: API name, API type, Gateway URL with copy button, usage description.  
API binding: M03-IC-006.

#### 2.4.4 Interface Design

##### M03-IC-001 — Create Own API Key

`POST /api/v1/workbench/api-keys`

Request:

```json
{
  "key_name": "VS Code Key",
  "expires_at": "2026-08-25T00:00:00Z"
}
```

Processing:

```text
Validate session and permission
  → load User and Role
  → validate expiry does not exceed Role validity days
  → generate cryptographically strong API Key Secret
  → store hash, prefix, and mask
  → insert APIKey with status ENABLED
  → return APIKeyDTO and raw secret once
```

Initial success response:

```json
{
  "api_key": { "api_key_id": "key_...", "api_key_mask": "sk-...abcd", "status": "ENABLED" },
  "api_key_secret": "sk-full-secret-shown-once",
  "api_key_secret_available": true
}
```

Idempotency behavior:

```text
First successful create returns secret.
Retry with same Idempotency-Key and same body within one-time secret TTL may return same secret.
Retry after TTL returns APIKeyDTO only with api_key_secret_available=false.
```

Post-TTL response:

```json
{
  "api_key": { "api_key_id": "key_...", "api_key_mask": "sk-...abcd", "status": "ENABLED" },
  "api_key_secret": null,
  "api_key_secret_available": false,
  "message": "The API Key was already created. The secret cannot be displayed again."
}
```

##### M03-IC-002 — List Own API Keys

Returns masked APIKeyDTO records where `owner_user_id = current_session.user_id`.

##### M03-IC-003 — Enable/Disable Own API Key

Requires `If-Match`. Verifies ownership and status transition. Deleted keys cannot be re-enabled.

##### M03-IC-004 — Delete Own API Key

Soft-deletes by setting `status = DELETED`. Future M04 gateway requests with this key are rejected.

##### M03-IC-005 / M03-IC-006 — Catalog Views

Read-only views of active Models and active EnterpriseOpenAPIs.

#### 2.4.5 Data Design

##### APIKey

| Attribute | Type | Constraints |
|---|---|---|
| api_key_id | UUID/varchar | PK |
| owner_user_id | UUID/varchar | FK User |
| key_name | varchar(128) | required |
| api_key_prefix | varchar(16) | indexed |
| api_key_secret_hash | varchar(255) | unique, required |
| api_key_mask | varchar(64) | required |
| application_date | timestamp | required |
| expires_at | timestamp | required |
| status | enum | `ENABLED`, `DISABLED`, `DELETED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| deleted_at | timestamp | nullable |
| version | integer | required |

Indexes:

```text
(owner_user_id, status)
(api_key_prefix)
(api_key_secret_hash)
(expires_at)
```

##### APIKeyCreationOneTimeSecret Cache

Short-lived encrypted storage used only for idempotent retry during a narrow window.

| Attribute | Type | Constraints |
|---|---|---|
| idempotency_key | varchar(128) | PK |
| api_key_id | UUID/varchar | required |
| encrypted_one_time_secret | text | strict TTL |
| expires_at | timestamp | required |
| created_at | timestamp | required |

After TTL, raw API Key Secret is unrecoverable.

#### 2.4.6 Permission Design

| M03 Action | Required Permission | System Administrator | Team Manager | Normal User |
|---|---|---:|---:|---:|
| Create own API Key | `workbench.api_key.create` | Yes | Yes | Yes |
| List own API Keys | `workbench.api_key.read_own` | Yes | Yes | Yes |
| Enable/disable own API Key | `workbench.api_key.update_status_own` | Yes | Yes | Yes |
| Delete own API Key | `workbench.api_key.delete_own` | Yes | Yes | Yes |
| View model catalog | `workbench.model.read` | Yes | Yes | Yes |
| View Enterprise OpenAPI catalog | `workbench.openapi.read` | Yes | Yes | Yes |

Ownership rule:

```text
api_key.owner_user_id must equal current_session.user_id for every own-key mutation.
```

#### 2.4.7 Logging Design

Events:

```text
workbench.api_key.created
workbench.api_key.secret_displayed
workbench.api_key.listed
workbench.api_key.enabled
workbench.api_key.disabled
workbench.api_key.deleted
workbench.api_key.ownership_violation
workbench.catalog.models_viewed
workbench.catalog.openapi_viewed
```

Never log raw API Key Secret, API Key hash, session token, or authorization header.

---

### 2.5 M04 — API Service Layer / LLM Gateway Runtime API

#### 2.5.1 Scope

M04 exposes runtime gateway endpoints to IDEs, plugins, CLI tools, and internal clients. It validates API Keys, validates User status, checks quota, resolves model/provider configuration, forwards requests, calculates cost from actual token usage, deducts quota atomically, and records detailed Usage Logs.

#### 2.5.2 Primary Functions

1. Expose OpenAI-compatible and Anthropic-compatible Gateway URLs.
2. Authenticate using API Key Secret.
3. Validate API Key status and expiry.
4. Validate owning User account status.
5. Resolve EnterpriseOpenAPI by incoming route.
6. Resolve Model and Provider.
7. Precheck quota.
8. Create UsageLog before provider call with `PROVIDER_IN_FLIGHT` status.
9. Forward request to provider.
10. Extract actual token usage from provider response.
11. Calculate cost using Model pricing.
12. Update UsageLog, insert CostRecord, deduct QuotaBalance, and insert outbox event in one transaction.
13. Return provider-compatible response.

#### 2.5.3 Runtime Request Processing

```text
Receive request
  → generate/accept trace_id
  → extract API Key from Authorization or x-api-key
  → validate API Key hash, status, expiry
  → load owning User; reject if not ENABLED
  → match request path to active EnterpriseOpenAPI.gateway_url
  → select compatibility handler by api_type
  → parse provider-compatible request and require model field
  → resolve active Model by model_name
  → resolve active Provider by model.provider_id
  → quota precheck
  → create UsageLog with PROVIDER_IN_FLIGHT
  → call provider
  → extract provider token usage
  → calculate input/output/total cost
  → transaction:
       update UsageLog
       insert CostRecord
       update QuotaBalance atomically
       insert TransactionalOutbox event
  → return provider-compatible response
```

Route resolution:

```text
Incoming request path → active EnterpriseOpenAPI.gateway_url path
  → EnterpriseOpenAPI.api_type
  → M04-IC-001 or M04-IC-002 handler
  → request body model field
  → Model.provider_id
  → Provider.api_base_url + provider credential
```

#### 2.5.4 Error Behavior

| Error | Status | Business UsageLog | Operational Log |
|---|---:|---:|---:|
| Missing API Key | 401 | No | Yes |
| Invalid API Key | 401 | No | Yes |
| Disabled API Key | 403 | Yes if key identified | Yes |
| Expired API Key | 403 | Yes if key identified | Yes |
| Disabled User | 403 | Yes | Yes |
| Quota exceeded | 429 | Yes | Yes |
| Model not found | 404/400 | Yes if key/user valid | Yes |
| Provider not configured | 502 | Yes if key/user valid | Yes |
| Provider failure | 502/503/504 | Yes | Yes |
| Token usage missing | 502 | Yes, status `COST_FAILED` | Yes |
| Cost deduction failure | 500 | Yes if possible | Error/Fatal |

If provider response lacks usable token usage:

```text
UsageLog.request_status = COST_FAILED
CostRecord.cost_calculation_status = FAILED_MISSING_PROVIDER_USAGE
QuotaBalance is not deducted
Gateway returns TOKEN_USAGE_MISSING as failure
```

#### 2.5.5 Interface Design

##### M04-IC-001 — OpenAI-Compatible Gateway Request

`POST {configured OPENAI_COMPATIBLE gateway_url}`

Request body is OpenAI-compatible and must include `model`. Other fields are passed through with minimal normalization for logging, routing, and usage extraction.

##### M04-IC-002 — Anthropic-Compatible Gateway Request

`POST {configured ANTHROPIC_COMPATIBLE gateway_url}`

Request body is Anthropic-compatible and must include `model`.

##### M04-IC-003 — Internal API Key Validation

```text
Validate format
  → derive lookup prefix
  → hash submitted secret
  → find matching APIKey
  → verify status ENABLED
  → verify expires_at > now
  → return api_key_id and owner_user_id
```

##### M04-IC-004 — Quota Precheck

```text
Load User effective cost limit
  → resolve current quota period
  → load/create QuotaBalance
  → if consumed_amount >= cost_limit_amount reject QUOTA_EXCEEDED
  → else allow provider call
```

##### M04-IC-005 — Actual Cost Deduction

```text
Begin transaction
  → lock QuotaBalance row
  → insert CostRecord with unique usage_log_id
  → consumed_amount += total_cost
  → remaining_amount -= total_cost
  → if remaining_amount <= 0 set quota_status = EXCEEDED
  → commit
```

##### M04-IC-006 — Usage Log Write

Persists gateway request details and inserts outbox event for downstream processing.

#### 2.5.6 Data Design

##### QuotaPeriod

| Attribute | Type | Constraints |
|---|---|---|
| quota_period_id | UUID/varchar | PK |
| period_type | enum | `MONTHLY`, `NONE` or configured period |
| period_start_at | timestamp | required |
| period_end_at | timestamp | nullable |
| reset_policy_id | UUID/varchar | FK |
| created_at | timestamp | required |

##### QuotaBalance

| Attribute | Type | Constraints |
|---|---|---|
| quota_balance_id | UUID/varchar | PK |
| user_id | UUID/varchar | FK User |
| quota_period_id | UUID/varchar | FK QuotaPeriod |
| cost_limit_amount | decimal(20,6) | required |
| consumed_amount | decimal(20,6) | required |
| remaining_amount | decimal(20,6) | required |
| currency | char(3) | required |
| quota_status | enum | `AVAILABLE`, `EXCEEDED` |
| created_at | timestamp | required |
| updated_at | timestamp | required |
| version | integer | required |

Unique: `(user_id, quota_period_id)`.

##### UsageLog

| Attribute | Type | Constraints |
|---|---|---|
| usage_log_id | UUID/varchar | PK |
| gateway_request_id | varchar(128) | unique |
| trace_id | varchar(128) | indexed |
| api_key_id | UUID/varchar | FK APIKey |
| api_key_mask | varchar(64) | required |
| user_id | UUID/varchar | FK User |
| enterprise_openapi_id | UUID/varchar | nullable |
| provider_id | UUID/varchar | FK Provider |
| model_id | UUID/varchar | FK Model |
| model_name_snapshot | varchar(256) | required |
| request_started_at | timestamp | required |
| provider_completed_at | timestamp | nullable |
| request_status | enum | `PROVIDER_IN_FLIGHT`, `SUCCESS`, `FAILED`, `REJECTED`, `COST_FAILED` |
| prompt_content | text/jsonb | required by FRD |
| response_content | text/jsonb | nullable |
| input_tokens | bigint | nullable |
| output_tokens | bigint | nullable |
| total_tokens | bigint | nullable |
| latency_ms | integer | nullable |
| error_code | varchar(128) | nullable |
| created_at | timestamp | required |

##### CostRecord

| Attribute | Type | Constraints |
|---|---|---|
| cost_record_id | UUID/varchar | PK |
| usage_log_id | UUID/varchar | unique FK UsageLog |
| user_id | UUID/varchar | FK User |
| api_key_id | UUID/varchar | FK APIKey |
| model_id | UUID/varchar | FK Model |
| quota_period_id | UUID/varchar | FK QuotaPeriod |
| input_tokens | bigint | required |
| output_tokens | bigint | required |
| input_unit_price_per_million | decimal(20,6) | required |
| output_unit_price_per_million | decimal(20,6) | required |
| input_cost | decimal(20,6) | required |
| output_cost | decimal(20,6) | required |
| total_cost | decimal(20,6) | required |
| currency | char(3) | required |
| cost_calculation_status | enum | `CALCULATED`, `FAILED_MISSING_PROVIDER_USAGE`, `FAILED_MODEL_PRICE_NOT_FOUND` |
| created_at | timestamp | required |

Cost formula:

```text
input_cost  = input_tokens  / 1,000,000 × input_price_per_million_tokens
output_cost = output_tokens / 1,000,000 × output_price_per_million_tokens
total_cost  = input_cost + output_cost
```

#### 2.5.7 Storage and Partitioning

| Data | Storage | Strategy |
|---|---|---|
| UsageLog | Relational DB, optionally object storage for large payloads | Time partition by month/day |
| CostRecord | Relational DB | Partition aligned with UsageLog |
| QuotaBalance | Relational DB | Indexed by user and period |
| API Key validation cache | Redis/local cache | Short TTL plus invalidation |
| Provider/model/OpenAPI config cache | Redis/local cache | Short TTL plus invalidation |

#### 2.5.8 Permission Design

Runtime authorization checks:

| Check | Required Result | Failure Code |
|---|---|---|
| API Key exists | Yes | API_KEY_INVALID |
| API Key status | ENABLED | API_KEY_DISABLED |
| API Key expiry | Future timestamp | API_KEY_EXPIRED |
| Owning User status | ENABLED | USER_DISABLED |
| Model configured | Active Model found | MODEL_NOT_FOUND |
| Provider configured | Active Provider found | PROVIDER_NOT_CONFIGURED |
| Quota state | Not exceeded | QUOTA_EXCEEDED |

M04 does not accept platform session tokens for runtime inference requests.

#### 2.5.9 Logging Design

Operational events:

```text
gateway.request.received
gateway.auth.api_key_invalid
gateway.auth.api_key_disabled
gateway.auth.api_key_expired
gateway.auth.user_disabled
gateway.quota.precheck_failed
gateway.provider.request_started
gateway.provider.request_failed
gateway.cost.calculated
gateway.cost.calculation_failed
gateway.quota.deducted
gateway.usage_log.persisted
gateway.request.completed
gateway.persistence.failed
```

Operational logs must not contain raw API Key Secrets, provider API keys, authorization headers, full prompts, full responses, or session tokens. Prompt and response are stored only in protected UsageLog storage because the FRD requires detailed request logging.

---

### 2.6 M05 — Data Analytics & Reporting

#### 2.6.1 Scope

M05 provides analytics dashboards: personal consumption, masked consumption ranking, prompt category statistics, consumption detail, and consumption summary.

#### 2.6.2 Primary Functions

1. Personal consumption statistics by day/week/month/current accumulated period and model.
2. Current period consumed amount and quota usage ratio.
3. Consumption ranking by user with enterprise email hidden.
4. Top 30% users plus current logged-in user in ranking.
5. Prompt category statistics and trend analysis.
6. Consumption detail drilldown for System Administrator and Team Manager.
7. All-user consumption summary for System Administrator and Team Manager.

#### 2.6.3 Shared Analytics Filters

| Field | Type | Required | Values |
|---|---|---:|---|
| period_type | select | Yes | `DAY`, `WEEK`, `MONTH`, `CURRENT_ACCUMULATED` |
| period_start | date | Conditional | Date |
| period_end | date | Conditional | Date |
| model_id | select | No | Active or historical model reference |
| metric | select | Contextual | `COST`, `TOTAL_TOKENS`, `INPUT_TOKENS`, `OUTPUT_TOKENS` |
| granularity | select | Contextual | `DAY`, `WEEK`, `MONTH` |

`CURRENT_ACCUMULATED` means from the start of the current active quota/accounting period to now. If reset mode is `NONE`, it means from the user's first recorded usage or system usage start to now.

#### 2.6.4 UI/UX Interaction Logic

##### Personal Consumption

API: M05-IC-001.

Displays:

```text
Summary cards:
  total input tokens
  total output tokens
  total tokens
  total cost
  current period consumed
  quota usage ratio
Trend chart:
  selected metric over time
Model breakdown table:
  model, tokens, cost
```

##### Consumption Ranking

API: M05-IC-002.

Ranking rule:

```text
ranked_user_count = users with usage under selected filter
top_count = ceil(ranked_user_count × 0.30)
minimum top_count = 1 when ranked_user_count > 0
return all users with rank <= top_count
include current user if not already included
de-duplicate current user if already in Top 30%
```

Display:

```text
Other users: Anonymous User 1, Anonymous User 2, ...
Current user: You
```

##### Prompt Category Statistics

API: M05-IC-003.

Displays category rankings, token/cost totals, and trends. Recent requests may appear after background classification completes.

##### Consumption Detail

API: M05-IC-004. Available to System Administrator and Team Manager.

Default row fields:

```text
usage_log_id
time
user
api_key_mask
model
input_tokens
output_tokens
cost
status
```

Prompt/response payloads are returned only when:

```text
caller has analytics.detail.read
caller explicitly requests include_payload=true
access is audited
payload is masked/redacted according to sensitive-data rules
```

##### Consumption Summary

API: M05-IC-005. Available to System Administrator and Team Manager.

Displays all-user totals by day/week/month, model breakdown, cost/token trend, and fluctuation metrics.

#### 2.6.5 Data Design

##### AnalyticsAggregate

| Attribute | Type | Constraints |
|---|---|---|
| aggregate_id | UUID/varchar | PK |
| aggregate_type | enum | `PERSONAL`, `RANKING`, `SUMMARY`, `PROMPT_CATEGORY` |
| period_type | enum | `DAY`, `WEEK`, `MONTH`, `CURRENT_ACCUMULATED` |
| period_start_at | timestamp | required |
| period_end_at | timestamp | nullable |
| user_id | UUID/varchar | nullable |
| model_id | UUID/varchar | nullable |
| prompt_category_id | UUID/varchar | nullable |
| input_tokens | bigint | required |
| output_tokens | bigint | required |
| total_tokens | bigint | required |
| input_cost | decimal(20,6) | required |
| output_cost | decimal(20,6) | required |
| total_cost | decimal(20,6) | required |
| currency | char(3) | required |
| calculated_at | timestamp | required |
| version | integer | required |

##### PromptCategory

| Attribute | Type | Constraints |
|---|---|---|
| prompt_category_id | UUID/varchar | PK |
| category_name | varchar(128) | unique, required |
| description | text | nullable |
| status | enum | `ACTIVE`, `DELETED` |
| created_at | timestamp | required |

##### PromptClassificationResult

| Attribute | Type | Constraints |
|---|---|---|
| classification_id | UUID/varchar | PK |
| usage_log_id | UUID/varchar | unique FK UsageLog |
| prompt_category_id | UUID/varchar | FK PromptCategory |
| classification_status | enum | `PENDING`, `CLASSIFIED`, `FAILED` |
| confidence_score | decimal(5,4) | nullable |
| classified_at | timestamp | nullable |
| error_code | varchar(128) | nullable |

##### AnalyticsQueryAudit

| Attribute | Type | Constraints |
|---|---|---|
| query_audit_id | UUID/varchar | PK |
| user_id | UUID/varchar | required |
| interface_id | varchar(32) | required |
| query_filters | jsonb | sanitized |
| result_count | integer | required |
| created_at | timestamp | required |

#### 2.6.6 Permission Design

| Function | Required Permission | System Administrator | Team Manager | Normal User |
|---|---|---:|---:|---:|
| Personal consumption | `analytics.personal.read` | Yes | Yes | Yes |
| Consumption ranking | `analytics.ranking.read` | Yes | Yes | Yes |
| Prompt category statistics | `analytics.prompt_category.read` | Yes | Yes | Yes |
| Consumption detail | `analytics.detail.read` | Yes | Yes | No |
| Consumption summary | `analytics.summary.read` | Yes | Yes | No |

Team Manager scope remains a product clarification because no team hierarchy is defined.

#### 2.6.7 Logging Design

Events:

```text
analytics.personal.viewed
analytics.ranking.viewed
analytics.prompt_category.viewed
analytics.detail.viewed
analytics.summary.viewed
analytics.permission.denied
analytics.query.invalid
analytics.query.failed
```

Never log raw prompts, raw model responses, raw API Key Secrets, authorization headers, or session tokens. Prompt/response access must be audited without copying raw payloads into operational logs.

---

### 2.7 Cross-Module Permission Matrix

| Permission | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| `platform.provider.*` | Yes | No | No |
| `platform.model.*` | Yes | No | No |
| `platform.openapi.*` | Yes | No | No |
| `platform.user.*` | Yes | No | No |
| `platform.role.*` | Yes | No | No |
| `platform.api_key.read_all` | Yes | No | No |
| `platform.api_key.extend_expiry` | Yes | No | No |
| `platform.quota_policy.*` | Yes | No | No |
| `workbench.api_key.create` | Yes | Yes | Yes |
| `workbench.api_key.read_own` | Yes | Yes | Yes |
| `workbench.api_key.update_status_own` | Yes | Yes | Yes |
| `workbench.api_key.delete_own` | Yes | Yes | Yes |
| `workbench.model.read` | Yes | Yes | Yes |
| `workbench.openapi.read` | Yes | Yes | Yes |
| `analytics.personal.read` | Yes | Yes | Yes |
| `analytics.ranking.read` | Yes | Yes | Yes |
| `analytics.prompt_category.read` | Yes | Yes | Yes |
| `analytics.detail.read` | Yes | Yes | No |
| `analytics.summary.read` | Yes | Yes | No |

---

### 2.8 Cross-Module Logging Standard

All modules emit structured logs with this baseline schema:

```json
{
  "timestamp": "2026-05-27T00:00:00.000Z",
  "level": "INFO",
  "trace_id": "req_...",
  "module_id": "M04",
  "service_name": "llm-gateway",
  "user_id": "usr_...",
  "action": "gateway.request.completed",
  "resource_type": "InferenceRequest",
  "resource_id": "ulg_...",
  "payload_summary": {},
  "result": "SUCCESS",
  "error_code": null,
  "latency_ms": 100
}
```

Sensitive-data rules:

| Data | Rule |
|---|---|
| Raw API Key Secret | Never log; never store recoverably |
| API Key hash | Never log |
| API Key mask | May log/display |
| Provider API key | Never log plaintext |
| Session token | Never log |
| Random login password | Never log |
| Enterprise email | Hash or mask in operational logs |
| Prompt | Protected UsageLog storage only |
| Model response | Protected UsageLog storage only |
| Authorization header | Never log |

---

## 3. Backend Service Designs

### 3.1 Backend Service Architecture Overview

| Service ID | Service Name | Category | Primary Module | Purpose |
|---|---|---|---|---|
| BS01 | Login Email Delivery Worker | Async worker | M01 | Send one-time random login passwords |
| BS02 | Usage Event Outbox Dispatcher | Async dispatcher | M04 | Publish UsageLog events after durable commit |
| BS03 | Prompt Classification Worker | Async worker | M05 | Automatically classify prompts |
| BS04 | Analytics Aggregation Worker | Batch/stream worker | M05 | Precompute token/cost aggregates |
| BS05 | Quota Reset Scheduler and Worker | Scheduled worker | M02/M04 | Apply quota reset policy |
| BS06 | Runtime Cache Invalidation Consumer | Event consumer | M02/M03/M04 | Invalidate runtime caches after mutations |
| BS07 | Failed Event Retry and DLQ Reprocessor | Operational worker | Cross-module | Reprocess failed async events safely |

Common message envelope:

```json
{
  "event_id": "evt_01HX0000000000000000000000",
  "event_type": "usage.log.persisted",
  "schema_version": "1.0",
  "occurred_at": "2026-05-27T00:00:00Z",
  "trace_id": "req_01HX0000000000000000000000",
  "producer": "llm-gateway",
  "idempotency_key": "usage_log_id:ulg_01HX0000000000000000000000",
  "payload": {}
}
```

Common worker lifecycle:

```text
Receive message
  → validate schema
  → check idempotency key
  → mark processing state
  → execute business logic
  → persist result transactionally
  → acknowledge only after durable success
  → retry retryable failures with exponential backoff
  → move permanently failed messages to DLQ
```

---

### 3.2 BS01 — Login Email Delivery Worker

#### Purpose

Sends one-time random login passwords to enterprise email addresses after M01 creates a LoginChallenge.

#### Input Event

`auth.email.delivery.requested`

```json
{
  "event_id": "evt_...",
  "event_type": "auth.email.delivery.requested",
  "schema_version": "1.0",
  "trace_id": "req_...",
  "idempotency_key": "challenge_id:lch_...",
  "payload": {
    "challenge_id": "lch_...",
    "enterprise_email": "user@example.com",
    "enterprise_email_mask": "u***@example.com",
    "expires_at": "2026-05-27T00:05:00Z"
  }
}
```

#### Processing

```text
Consume event
  → validate schema
  → load LoginChallenge
  → verify status PENDING and not expired
  → render email template
  → send via enterprise email provider
  → record delivery status
  → acknowledge after status persisted
```

#### State Machine

```text
EMAIL_DELIVERY_PENDING
  → EMAIL_DELIVERY_SENDING
  → EMAIL_DELIVERY_SENT
  → EMAIL_DELIVERY_FAILED_RETRYABLE
  → EMAIL_DELIVERY_FAILED_PERMANENT
```

#### High Availability

| Concern | Design |
|---|---|
| Duplicate delivery events | Idempotency key = challenge_id |
| Email provider throttling | Per-domain/global send-rate limiter |
| Worker crash | Message redelivery; status check prevents unsafe duplicate behavior |
| Expired challenge | Permanent failure; do not send |
| Email provider temporary failure | Retry with exponential backoff |

---

### 3.3 BS02 — Usage Event Outbox Dispatcher

#### Purpose

Reliably publishes events after UsageLog, CostRecord, and QuotaBalance updates commit.

#### Processing

```text
Poll TransactionalOutbox
  → lock pending batch
  → publish event to broker
  → mark PUBLISHED after broker acknowledgement
  → retry on publish failure
  → move to failed permanent after retry exhaustion
```

Outbox insert occurs in the same transaction as M04 UsageLog update, CostRecord insert, and QuotaBalance update.

#### Output Event

`usage.log.persisted`

```json
{
  "event_id": "evt_...",
  "event_type": "usage.log.persisted",
  "schema_version": "1.0",
  "trace_id": "req_...",
  "producer": "usage-outbox-dispatcher",
  "idempotency_key": "usage_log_id:ulg_...",
  "payload": {
    "usage_log_id": "ulg_...",
    "user_id": "usr_...",
    "api_key_id": "key_...",
    "model_id": "mdl_...",
    "provider_id": "prv_...",
    "quota_period_id": "qtp_...",
    "request_status": "SUCCESS",
    "input_tokens": 1000,
    "output_tokens": 500,
    "total_tokens": 1500,
    "input_cost": "0.003000",
    "output_cost": "0.007500",
    "total_cost": "0.010500",
    "currency": "USD",
    "request_started_at": "2026-05-27T00:00:00Z"
  }
}
```

#### HA Rules

Use row-level locks with `SKIP LOCKED` or equivalent. Duplicate publishes are allowed; consumers deduplicate by idempotency key.

---

### 3.4 BS03 — Prompt Classification Worker

#### Purpose

Automatically classifies prompts from UsageLogs for prompt-category analytics. The taxonomy and classifier engine are product/configuration decisions.

#### Processing

```text
Consume prompt.classification.requested or usage.log.persisted
  → load UsageLog
  → check if PromptClassificationResult exists
  → retrieve prompt from protected UsageLog storage
  → classify prompt using configured classifier
  → map to PromptCategory
  → insert/update PromptClassificationResult
  → emit analytics.aggregate.requested
  → acknowledge
```

#### Input Event

```json
{
  "event_type": "prompt.classification.requested",
  "idempotency_key": "usage_log_id:ulg_...",
  "payload": {
    "usage_log_id": "ulg_...",
    "user_id": "usr_...",
    "model_id": "mdl_...",
    "request_started_at": "2026-05-27T00:00:00Z"
  }
}
```

#### State Machine

```text
CLASSIFICATION_PENDING
  → CLASSIFICATION_PROCESSING
  → CLASSIFIED
  → CLASSIFICATION_FAILED_RETRYABLE
  → CLASSIFICATION_FAILED_PERMANENT
```

#### High Concurrency and Privacy

| Concern | Design |
|---|---|
| Many prompts | Partition queue by usage_log_id hash |
| Duplicate events | Unique constraint on usage_log_id |
| Large prompt payloads | Event carries usage_log_id only; worker loads prompt by reference |
| Sensitive content | Raw prompt is never logged or placed into queue messages |

---

### 3.5 BS04 — Analytics Aggregation Worker

#### Purpose

Precomputes token/cost aggregates for M05 dashboards while UsageLog and CostRecord remain the source of truth.

#### Processing

```text
Consume usage.log.persisted or analytics.aggregate.requested
  → load UsageLog and CostRecord
  → determine impacted aggregate keys
  → calculate DAY, WEEK, MONTH, CURRENT_ACCUMULATED periods
  → upsert AnalyticsAggregate records
  → record processed-event idempotency
  → acknowledge
```

Supported aggregate dimensions:

```text
User
Model
Period
Prompt Category
Aggregate Type
```

No team/project dimension is introduced.

#### Idempotency Key

```text
usage_log_id + aggregate_type + period_type + model_id + user_id + prompt_category_id
```

#### HA Rules

Use a processed-event table to prevent double counting. Scheduled recompute can rebuild aggregates from UsageLog and CostRecord if corruption is suspected.

---

### 3.6 BS05 — Quota Reset Scheduler and Worker

#### Purpose

Applies the QuotaResetPolicy configured by System Administrator.

#### Scheduler Logic

```text
Wake on polling interval
  → load current QuotaResetPolicy
  → if reset_mode = NONE: do not create reset jobs
  → if reset_mode = MONTHLY: evaluate due time
  → create quota.reset.requested event once per policy-period
```

#### Worker Logic

```text
Consume quota.reset.requested
  → validate policy version and target period
  → create new QuotaPeriod
  → batch active Users
  → calculate effective cost limit for each User
  → create QuotaBalance with consumed=0 and remaining=limit
  → checkpoint batch progress
  → complete job
```

#### Input Event

```json
{
  "event_type": "quota.reset.requested",
  "idempotency_key": "quota_reset:qrp_...:2026-06",
  "payload": {
    "policy_id": "qrp_...",
    "policy_version": 3,
    "new_period_start_at": "2026-06-01T00:00:00Z",
    "new_period_end_at": "2026-07-01T00:00:00Z",
    "period_type": "MONTHLY"
  }
}
```

#### HA Rules

| Concern | Design |
|---|---|
| Multiple scheduler replicas | Leader election or unique reset-job constraint |
| Many users | Batch by user_id and checkpoint |
| Duplicate reset events | Unique key on policy/version/period |
| API requests during reset | M04 resolves period by timestamp and locks QuotaBalance row |

---

### 3.7 BS06 — Runtime Cache Invalidation Consumer

#### Purpose

Keeps M04 runtime caches fresh after admin and Workbench mutations.

#### Input Event

`config.changed`

```json
{
  "event_type": "config.changed",
  "idempotency_key": "config_changed:Model:mdl_...:version:5",
  "payload": {
    "resource_type": "Model",
    "resource_id": "mdl_...",
    "change_type": "UPDATED",
    "version": 5,
    "changed_fields": ["input_price_per_million_tokens", "output_price_per_million_tokens"]
  }
}
```

Supported resource types:

```text
APIKey
User
Role
Provider
Model
EnterpriseOpenAPI
QuotaResetPolicy
```

Mandatory event emission points:

| Interface | Resource Type |
|---|---|
| M02-IC-004, M02-IC-005 | Provider |
| M02-IC-009, M02-IC-010 | Model |
| M02-IC-014, M02-IC-015 | EnterpriseOpenAPI |
| M02-IC-019, M02-IC-020 | User |
| M02-IC-024, M02-IC-025 | Role |
| M02-IC-027 | APIKey |
| M02-IC-029 | QuotaResetPolicy |
| M03-IC-003, M03-IC-004 | APIKey |

Cache delete is idempotent. Short TTLs provide fallback if invalidation is delayed.

---

### 3.8 BS07 — Failed Event Retry and DLQ Reprocessor

#### Purpose

Safely inspects and reprocesses failed async messages after transient failures or corrected configuration problems.

#### Processing

```text
Scan DLQ
  → load message metadata
  → classify failure reason
  → requeue retryable/corrected failures preserving idempotency key
  → mark unrecoverable failures permanent
  → emit operational log and metric
```

DLQ payloads must contain references only, not raw prompts, responses, API Key Secrets, provider credentials, or session tokens.

---

### 3.9 Shared Worker Data Models

#### TransactionalOutbox

| Attribute | Type | Constraints |
|---|---|---|
| outbox_id | UUID/varchar | PK |
| event_type | varchar(128) | required |
| aggregate_type | varchar(128) | required |
| aggregate_id | UUID/varchar | required |
| payload | jsonb | no raw secrets |
| status | enum | `PENDING`, `PUBLISHING`, `PUBLISHED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT` |
| attempt_count | integer | required |
| next_attempt_at | timestamp | required |
| created_at | timestamp | required |
| published_at | timestamp | nullable |
| last_error_code | varchar(128) | nullable |

#### WorkerProcessedEvent

| Attribute | Type | Constraints |
|---|---|---|
| processed_event_id | UUID/varchar | PK |
| consumer_name | varchar(128) | required |
| event_id | UUID/varchar | required |
| idempotency_key | varchar(256) | required |
| processing_status | enum | `PROCESSING`, `SUCCEEDED`, `FAILED` |
| processed_at | timestamp | nullable |
| result_ref | UUID/varchar | nullable |
| error_code | varchar(128) | nullable |

Unique:

```text
(consumer_name, event_id)
(consumer_name, idempotency_key)
```

#### BackgroundJob

| Attribute | Type | Constraints |
|---|---|---|
| job_id | UUID/varchar | PK |
| job_type | enum | email/classification/aggregation/quota/cache/DLQ |
| job_status | enum | worker state |
| source_event_id | UUID/varchar | nullable |
| idempotency_key | varchar(256) | required |
| attempt_count | integer | required |
| max_attempts | integer | required |
| next_attempt_at | timestamp | nullable |
| started_at | timestamp | nullable |
| completed_at | timestamp | nullable |
| error_code | varchar(128) | nullable |
| error_summary | varchar(1024) | sanitized |

---

### 3.10 Shared High-Availability Rules

#### Health Checks

Every worker exposes:

```text
/healthz   → process liveness
/readiness → required dependencies available
```

Dependencies include database, queue, cache, email provider, and classifier provider as applicable.

#### Graceful Shutdown

```text
Stop polling new messages
  → finish or safely abandon current message
  → commit or rollback transaction
  → acknowledge only after durable success
  → flush logs/metrics
  → exit within grace period
```

#### Retry Policy

| Attempt | Delay |
|---:|---:|
| 1 | 5 seconds |
| 2 | 30 seconds |
| 3 | 2 minutes |
| 4 | 10 minutes |
| 5 | 30 minutes |
| Exhausted | DLQ |

Retryable errors:

```text
database timeout
queue timeout
cache timeout
email provider temporary failure
classifier temporary failure
network timeout
lock conflict
```

Permanent errors:

```text
invalid message schema
missing required source record after verification
unsupported event type
business rule violation
expired login challenge
```
