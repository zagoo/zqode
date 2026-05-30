# Functional Design Document: LLM API Gateway Platform

## Document Control

| Item | Value |
|---|---|
| Document Type | Functional Design Document (FDD) |
| Product Area | Internal Enterprise LLM API Gateway Platform |
| Feature | AI Chat Module |
| Source Requirement | `chatfrd.md` |
| Language | English |
| Phase 2 Research | Skipped by user instruction |
| Scope Discipline | No feature expansion beyond the FRD; technical controls are included only when required for implementation readiness |

---

## 0. Domain Concept & Requirements Knowledge Base

### 0.1 Source Boundary

The source FRD defines a new **AI Chat** interface for an internal enterprise **LLM API Gateway Platform**. The AI Chat capability allows employees to select an API Key that they own or are authorized to use, choose a model that the selected Key is permitted to call, and interact with the model through the platform UI. Every AI Chat request must continue to use the existing LLM API Gateway request path. The AI Chat module must not bypass existing authentication, model permission, rate limiting, circuit breaker, logging, audit, billing, or usage-statistics rules.

The FRD includes the following functional scope:

| Scope Item | Included | Design Boundary |
|---|---:|---|
| AI Chat UI | Yes | New frontend workbench page. |
| API Key selection | Yes | Only Keys owned by or authorized to the current user. |
| Model selection | Yes | Model list must be filtered by selected Key permissions. |
| Text chat | Yes | Prompt input and model response output. |
| Conversation history | Yes | Create, view, load, continue, and delete own conversations. |
| Multi-turn context | Yes | Context is based on conversation message list. |
| Image chat | Yes | Only when selected model supports image input. |
| Gateway invocation record | Yes | AI Chat requests are included in existing Gateway records. |
| Usage statistics | Yes | Reuses existing analytics/consumption detail capability. |
| New AI Chat reporting module | No | Explicitly out of scope. |
| Knowledge base / file management / cross-session image reuse | No | Explicitly out of scope. |

### 0.2 Business Concepts

| Concept | Definition |
|---|---|
| LLM API Gateway Platform | Existing internal platform that brokers model calls and enforces authentication, authorization, model permission, rate limiting, circuit breaker, logging, audit, and usage statistics. |
| AI Chat | New UI module that lets users chat with AI models through the Gateway. |
| API Key / Key | Existing credential object in the Gateway platform. AI Chat uses `key_id` references only and never exposes Key secrets. |
| Authorized Key | A Key the current user owns or has been granted permission to use. |
| Key Availability | Runtime state determining whether a Key can be used. A Key is not usable if it is disabled, expired, quota-exhausted, or has no model permissions. |
| Model | A model exposed by the platform and callable through the Gateway. |
| Model Permission | Relationship between a Key and one or more models the Key is allowed to call. |
| Model Capability | Model metadata such as text support, image support, context limit, supported image MIME types, max image size, and max image count. |
| Conversation Session | A persisted chat container owned by one user. It contains ordered messages and remembers the most recently used Key and model. |
| Conversation Message | A user or assistant message belonging to one conversation session. The ordered message list is the basis for multi-turn context. |
| Image Attachment | Image uploaded for a single conversation context. It is not a knowledge-base document, file library item, or cross-session reusable asset. |
| Gateway Inference Request | Request created by AI Chat and executed through the existing LLM API Gateway. |
| Usage Record | Existing Gateway usage record enriched with `request_origin = AI_CHAT`, session ID, user ID, team ID, Key ID, model ID, token usage, cost, and status. |
| Audit Log | Structured operational/security log created by platform services and Gateway request flow. |

### 0.3 Actors and Roles

| Role | Primary Intent | Functional Boundary |
|---|---|---|
| System Administrator | Operates and supervises the platform. | Can access AI Chat as a user if authorized to a Key. Can query platform-level AI Chat consumption details through the existing analytics module. Does not receive default access to user conversation content through AI Chat. |
| Team Manager | Supervises team usage. | Can access AI Chat as a user if authorized to a Key. Can query own-team AI Chat consumption details through the existing analytics module. Does not receive default access to other users' conversation content. |
| Normal User | Uses AI Chat for work. | Can select authorized Keys, select permitted models, send text/image messages, and manage own conversation history. |

### 0.4 Domain Entities

| Entity | Key Attributes | Relationships |
|---|---|---|
| User | `user_id`, `display_name`, `status`, `team_id`, `roles` | Belongs to Team; owns Conversation Sessions; may own or be authorized to use Keys. |
| Team | `team_id`, `team_name`, `status` | Contains Users; scopes Key authorization and analytics visibility. |
| API Key | `key_id`, `key_name`, `team_id`, `owner_user_id`, `status`, `expires_at`, `quota_state` | Authorized to Users/Teams; has model permissions; used by Gateway invocation. |
| Model | `model_id`, `model_name`, `status`, `capabilities` | Callable only when permitted by selected Key. |
| Conversation Session | `session_id`, `owner_user_id`, `team_id`, `title`, `last_key_id`, `last_model_id`, `status`, timestamps | Contains messages and attachments. |
| Conversation Message | `message_id`, `session_id`, `role`, `content`, `status`, `key_id`, `model_id`, token fields, error fields | Belongs to a session; may reference image attachments. |
| Image Attachment | `attachment_id`, `session_id`, `message_id`, `mime_type`, `size_bytes`, `storage_uri`, `status`, `expires_at` | Belongs to one user and one session; bound to one message when sent. |
| AI Chat Invocation | `invocation_id`, `gateway_request_id`, `session_id`, `user_message_id`, `assistant_message_id`, `key_id`, `model_id`, `status` | Correlates AI Chat messages to Gateway request and usage records. |
| Gateway Usage Record | `usage_id`, `request_origin`, `gateway_request_id`, `user_id`, `team_id`, `key_id`, `model_id`, tokens, cost, status | Queried by analytics module. |

### 0.5 Functional Requirement Baseline

| Requirement ID | Requirement |
|---|---|
| R-AIC-001 | AI Chat must be a UI module inside the existing LLM API Gateway platform. |
| R-AIC-002 | Users can select only Keys they own or are authorized to use. |
| R-AIC-003 | AI Chat must never display or persist plaintext API Key values. |
| R-AIC-004 | Disabled, expired, quota-exhausted, or no-model-permission Keys cannot be used for new chat requests. |
| R-AIC-005 | The model list must be dynamically filtered by the selected Key's permissions. |
| R-AIC-006 | Unavailable, offline, or unauthorized models cannot be used for chat. |
| R-AIC-007 | Users can send text prompts and receive model responses. |
| R-AIC-008 | Every AI Chat request must be executed through the existing LLM API Gateway. |
| R-AIC-009 | AI Chat must show generation states: generating, completed, and failed. |
| R-AIC-010 | Failed generation must show a reason and allow the current message to be resent. |
| R-AIC-011 | Users can create new conversations. |
| R-AIC-012 | Users can view, load, continue, and delete their own conversation history. |
| R-AIC-013 | Multi-turn context must be based on the conversation message list. |
| R-AIC-014 | Switching model affects only subsequent requests; historical messages are not rewritten. |
| R-AIC-015 | Continuing a historical conversation defaults to the most recently used Key and model, but both must be revalidated before new requests. |
| R-AIC-016 | If a historical Key or model is no longer available, the historical conversation remains viewable but cannot continue with that unavailable Key/model. |
| R-AIC-017 | Conversation history stores message content, Key ID, model ID, creation time, update time, and invocation status. |
| R-AIC-018 | Conversation history must not store Key secrets. |
| R-AIC-019 | If context exceeds model limits, the system applies platform truncation policy or asks the user to start a new conversation. |
| R-AIC-020 | Image upload appears only when the selected model supports image input. |
| R-AIC-021 | Users can upload images in a single conversation and ask questions based on image content. |
| R-AIC-022 | Image capability is limited to current conversation context and must not become a knowledge base, file management system, or cross-session reuse feature. |
| R-AIC-023 | Image type, size, count, and retention follow platform configuration. |
| R-AIC-024 | Unsupported images must show a clear reason. |
| R-AIC-025 | AI Chat requests must be included in existing Gateway invocation records. |
| R-AIC-026 | Usage statistics reuse existing analytics capability; AI Chat does not add a new reporting module. |
| R-AIC-027 | Normal users cannot view other users' conversation history. |
| R-AIC-028 | Team data and usage records are isolated by team. |
| R-AIC-029 | System Administrators and Team Managers can query AI Chat request consumption details in the existing analytics module according to their scope. |

### 0.6 Functional Requirements Knowledge Graph

```text
User
 ├─ has Role
 ├─ belongs to Team
 ├─ owns or is authorized for API Key
 └─ owns Conversation Session

Team
 ├─ contains User
 ├─ scopes API Key authorization
 └─ scopes Usage Record visibility

API Key
 ├─ has status / expiry / quota
 ├─ has Model permissions
 ├─ is selected in AI Chat
 └─ is consumed by Gateway Inference Request

Model
 ├─ has availability status
 ├─ has capabilities
 │   ├─ supports text input
 │   └─ may support image input
 ├─ is filtered by selected API Key
 └─ is consumed by Gateway Inference Request

AI Chat Workbench
 ├─ requires authenticated User
 ├─ loads authorized API Key summaries
 ├─ loads Models permitted by selected Key
 ├─ creates / loads Conversation Session
 ├─ submits Message
 ├─ optionally uploads Image Attachment when model supports image
 └─ displays response / error state

Conversation Session
 ├─ belongs to User
 ├─ contains Conversation Messages
 ├─ stores latest API Key ID
 ├─ stores latest Model ID
 └─ provides context for multi-turn chat

Conversation Message
 ├─ belongs to Conversation Session
 ├─ may reference Image Attachment
 ├─ becomes part of Conversation Context
 └─ may produce Usage Record through Gateway Inference Request

Gateway Inference Request
 ├─ consumes User, API Key, Model, Message, optional Image Attachment
 ├─ triggers platform auth / permission / rate limit / circuit breaker
 ├─ produces Assistant Message
 ├─ produces Usage Record
 └─ produces Audit Log
```

### 0.7 Ambiguities and Design Assumptions

| Area | Ambiguity | Assumption Used in This FDD |
|---|---|---|
| Login system | The FRD says AI Chat belongs to the internal platform but does not define login. | Reuse existing platform authentication and session context. No new login product is introduced. |
| Key authorization model | The FRD says users may use applied or authorized Keys. | Key authorization may be user-level or team-level. AI Chat works only with safe `key_id` references. |
| Admin content visibility | The FRD allows admins/team managers to query consumption details but does not grant conversation-content visibility. | Elevated roles can query usage metadata by scope, not user conversation content. |
| Conversation title | The FRD requires saved history but does not define title behavior. | Use `New Chat` initially; optionally derive a safe preview from the first user message. No manual title-management feature is introduced. |
| Context truncation | The FRD says use platform strategy to truncate older messages or prompt for a new session. | Implement a configurable context policy: include recent ordered messages, truncate oldest eligible messages, and return `CONTEXT_LIMIT_EXCEEDED` if still too large. |
| Image retention | The FRD says image retention follows platform configuration. | Store image metadata and object references; exact retention duration is configurable outside AI Chat. |
| Streaming | The FRD requires generation status display but does not require token streaming. | Use synchronous request/response plus frontend loading state. No streaming API is introduced. |
| Retry | The FRD says users can resend the current message after failure. | Provide retry for a failed assistant message using the same user message, Key, model, and attachments with idempotency protection. |

### 0.8 Phase 2 Research Status

Phase 2 external research was explicitly skipped by user instruction. This FDD therefore contains no external research findings or external reference citations. The design is based on the FRD, existing platform assumptions, and implementation consistency checks only.

---

## 1. Executive Summary & Module Map

### 1.1 Executive Summary

This FDD designs the AI Chat module as a controlled client of the existing LLM API Gateway. The module gives internal users a browser-based chat interface while preserving the Gateway as the only model execution path. The functional design is organized around six modules:

1. Platform Authentication & Session Context.
2. AI Chat Workbench.
3. Conversation Management.
4. Key & Model Authorization Integration.
5. AI Chat Gateway Invocation Layer.
6. Usage Analytics & Consumption Detail Integration.

The design avoids creating a second model access path, a new reporting product, a knowledge base, a general file manager, or cross-session image storage. All generated requests are traceable to user, team, Key ID, model ID, session ID, and Gateway request ID.

### 1.2 Module Decomposition

| Module ID | Module Name | Category | Scope Boundary | Roles | Upstream Dependencies | Downstream Dependencies |
|---|---|---|---|---|---|---|
| M01 | Platform Authentication & Session Context | Platform Authentication & Login | Validates current platform user and provides `user_id`, `team_id`, and roles. No new login capability. | All roles | Existing identity platform | M02, M03, M04, M05, M06 |
| M02 | AI Chat Workbench | Core Module / Workbench / Developer Portal | Frontend AI Chat page: Key selector, model selector, history list, chat area, image upload area, error display. | All roles | M01, M03, M04, M05 | None |
| M03 | Conversation Management | Core Module | Creates, lists, loads, deletes sessions; stores messages and attachments metadata; builds context. | All roles for own data | M01, M04 | M02, M05 |
| M04 | Key & Model Authorization Integration | Platform Administration Integration | Lists safe Key summaries, returns permitted models, validates Key/model capability. No new Key admin UI. | All roles for authorized data | Existing Key registry, quota service, model registry | M02, M03, M05 |
| M05 | AI Chat Gateway Invocation Layer | API Service Layer | Validates chat requests, persists messages, invokes existing Gateway, handles response/failure, links usage. | All roles for own sessions | M01, M03, M04, existing Gateway | M06 |
| M06 | Usage Analytics & Consumption Detail Integration | Data Analytics & Reporting | Exposes AI Chat-originated usage through existing analytics module. No new report module. | System Administrator, Team Manager | Existing usage store, M05 | Existing analytics UI |

### 1.3 Cross-Module Main Flow

```text
User opens /ai-chat
  → M01 validates session
  → M02 renders workbench shell
  → M04 returns authorized Key summaries
  → M03 returns current user's conversation list
  → User selects Key
  → M04 returns models permitted by selected Key
  → User selects model
  → M02 shows image upload only when model supports image
  → User submits text and optional image attachment IDs
  → M05 validates session ownership, Key, model, quota, and image capability
  → M03 persists user message and assistant placeholder
  → M03 builds conversation context
  → M05 invokes existing Gateway
  → Gateway enforces auth, model permission, rate limit, circuit breaker, logging, audit, and metering
  → M05 persists assistant response or failure
  → M06 exposes usage through existing analytics module
```

### 1.4 Common API Conventions

All AI Chat APIs are under:

```text
/api/v1/ai-chat
```

Common headers:

| Header | Required | Purpose |
|---|---:|---|
| `Authorization` or platform session cookie | Yes | Existing platform authentication. |
| `X-Request-Id` | Recommended | Cross-service trace correlation. |
| `Idempotency-Key` | Required for mutation APIs | Prevent duplicate sessions, uploads, sends, or retries. |
| `Content-Type` | Yes | `application/json` or `multipart/form-data`. |

Common error response:

```json
{
  "error": {
    "code": "KEY_EXPIRED",
    "message": "The selected Key has expired.",
    "details": {
      "key_id": "uuid"
    },
    "trace_id": "trace-uuid",
    "retryable": false
  }
}
```

Common error catalog:

| Error Code | HTTP Status | Retryable | Meaning |
|---|---:|---:|---|
| `AUTH_REQUIRED` | 401 | No | User session is missing or expired. |
| `FORBIDDEN` | 403 | No | Caller has no permission for the resource. |
| `VALIDATION_ERROR` | 400 | No | Request shape or field value is invalid. |
| `SESSION_NOT_FOUND` | 404 | No | Session does not exist or is not visible. |
| `SESSION_FORBIDDEN` | 403 | No | Current user is not the session owner. |
| `KEY_NOT_FOUND` | 404 | No | Key does not exist. |
| `KEY_NOT_AUTHORIZED` | 403 | No | User is not authorized to use the Key. |
| `KEY_DISABLED` | 409 | No | Key is disabled. |
| `KEY_EXPIRED` | 409 | No | Key is expired. |
| `KEY_QUOTA_EXCEEDED` | 429 | No | Key has no remaining quota. |
| `KEY_NO_MODEL_PERMISSION` | 403 | No | Key has no model permission. |
| `MODEL_NOT_FOUND` | 404 | No | Model does not exist. |
| `MODEL_UNAVAILABLE` | 409 | Yes | Model is unavailable or offline. |
| `MODEL_NOT_AUTHORIZED` | 403 | No | Key cannot call the selected model. |
| `IMAGE_NOT_SUPPORTED` | 400 | No | Model does not support image input. |
| `IMAGE_TYPE_UNSUPPORTED` | 400 | No | Image MIME type is not supported. |
| `IMAGE_SIZE_EXCEEDED` | 413 | No | Image exceeds configured size. |
| `IMAGE_COUNT_EXCEEDED` | 400 | No | Image count exceeds configured limit. |
| `ATTACHMENT_NOT_FOUND` | 404 | No | Attachment does not exist or is not visible. |
| `CONTEXT_LIMIT_EXCEEDED` | 400 | No | Context exceeds model limit after policy handling. |
| `RATE_LIMITED` | 429 | Yes | Gateway rate limit reached. |
| `GATEWAY_TIMEOUT` | 504 | Yes | Gateway/provider timed out before safe persistence. |
| `GATEWAY_PROVIDER_ERROR` | 502 | Yes | Provider error before safe persistence. |
| `IDEMPOTENCY_CONFLICT` | 409 | No | Same idempotency key reused with different body. |
| `INTERNAL_ERROR` | 500 | Yes | Unexpected server error. |

Important response semantics for chat send/retry:

| Case | Response Rule |
|---|---|
| Validation fails before user message is accepted | Return HTTP 4xx/429 with common error response. No message is created. |
| Message is accepted and assistant generation later fails | Return HTTP 200 with `assistant_message.status = FAILED`, `error_code`, and `retryable`. |
| Server cannot persist accepted state | Return HTTP 5xx because the UI cannot safely render a persisted failed message. |

---

## 2. Module Designs

### 2.1 M01 — Platform Authentication & Session Context

#### 2.1.1 Scope

M01 validates the current user session and provides downstream modules with identity and authorization context. It reuses the existing platform authentication system and does not introduce a new login flow.

#### 2.1.2 Primary Functions

| Function | Description |
|---|---|
| Session validation | Validate the platform session cookie or authorization token. |
| User context resolution | Resolve `user_id`, `display_name`, `status`, `team_id`, and roles. |
| Permission context construction | Provide role and scope boundary to M02-M06. |
| Trace propagation | Attach or propagate `trace_id` for logging. |

#### 2.1.3 UI/UX Interaction Logic

| UI Event | API Binding | Success State | Failure State |
|---|---|---|---|
| Open `/ai-chat` | `GET /api/v1/platform/session/current` | Workbench shell loads. | Redirect to existing login or show session-expired message. |
| Session expires while working | Any protected API returns `401` | N/A | M02 shows “Your session has expired. Please sign in again.” |

#### 2.1.4 Interface: M01-I01 — Get Current Session Context

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/platform/session/current` |
| Consumer | M02, M03, M04, M05, M06 |

Request parameters: none.

Success response schema:

```json
{
  "type": "object",
  "required": ["user", "team", "roles"],
  "properties": {
    "user": {
      "type": "object",
      "required": ["user_id", "display_name", "status"],
      "properties": {
        "user_id": { "type": "string", "format": "uuid" },
        "display_name": { "type": "string" },
        "status": { "type": "string", "enum": ["ACTIVE", "DISABLED"] }
      }
    },
    "team": {
      "type": "object",
      "required": ["team_id", "team_name"],
      "properties": {
        "team_id": { "type": "string", "format": "uuid" },
        "team_name": { "type": "string" }
      }
    },
    "roles": {
      "type": "array",
      "items": { "type": "string", "enum": ["SYSTEM_ADMIN", "TEAM_MANAGER", "NORMAL_USER"] }
    }
  }
}
```

Internal processing:

1. Read platform session cookie or authorization token.
2. Validate token signature and expiry.
3. Resolve user and team records.
4. Reject disabled users.
5. Resolve role assignments.
6. Return session context.

Status codes: `200`, `401`, `403`, `500`.

Idempotency: read-only; no idempotency key required.

#### 2.1.5 Data Design

M01 uses existing identity tables:

| Entity | Required Fields |
|---|---|
| `users` | `user_id`, `display_name`, `status`, `team_id` |
| `teams` | `team_id`, `team_name`, `status` |
| `user_roles` | `user_id`, `role_code`, `scope_type`, `scope_id` |

Storage is the existing identity database and session cache. Retention follows existing platform policy.

#### 2.1.6 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Access AI Chat page | Yes | Yes | Yes |
| Receive own session context | Yes | Yes | Yes |
| Receive another user's session context | No | No | No |

Permission granularity: individual-level session identity.

#### 2.1.7 Logging Design

| Level | Trigger |
|---|---|
| DEBUG | Session cache diagnostics in non-production. |
| INFO | Session context resolved. |
| WARN | Expired session, disabled user, invalid role mapping. |
| ERROR | Identity lookup failure. |
| FATAL | Authentication service unavailable. |

Structured log schema:

```json
{
  "timestamp": "2026-05-30T10:00:00Z",
  "level": "INFO",
  "trace_id": "trace-uuid",
  "module": "M01",
  "user_id": "uuid",
  "team_id": "uuid",
  "action": "SESSION_CONTEXT_RESOLVED",
  "resource_type": "SESSION",
  "resource_id": "session-hash",
  "payload_summary": {},
  "result": "SUCCESS",
  "latency_ms": 12
}
```

Sensitive data: never log session tokens, authorization headers, or cookies.

---

### 2.2 M02 — AI Chat Workbench

#### 2.2.1 Scope

M02 is the frontend workbench for AI Chat. It renders Key selection, model selection, history list, chat messages, image upload entry, input box, send/retry actions, and user-facing error states. M02 never calls model providers directly and never receives plaintext API Key values.

#### 2.2.2 Primary Functions

| Function | Description |
|---|---|
| Page initialization | Load session context, authorized Keys, and recent conversation list. |
| Key selection | Select one authorized Key from safe summaries. |
| Model selection | Show only models permitted by selected Key. |
| Image entry visibility | Show upload only when selected model supports image input. |
| New conversation | Create a new session. |
| Send message | Submit text and optional image attachment IDs. |
| Retry failed message | Retry a failed assistant response. |
| History management | Load and delete own sessions. |
| Error display | Render clear errors for Key, model, image, rate limit, and Gateway failures. |

#### 2.2.3 UI Layout

```text
+-------------------------------------------------------------+
| AI Chat                                                     |
+----------------------+--------------------------------------+
| History List          | Key Selector | Model Selector       |
| - New Chat            |--------------------------------------|
| - Session A           | Chat Message Display                |
| - Session B           |                                      |
|                       |                                      |
|                       |--------------------------------------|
|                       | Image Upload Area                   |
|                       | Message Input                       |
|                       | Send Button                         |
+----------------------+--------------------------------------+
```

#### 2.2.4 Input Fields

Key selector:

| Field | Type | Default | Placeholder | Validation |
|---|---|---|---|---|
| `key_id` | Select | None | `Select a Key` | Required before model selection and message send. Must be one of M04-I01 returned Keys. |
| Key display | Read-only | N/A | N/A | Show Key name, team, status, quota summary, model count. Never show Key secret. |

Model selector:

| Field | Type | Default | Placeholder | Validation |
|---|---|---|---|---|
| `model_id` | Select | None | `Select a model` | Required before message send. Must be in M04-I02 response for selected Key. |
| Capability indicator | Read-only | N/A | N/A | Display `Text` or `Text + Image`. |

Message input:

| Field | Type | Default | Placeholder | Validation |
|---|---|---|---|---|
| `content` | Multiline text | Empty | `Ask AI a question...` | Required if no image is attached. Max length follows backend configuration. Trim for validation. |

Image upload:

| Field | Type | Default | Placeholder | Validation |
|---|---|---|---|---|
| `image_file` | File | None | `Upload image` | Visible only when selected model supports image input. Validate type/size client-side and backend-side. |
| `image_attachment_ids` | Hidden array | Empty | N/A | Must reference uploaded images in current session. |

#### 2.2.5 UI Action-to-API Binding

| UI Action | API Binding | Success Rendering | Failure Rendering |
|---|---|---|---|
| Open AI Chat | M01-I01 | Render shell. | Login/session-expired state. |
| Load Keys | M04-I01 | Render Key selector. | `Unable to load Keys.` |
| Select Key | M04-I02 | Render model selector and clear prior model. | Show unavailable reason. |
| Load history | M03-I02 | Render session list. | Empty/error state. |
| New Chat | M03-I01 | Create empty active session. | Toast failure. |
| Load session | M03-I03 | Render messages in order. | Toast failure. |
| Upload image | M05-I01 | Show thumbnail and attachment summary. | Show image error reason. |
| Send message | M05-I02 | Show local generating state while request is pending; render completed or failed assistant message when returned. | Show API error if request rejected before persistence. |
| Retry failed response | M05-I03 | Show local generating state; update failed assistant message. | Keep failed state and show new error. |
| Delete session | M03-I04 | Remove from history list. | Toast failure. |
| Open usage details | M06-I01 through existing analytics UI | Show usage detail if authorized. | Permission denied or empty state. |

#### 2.2.6 Output Rendering Rules

| State | Rendering |
|---|---|
| No selected Key/model | `Select a Key and model to start chatting.` |
| No authorized Keys | `No available Keys. Please apply for or request access to a Key.` |
| Key has no models | `This Key has no available model permissions.` |
| Generating | Local assistant placeholder with spinner while M05-I02 or M05-I03 is pending. |
| Completed | Render assistant content as sanitized text/Markdown according to platform rendering policy. |
| Failed persisted generation | Render error reason and retry button. |
| Rate limited | `Request rate limit reached. Please try again later.` |
| Key unavailable in history | Conversation is viewable; send is disabled until valid Key/model is selected. |
| Image unsupported | Hide upload entry; backend rejection still shows explicit error if triggered. |

#### 2.2.7 Interface Design

M02 owns no backend REST API. It consumes M01-I01, M03-I01 through M03-I04, M04-I01 through M04-I02, M05-I01 through M05-I03, and existing analytics UI over M06-I01.

Frontend route:

| Route | Purpose |
|---|---|
| `/ai-chat` | AI Chat Workbench page. |

Route guard:

1. Call M01-I01.
2. If unauthenticated, redirect to existing platform login.
3. Load M04-I01 and M03-I02.
4. Render workbench.

#### 2.2.8 Data Design

M02 stores only client-side UI state:

| State Object | Fields | Persistence |
|---|---|---|
| `selectedKey` | `key_id`, `key_name`, `selectable`, `unavailable_reason` | Browser memory only. |
| `selectedModel` | `model_id`, `model_name`, `capabilities` | Browser memory only. |
| `activeSession` | `session_id`, `title`, `status` | Browser memory only; persisted by M03. |
| `draftMessage` | `content`, `image_attachment_ids` | Browser memory only. |
| `pendingRequest` | `idempotency_key`, `status` | Browser memory only. |

No Key secret, provider credential, or raw session token may be stored in browser local storage.

#### 2.2.9 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Open AI Chat page | Yes | Yes | Yes |
| View own/authorized Keys | Yes | Yes | Yes |
| Select authorized Key | Yes | Yes | Yes |
| Select model permitted by Key | Yes | Yes | Yes |
| View own conversations | Yes | Yes | Yes |
| Delete own conversations | Yes | Yes | Yes |
| View another user's conversations | No | No | No |
| Use unauthorized Key/model | No | No | No |

#### 2.2.10 Logging Design

Frontend telemetry must not include prompt content, assistant content, image binary/base64, Key secret, session token, or authorization header.

| Level | Trigger |
|---|---|
| DEBUG | Local development state transitions. |
| INFO | Page opened, session loaded, send attempted. |
| WARN | Client validation failure. |
| ERROR | API request failure or rendering failure. |
| FATAL | Workbench cannot initialize. |

---

### 2.3 M03 — Conversation Management

#### 2.3.1 Scope

M03 owns conversation session and message persistence. It creates, lists, loads, and soft-deletes sessions; stores messages and image metadata references; and provides internal context assembly to M05. It does not call model providers.

#### 2.3.2 Primary Functions

| Function | Description |
|---|---|
| Create session | Create an active session owned by current user. |
| List sessions | Return visible sessions for current user. |
| Get session detail | Return session metadata, messages, and attachment summaries. |
| Delete session | Soft delete session from frontend visibility. |
| Store messages | Persist user and assistant messages created by M05. |
| Bind attachments | Bind uploaded images to the submitted user message. |
| Build context | Internal method that returns ordered message context for M05. |
| Apply context policy | Truncate older eligible messages or return context-limit error. |

#### 2.3.3 UI/UX Interaction Logic

| UI Area | Behavior |
|---|---|
| History list | Sessions sorted by `updated_at DESC`. |
| New Chat | Creates session title `New Chat`. |
| First user message | May update title from first user message preview. |
| Load Chat | Messages are returned in chronological order. |
| Delete Chat | Session disappears after successful soft delete. |
| Historical unavailable Key/model | Conversation loads read-only until a valid Key/model is selected. |

#### 2.3.4 Interface: M03-I01 — Create Conversation Session

| Field | Value |
|---|---|
| Method | POST |
| Path | `/api/v1/ai-chat/sessions` |
| Consumer | M02 |

Request body:

```json
{
  "type": "object",
  "properties": {
    "initial_key_id": { "type": "string", "format": "uuid" },
    "initial_model_id": { "type": "string" }
  },
  "additionalProperties": false
}
```

Processing:

1. Validate session through M01.
2. If both `initial_key_id` and `initial_model_id` are supplied, validate through M04-I03.
3. If only one of the two fields is supplied, return `VALIDATION_ERROR`.
4. Create `ai_chat_session` with owner user, team, title `New Chat`, status `ACTIVE`, optional validated last Key/model.
5. Commit transaction.
6. Return session summary.

Success response:

```json
{
  "session_id": "uuid",
  "title": "New Chat",
  "status": "ACTIVE",
  "last_key_id": "uuid",
  "last_model_id": "model-id",
  "created_at": "2026-05-30T10:00:00Z",
  "updated_at": "2026-05-30T10:00:00Z"
}
```

Status codes: `201`, `400`, `401`, `403`, `409`, `429`, `500`.

Idempotency: required. Same user, same idempotency key, same body returns the original session.

#### 2.3.5 Interface: M03-I02 — List Conversation Sessions

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/ai-chat/sessions` |
| Consumer | M02 |

Query parameters:

| Parameter | Type | Required | Default | Validation |
|---|---|---:|---|---|
| `limit` | integer | No | 20 | 1-100 |
| `cursor` | string | No | None | Opaque cursor |

Processing:

1. Validate session through M01.
2. Query sessions where `owner_user_id = current_user.user_id` and `status = ACTIVE`.
3. Sort by `updated_at DESC`.
4. Return page and cursor.

Success response:

```json
{
  "items": [
    {
      "session_id": "uuid",
      "title": "Summarize quarterly plan",
      "last_key_id": "uuid",
      "last_model_id": "model-id",
      "created_at": "2026-05-30T10:00:00Z",
      "updated_at": "2026-05-30T10:10:00Z"
    }
  ],
  "next_cursor": "opaque-cursor"
}
```

Status codes: `200`, `401`, `500`.

#### 2.3.6 Interface: M03-I03 — Get Conversation Session Detail

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/ai-chat/sessions/{session_id}` |
| Consumer | M02 |

Processing:

1. Validate session through M01.
2. Load session by `session_id`.
3. Verify `owner_user_id = current_user.user_id`.
4. Reject deleted sessions with `SESSION_NOT_FOUND` or `SESSION_FORBIDDEN` according to platform convention.
5. Load messages ordered by `created_at ASC`.
6. Load attachment summaries for messages.
7. Return detail.

Success response:

```json
{
  "session": {
    "session_id": "uuid",
    "title": "Summarize quarterly plan",
    "status": "ACTIVE",
    "last_key_id": "uuid",
    "last_model_id": "model-id",
    "created_at": "2026-05-30T10:00:00Z",
    "updated_at": "2026-05-30T10:10:00Z"
  },
  "messages": [
    {
      "message_id": "uuid",
      "role": "USER",
      "content": "Please summarize this image.",
      "status": "SUBMITTED",
      "key_id": "uuid",
      "model_id": "model-id",
      "created_at": "2026-05-30T10:02:00Z",
      "attachments": [
        {
          "attachment_id": "uuid",
          "mime_type": "image/png",
          "size_bytes": 200000,
          "status": "BOUND"
        }
      ]
    },
    {
      "message_id": "uuid",
      "role": "ASSISTANT",
      "content": "The image appears to show...",
      "status": "COMPLETED",
      "key_id": "uuid",
      "model_id": "model-id",
      "created_at": "2026-05-30T10:02:05Z",
      "token_usage": {
        "input_tokens": 100,
        "output_tokens": 80
      }
    }
  ]
}
```

Status codes: `200`, `401`, `403`, `404`, `500`.

#### 2.3.7 Interface: M03-I04 — Delete Conversation Session

| Field | Value |
|---|---|
| Method | DELETE |
| Path | `/api/v1/ai-chat/sessions/{session_id}` |
| Consumer | M02 |

Processing:

1. Validate session through M01.
2. Load session.
3. Verify ownership.
4. Set `status = DELETED`, `deleted_at = now()`, `updated_at = now()`.
5. Do not immediately physically delete messages or images.
6. Physical cleanup follows retention policy through S02.

Success response:

```json
{
  "session_id": "uuid",
  "status": "DELETED",
  "deleted_at": "2026-05-30T10:20:00Z"
}
```

Status codes: `200`, `401`, `403`, `404`, `409`, `500`.

Idempotency: repeated delete returns final deleted state.

#### 2.3.8 Internal Method: M03-SVC01 — Build Conversation Context

| Field | Value |
|---|---|
| Method Type | Internal service method, not public REST API |
| Consumer | M05 |
| Purpose | Build model input context from session messages and current user message. |

Input:

```json
{
  "session_id": "uuid",
  "current_user_message_id": "uuid",
  "model_id": "model-id",
  "context_limit_tokens": 128000,
  "include_image_attachments": true
}
```

Processing:

1. Verify session is active.
2. Load completed prior messages plus current user message.
3. Exclude failed assistant messages from model context.
4. Preserve chronological order.
5. Include image attachments bound to current user message if requested.
6. Estimate token length using platform estimator.
7. Apply configured truncation strategy to older eligible messages.
8. If still over limit, return `CONTEXT_LIMIT_EXCEEDED`.

Output:

```json
{
  "context_messages": [
    {
      "role": "user",
      "content": "Question text",
      "attachments": []
    },
    {
      "role": "assistant",
      "content": "Prior answer"
    }
  ],
  "truncated": false,
  "estimated_input_tokens": 1200
}
```

#### 2.3.9 Data Design

Entity: `ai_chat_session`

| Field | Type | Constraint |
|---|---|---|
| `session_id` | UUID | Primary key |
| `owner_user_id` | UUID | Required, indexed |
| `team_id` | UUID | Required, indexed |
| `title` | varchar(200) | Required |
| `last_key_id` | UUID | Nullable |
| `last_model_id` | varchar(128) | Nullable |
| `status` | enum | `ACTIVE`, `DELETED` |
| `created_at` | timestamp | Required |
| `updated_at` | timestamp | Required |
| `deleted_at` | timestamp | Nullable |
| `version` | integer | Required for optimistic locking |

Entity: `ai_chat_message`

| Field | Type | Constraint |
|---|---|---|
| `message_id` | UUID | Primary key |
| `session_id` | UUID | Foreign key |
| `owner_user_id` | UUID | Required, indexed |
| `team_id` | UUID | Required, indexed |
| `role` | enum | `USER`, `ASSISTANT` |
| `content` | text | Nullable for failed assistant message |
| `status` | enum | `SUBMITTED`, `GENERATING`, `COMPLETED`, `FAILED` |
| `key_id` | UUID | Required for submitted/generated messages |
| `model_id` | varchar(128) | Required for submitted/generated messages |
| `gateway_request_id` | varchar(128) | Nullable |
| `input_tokens` | integer | Nullable |
| `output_tokens` | integer | Nullable |
| `error_code` | varchar(64) | Nullable |
| `error_message` | varchar(500) | Nullable |
| `created_at` | timestamp | Required |
| `updated_at` | timestamp | Required |

Entity: `ai_chat_image_attachment`

| Field | Type | Constraint |
|---|---|---|
| `attachment_id` | UUID | Primary key |
| `session_id` | UUID | Required |
| `message_id` | UUID | Nullable until bound |
| `owner_user_id` | UUID | Required |
| `team_id` | UUID | Required |
| `storage_uri` | varchar(500) | Required, never directly exposed if private |
| `mime_type` | varchar(64) | Required |
| `size_bytes` | bigint | Required |
| `checksum_sha256` | varchar(64) | Required |
| `status` | enum | `UPLOADED`, `BOUND`, `EXPIRED`, `DELETED` |
| `created_at` | timestamp | Required |
| `expires_at` | timestamp | Required |

Storage:

| Data | Storage |
|---|---|
| Sessions/messages/metadata | Relational database |
| Image binary | Existing secure object storage |
| Hot session cache | Optional; invalidate on message write or delete |
| Full-text search | Not included |

#### 2.3.10 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Create own session | Yes | Yes | Yes |
| List own sessions | Yes | Yes | Yes |
| Load own session | Yes | Yes | Yes |
| Delete own session | Yes | Yes | Yes |
| Load/delete another user's session | No | No | No |
| Read plaintext Key from session | No | No | No |

Granularity: individual-level for session and message content.

#### 2.3.11 Logging Design

| Level | Trigger |
|---|---|
| DEBUG | Context assembly diagnostics in non-production. |
| INFO | Session created/listed/loaded/deleted. |
| WARN | Unauthorized session access. |
| ERROR | Database failure or attachment metadata inconsistency. |
| FATAL | Conversation database unavailable. |

Message content and image URIs must not be written to operational logs by default.

---

### 2.4 M04 — Key & Model Authorization Integration

#### 2.4.1 Scope

M04 exposes safe Key and model authorization information for AI Chat. It reads existing Key, quota, model registry, and model permission data. It does not introduce a new Key administration UI.

#### 2.4.2 Primary Functions

| Function | Description |
|---|---|
| List authorized Keys | Return safe summaries for Keys visible to current user. |
| Mark unavailable Keys | Include disabled/unusable reasons for UI. |
| List permitted models | Return only available models the selected Key can call. |
| Validate Key/model | Internal validation for send, retry, and image upload. |
| Return model capabilities | Provide text/image capability metadata. |
| Protect Key secrecy | Never return Key secret or plaintext credential. |

#### 2.4.3 Interface: M04-I01 — List AI Chat Authorized Keys

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/ai-chat/keys` |
| Consumer | M02 |

Query parameters:

| Parameter | Type | Required | Default |
|---|---|---:|---|
| `include_unavailable` | boolean | No | `true` |

Processing:

1. Validate session through M01.
2. Query Keys owned by or authorized to current user through user-level or team-level grants.
3. Evaluate status, expiry, quota, and model permission count.
4. Build safe summaries.
5. Do not return plaintext Key.
6. Sort by recently used, then name.

Success response:

```json
{
  "items": [
    {
      "key_id": "uuid",
      "key_name": "Marketing Team Key",
      "team_id": "uuid",
      "team_name": "Marketing",
      "status": "ACTIVE",
      "quota_summary": {
        "remaining_quota_display": "Available",
        "quota_exhausted": false
      },
      "available_model_count": 3,
      "selectable": true,
      "unavailable_reason": null
    }
  ]
}
```

Status codes: `200`, `401`, `500`.

#### 2.4.4 Interface: M04-I02 — List Models Permitted by Key

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/ai-chat/keys/{key_id}/models` |
| Consumer | M02 |

Processing:

1. Validate session through M01.
2. Validate user authorization to selected Key.
3. Validate Key status, expiry, and quota availability.
4. Query model permissions for selected Key.
5. Return models that are currently available.
6. Include model capability metadata.

Success response:

```json
{
  "key_id": "uuid",
  "models": [
    {
      "model_id": "model-text-001",
      "model_name": "Enterprise Text Model",
      "status": "AVAILABLE",
      "capabilities": {
        "supports_text": true,
        "supports_image": false,
        "context_limit_tokens": 128000,
        "supported_image_mime_types": [],
        "max_image_size_bytes": null,
        "max_image_count": 0
      }
    },
    {
      "model_id": "model-vision-001",
      "model_name": "Enterprise Vision Model",
      "status": "AVAILABLE",
      "capabilities": {
        "supports_text": true,
        "supports_image": true,
        "context_limit_tokens": 128000,
        "supported_image_mime_types": ["image/png", "image/jpeg", "image/webp"],
        "max_image_size_bytes": 10485760,
        "max_image_count": 5
      }
    }
  ]
}
```

Status codes: `200`, `401`, `403`, `404`, `409`, `429`, `500`.

#### 2.4.5 Interface: M04-I03 — Validate Key and Model for AI Chat

| Field | Value |
|---|---|
| Method | POST |
| Path | `/api/v1/internal/ai-chat/authorization/validate` |
| Consumer | M03, M05 |
| Visibility | Internal service API |

Request body:

```json
{
  "type": "object",
  "required": ["user_id", "team_id", "key_id", "model_id"],
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "team_id": { "type": "string", "format": "uuid" },
    "key_id": { "type": "string", "format": "uuid" },
    "model_id": { "type": "string" },
    "require_image_support": { "type": "boolean", "default": false }
  }
}
```

Processing:

1. Validate user is active.
2. Validate Key exists.
3. Validate user or team is authorized to use Key.
4. Validate Key is active and not expired.
5. Validate Key has available quota.
6. Validate model exists and is available.
7. Validate Key has model permission.
8. If image support is required, validate model supports image and return image limits.
9. Return authorization decision and model capability data.

Success response:

```json
{
  "authorized": true,
  "key_id": "uuid",
  "model_id": "model-vision-001",
  "model_capabilities": {
    "supports_text": true,
    "supports_image": true,
    "context_limit_tokens": 128000,
    "supported_image_mime_types": ["image/png", "image/jpeg"],
    "max_image_size_bytes": 10485760,
    "max_image_count": 5
  }
}
```

Status codes: `200`, `400`, `403`, `404`, `409`, `429`, `500`.

#### 2.4.6 Data Design

M04 reads existing platform data:

| Entity | Required Fields |
|---|---|
| `api_key` | `key_id`, `key_name`, `key_secret_hash`, `owner_user_id`, `team_id`, `status`, `expires_at` |
| `api_key_authorization` | `key_id`, `principal_type`, `principal_id` |
| `api_key_model_permission` | `key_id`, `model_id`, `enabled` |
| `model_registry` | `model_id`, `model_name`, `status`, `supports_text`, `supports_image`, `context_limit_tokens`, image constraints |
| `quota_state` | `key_id`, remaining quota or quota-exhausted flag |

No new database is required for M04.

#### 2.4.7 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| List own/authorized Keys | Yes | Yes | Yes |
| List models for own/authorized Key | Yes | Yes | Yes |
| Validate own/authorized Key and model | Yes | Yes | Yes |
| View Key secret | No | No | No |
| Use disabled/expired/no-quota Key | No | No | No |
| Use model not permitted by Key | No | No | No |

Credential scoping: only `key_id` travels through AI Chat APIs; credential material remains inside the existing Gateway/key-management subsystem.

#### 2.4.8 Logging Design

| Level | Trigger |
|---|---|
| DEBUG | Key/model filter diagnostics in non-production. |
| INFO | Key list/model list returned; authorization validated. |
| WARN | Unauthorized Key or model access attempt. |
| ERROR | Key registry, model registry, or quota service failure. |
| FATAL | Authorization service unavailable. |

Never log Key secrets. Log `key_id` and `model_id` only.

---

### 2.5 M05 — AI Chat Gateway Invocation Layer

#### 2.5.1 Scope

M05 converts AI Chat user actions into Gateway inference requests. It validates session ownership, Key authorization, model permission, image capability, and context constraints; persists messages; calls the existing LLM API Gateway; persists successful or failed assistant response state; and correlates usage records.

#### 2.5.2 Primary Functions

| Function | Description |
|---|---|
| Upload image | Accept image attachments when model supports image input. |
| Send message | Submit text and optional images to the Gateway. |
| Revalidate Key/model | Call M04-I03 before execution. |
| Persist messages | Store user message and assistant placeholder. |
| Build context | Call M03-SVC01 for ordered context. |
| Invoke Gateway | Use existing Gateway path only. |
| Persist result | Store assistant output, token usage, Gateway request ID. |
| Persist failure | Store assistant failure state and safe error code. |
| Retry generation | Re-run failed assistant generation with original user message and attachments. |

#### 2.5.3 Interface: M05-I01 — Upload Image Attachment

| Field | Value |
|---|---|
| Method | POST |
| Path | `/api/v1/ai-chat/sessions/{session_id}/attachments/images` |
| Content Type | `multipart/form-data` |
| Consumer | M02 |

Form fields:

| Field | Type | Required | Validation |
|---|---|---:|---|
| `key_id` | UUID | Yes | User must be authorized to Key. |
| `model_id` | string | Yes | Model must be permitted by Key and support image input. |
| `image_file` | binary | Yes | MIME type and size must be supported. |

Processing:

1. Validate session through M01.
2. Load session through M03 and verify ownership.
3. Call M04-I03 with `require_image_support = true`.
4. Validate image MIME type and size against model/platform configuration.
5. Store image binary in secure object storage.
6. Create `ai_chat_image_attachment` with status `UPLOADED`.
7. Return attachment summary.

Success response:

```json
{
  "attachment_id": "uuid",
  "session_id": "uuid",
  "mime_type": "image/png",
  "size_bytes": 200000,
  "status": "UPLOADED",
  "created_at": "2026-05-30T10:00:00Z",
  "expires_at": "2026-06-06T10:00:00Z"
}
```

Status codes: `201`, `400`, `401`, `403`, `404`, `409`, `413`, `500`.

Idempotency: required. Same idempotency key and same image checksum returns same attachment.

#### 2.5.4 Interface: M05-I02 — Send Chat Message

| Field | Value |
|---|---|
| Method | POST |
| Path | `/api/v1/ai-chat/sessions/{session_id}/messages` |
| Consumer | M02 |

Request body:

```json
{
  "type": "object",
  "required": ["key_id", "model_id"],
  "properties": {
    "key_id": { "type": "string", "format": "uuid" },
    "model_id": { "type": "string" },
    "content": { "type": "string", "maxLength": 20000 },
    "image_attachment_ids": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" },
      "default": []
    }
  },
  "additionalProperties": false
}
```

Validation: `content` must be non-empty after trimming, or `image_attachment_ids` must contain at least one item.

Processing:

1. Validate session through M01.
2. Load session and verify ownership.
3. Validate request body.
4. Call M04-I03. Set `require_image_support = true` when image attachments are present.
5. Validate attachments belong to current user/session, are `UPLOADED`, are not expired, and do not exceed model max image count.
6. Start transaction.
7. Create `USER` message with status `SUBMITTED`.
8. Bind image attachments to user message and set status `BOUND`.
9. Create `ASSISTANT` message with status `GENERATING`.
10. Create `ai_chat_invocation` with status `GENERATING`.
11. Update session `last_key_id`, `last_model_id`, `updated_at`, and optional title preview.
12. Commit transaction.
13. Call M03-SVC01 to build context.
14. If context exceeds limit after policy handling, update assistant message and invocation to `FAILED` with `CONTEXT_LIMIT_EXCEEDED`, then return HTTP 200 with failed assistant state.
15. Invoke existing LLM API Gateway with `request_origin = AI_CHAT`, `session_id`, `user_message_id`, `assistant_message_id`, `key_id`, `model_id`, and context.
16. On Gateway success, update assistant message and invocation to `COMPLETED`, store assistant content, token usage, latency, and `gateway_request_id`.
17. On Gateway failure after accepted message persistence, update assistant message and invocation to `FAILED` with normalized safe error code, then return HTTP 200 with failed assistant state.
18. Ensure usage metadata is emitted to existing Gateway usage flow.

Success response for completed generation:

```json
{
  "session": {
    "session_id": "uuid",
    "title": "Summarize quarterly plan",
    "last_key_id": "uuid",
    "last_model_id": "model-vision-001",
    "updated_at": "2026-05-30T10:03:00Z"
  },
  "user_message": {
    "message_id": "uuid",
    "role": "USER",
    "content": "What does this image show?",
    "status": "SUBMITTED",
    "key_id": "uuid",
    "model_id": "model-vision-001",
    "created_at": "2026-05-30T10:03:00Z",
    "attachments": [
      {
        "attachment_id": "uuid",
        "mime_type": "image/png",
        "size_bytes": 200000,
        "status": "BOUND"
      }
    ]
  },
  "assistant_message": {
    "message_id": "uuid",
    "role": "ASSISTANT",
    "content": "The image shows...",
    "status": "COMPLETED",
    "key_id": "uuid",
    "model_id": "model-vision-001",
    "gateway_request_id": "gw-request-id",
    "token_usage": {
      "input_tokens": 120,
      "output_tokens": 90
    },
    "created_at": "2026-05-30T10:03:05Z"
  }
}
```

Success response for persisted generation failure:

```json
{
  "session": {
    "session_id": "uuid",
    "updated_at": "2026-05-30T10:03:00Z"
  },
  "user_message": {
    "message_id": "uuid",
    "role": "USER",
    "status": "SUBMITTED"
  },
  "assistant_message": {
    "message_id": "uuid",
    "role": "ASSISTANT",
    "content": null,
    "status": "FAILED",
    "error_code": "MODEL_UNAVAILABLE",
    "error_message": "The selected model is currently unavailable.",
    "retryable": true
  }
}
```

Status codes:

| Status | Meaning |
|---:|---|
| 200 | Message accepted; assistant completed or failed with persisted state. |
| 400 | Invalid input before persistence. |
| 401 | Not authenticated. |
| 403 | Session, Key, or model forbidden before persistence. |
| 404 | Session, Key, model, or attachment not found before persistence. |
| 409 | Key/model unavailable or idempotency conflict before persistence. |
| 429 | Quota or rate limit rejected before persistence. |
| 500 | Server error before safe persistence or persistence failure. |
| 502 | Gateway provider error before safe persistence. |
| 504 | Gateway timeout before safe persistence. |

Idempotency and concurrency:

| Concern | Design |
|---|---|
| Duplicate send | `Idempotency-Key` required. Same key and same body returns same message pair. |
| Same key, different body | Return `IDEMPOTENCY_CONFLICT`. |
| Concurrent sends in same session | Allowed; context order follows committed `created_at`. |
| Session deleted during send | If deleted before transaction, reject. If deleted after transaction, complete persistence but keep hidden in UI. |
| Gateway retry | Internal retries only if safe; user-visible retry uses M05-I03. |

#### 2.5.5 Interface: M05-I03 — Retry Failed Assistant Message

| Field | Value |
|---|---|
| Method | POST |
| Path | `/api/v1/ai-chat/sessions/{session_id}/messages/{assistant_message_id}/retry` |
| Consumer | M02 |

Request body:

```json
{
  "type": "object",
  "additionalProperties": false
}
```

Processing:

1. Validate session through M01.
2. Verify session ownership.
3. Load assistant message and verify status is `FAILED`.
4. Find paired user message.
5. Revalidate Key/model through M04-I03.
6. Revalidate attachments if present.
7. Set assistant message and invocation to `GENERATING`.
8. Build context through M03-SVC01.
9. Invoke Gateway.
10. Update assistant message to `COMPLETED` or `FAILED`.
11. Return assistant message state.

Status codes: `200`, `400`, `401`, `403`, `404`, `409`, `429`, `500`, `502`, `504`.

Idempotency: required. Only one active retry is allowed per assistant message; concurrent retries return `409`.

#### 2.5.6 Data Design

Entity: `ai_chat_invocation`

| Field | Type | Constraint |
|---|---|---|
| `invocation_id` | UUID | Primary key |
| `session_id` | UUID | Required |
| `user_message_id` | UUID | Required |
| `assistant_message_id` | UUID | Required |
| `user_id` | UUID | Required |
| `team_id` | UUID | Required |
| `key_id` | UUID | Required |
| `model_id` | varchar(128) | Required |
| `gateway_request_id` | varchar(128) | Nullable until Gateway returns |
| `request_origin` | varchar(32) | Always `AI_CHAT` |
| `status` | enum | `GENERATING`, `COMPLETED`, `FAILED` |
| `error_code` | varchar(64) | Nullable |
| `latency_ms` | integer | Nullable |
| `created_at` | timestamp | Required |
| `updated_at` | timestamp | Required |

M05 also writes M03-owned message/attachment tables through controlled repository/service methods.

#### 2.5.7 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Upload image to own session with valid model | Yes | Yes | Yes |
| Send text message to own session | Yes | Yes | Yes |
| Send image message with image-capable model | Yes | Yes | Yes |
| Retry own failed assistant message | Yes | Yes | Yes |
| Send message to another user's session | No | No | No |
| Use unauthorized Key/model | No | No | No |
| Bypass Gateway | No | No | No |

Granularity: individual-level for sessions/messages/images; Key-level for credentials; Key-model-level for model access.

#### 2.5.8 Logging Design

| Level | Trigger |
|---|---|
| DEBUG | Context token estimates in non-production. |
| INFO | Message submitted, Gateway invocation completed, retry completed. |
| WARN | Validation rejection, rate limit, retryable Gateway failure. |
| ERROR | Gateway failure, persistence failure, image storage failure. |
| FATAL | Invocation layer unavailable. |

Structured log example:

```json
{
  "timestamp": "2026-05-30T10:03:05Z",
  "level": "INFO",
  "trace_id": "trace-uuid",
  "module": "M05",
  "user_id": "uuid",
  "team_id": "uuid",
  "action": "AI_CHAT_GATEWAY_INVOCATION_COMPLETED",
  "resource_type": "AI_CHAT_INVOCATION",
  "resource_id": "invocation-uuid",
  "payload_summary": {
    "session_id": "session-uuid",
    "key_id": "key-uuid",
    "model_id": "model-vision-001",
    "has_image": true,
    "image_count": 1,
    "input_tokens": 120,
    "output_tokens": 90
  },
  "result": "SUCCESS",
  "latency_ms": 3200
}
```

Do not log prompts, assistant answers, image binary/base64, Key secrets, authorization headers, or raw provider errors.

---

### 2.6 M06 — Usage Analytics & Consumption Detail Integration

#### 2.6.1 Scope

M06 exposes AI Chat-originated usage records through the existing analytics/consumption detail module. It does not create a new reporting module.

#### 2.6.2 Primary Functions

| Function | Description |
|---|---|
| Store AI Chat origin | Ensure usage records contain `request_origin = AI_CHAT`. |
| Query usage details | Return AI Chat usage through existing analytics endpoint. |
| Enforce scope | Admin sees platform-level; Team Manager sees own team. |
| Exclude conversation content | Usage records contain metadata and consumption only. |

#### 2.6.3 Interface: M06-I01 — Query Usage Details

| Field | Value |
|---|---|
| Method | GET |
| Path | `/api/v1/analytics/usage-details` |
| Consumer | Existing analytics UI |

Query parameters:

| Parameter | Type | Required | Default | Validation |
|---|---|---:|---|---|
| `request_origin` | string | No | All | Use `AI_CHAT` for AI Chat requests. |
| `team_id` | UUID | No | Current scope | Admin may specify; Team Manager limited to own team. |
| `user_id` | UUID | No | All in scope | Must be within caller scope. |
| `key_id` | UUID | No | All in scope | Must be within caller scope. |
| `model_id` | string | No | All | Valid model ID. |
| `start_time` | timestamp | Yes | N/A | ISO-8601. |
| `end_time` | timestamp | Yes | N/A | Must be after start. |
| `limit` | integer | No | 50 | 1-500. |
| `cursor` | string | No | None | Opaque cursor. |

Processing:

1. Validate session through M01.
2. Resolve caller role.
3. Apply scope:
   - System Administrator: platform-level.
   - Team Manager: own team only.
   - Normal User: default deny unless existing analytics policy grants access.
4. Query usage records matching filters.
5. Return metadata and consumption details only.
6. Do not return prompt content, assistant content, images, or Key secrets.

Success response:

```json
{
  "items": [
    {
      "usage_id": "uuid",
      "request_origin": "AI_CHAT",
      "gateway_request_id": "gw-request-id",
      "session_id": "uuid",
      "user_id": "uuid",
      "team_id": "uuid",
      "key_id": "uuid",
      "model_id": "model-vision-001",
      "input_tokens": 120,
      "output_tokens": 90,
      "cost_amount": "0.0123",
      "currency": "USD",
      "status": "SUCCESS",
      "latency_ms": 3200,
      "created_at": "2026-05-30T10:03:05Z"
    }
  ],
  "next_cursor": "opaque-cursor"
}
```

Status codes: `200`, `400`, `401`, `403`, `500`.

#### 2.6.4 Data Design

Existing entity: `gateway_usage_record`

| Field | Type | AI Chat Requirement |
|---|---|---|
| `usage_id` | UUID | Required |
| `request_origin` | varchar(32) | `AI_CHAT` for AI Chat calls |
| `gateway_request_id` | varchar(128) | Required |
| `session_id` | UUID | Required for AI Chat |
| `user_id` | UUID | Required |
| `team_id` | UUID | Required |
| `key_id` | UUID | Required |
| `model_id` | varchar(128) | Required |
| `input_tokens` | integer | Required if available |
| `output_tokens` | integer | Required if available |
| `cost_amount` | decimal | Existing platform logic |
| `currency` | varchar(8) | Existing platform logic |
| `status` | enum | `SUCCESS`, `FAILED` |
| `latency_ms` | integer | Optional |
| `created_at` | timestamp | Required |

#### 2.6.5 Permission Design

| Action | System Administrator | Team Manager | Normal User |
|---|---:|---:|---:|
| Query platform AI Chat usage | Yes | No | No |
| Query own team AI Chat usage | Yes | Yes | No by default |
| Query other team usage | Yes | No | No |
| View message content through analytics | No | No | No |
| View Key secret through analytics | No | No | No |

Granularity: platform-level for System Administrator, team-level for Team Manager.

#### 2.6.6 Logging Design

| Level | Trigger |
|---|---|
| DEBUG | Query diagnostics in non-production. |
| INFO | Usage query executed. |
| WARN | Out-of-scope analytics query attempt. |
| ERROR | Analytics query failure. |
| FATAL | Analytics service unavailable. |

Do not log message content, image data, or Key secrets.

---

## 3. Backend Service Designs

### 3.1 S01 — AI Chat Usage Event Consumer

#### Purpose

Consume existing Gateway usage events for requests where `request_origin = AI_CHAT`, correlate them to AI Chat invocation/message records, and ensure usage details are available in the existing analytics module.

#### Business Processing Logic

1. Consume event from existing Gateway usage event stream.
2. Validate event schema.
3. If `request_origin != AI_CHAT`, ignore.
4. Resolve `gateway_request_id` and optional `assistant_message_id`.
5. Update `ai_chat_invocation` token usage, latency, status, and error code.
6. Update `ai_chat_message` token fields if `assistant_message_id` is available.
7. Confirm existing analytics usage record is persisted or ready for query.
8. Acknowledge event.

#### Service Interface

Input topic:

```text
gateway.usage.events
```

Input event schema:

```json
{
  "type": "object",
  "required": [
    "gateway_request_id",
    "request_origin",
    "user_id",
    "team_id",
    "key_id",
    "model_id",
    "status",
    "created_at"
  ],
  "properties": {
    "gateway_request_id": { "type": "string" },
    "request_origin": { "type": "string" },
    "session_id": { "type": "string", "format": "uuid" },
    "assistant_message_id": { "type": "string", "format": "uuid" },
    "user_id": { "type": "string", "format": "uuid" },
    "team_id": { "type": "string", "format": "uuid" },
    "key_id": { "type": "string", "format": "uuid" },
    "model_id": { "type": "string" },
    "input_tokens": { "type": "integer" },
    "output_tokens": { "type": "integer" },
    "cost_amount": { "type": "string" },
    "currency": { "type": "string" },
    "status": { "type": "string", "enum": ["SUCCESS", "FAILED"] },
    "latency_ms": { "type": "integer" },
    "error_code": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" }
  }
}
```

Outputs:

| Destination | Purpose |
|---|---|
| `ai_chat_invocation` | Update invocation status and usage metadata. |
| `ai_chat_message` | Update token fields for assistant message. |
| Existing analytics store | Ensure AI Chat records are queryable. |
| Dead-letter queue | Store events that fail validation or exceed retries. |

#### High Concurrency

| Concern | Design |
|---|---|
| Partitioning | Partition by `gateway_request_id` or `team_id`. |
| Duplicate events | Use `gateway_request_id` as idempotency key. |
| Database writes | Use upsert or optimistic updates. |
| Backpressure | Pause consumption when DB latency or queue lag exceeds thresholds. |
| Connection pooling | Use bounded pools. |

#### High Availability

| Area | Design |
|---|---|
| Health check | Report queue lag, DB connectivity, DLQ rate. |
| Graceful shutdown | Stop polling, finish in-flight event, commit offset. |
| Retry | Exponential backoff for transient failures. |
| Circuit breaker | Open on repeated downstream failures. |
| DLQ | Invalid or repeatedly failing events go to DLQ. |
| Recovery | Replay from event stream by offset. |

---

### 3.2 S02 — AI Chat Retention Cleanup Worker

#### Purpose

Apply platform retention policy to deleted conversations and expired image attachments. This supports the rule that deleted conversations disappear from frontend immediately while backend retention follows platform policy.

#### Business Processing Logic

1. Run on configured schedule.
2. Find `ai_chat_session` rows where `status = DELETED` and `deleted_at` is older than configured retention.
3. Apply platform deletion policy: physical delete, anonymize, or archive.
4. Find `ai_chat_image_attachment` rows where `expires_at < now()` and status is not `DELETED`.
5. Delete or expire object storage file.
6. Update attachment status to `DELETED`.
7. Emit audit log and metrics.

#### Service Interface

Scheduled job configuration:

```json
{
  "retention_policy_name": "platform_default_ai_chat_retention",
  "batch_size": 500,
  "max_runtime_seconds": 1800,
  "dry_run": false
}
```

Outputs:

| Destination | Purpose |
|---|---|
| Conversation database | Update/delete expired records. |
| Object storage | Delete expired image binaries. |
| Audit log | Record retention actions. |
| Metrics | Record processed/deleted counts. |

#### High Concurrency

| Concern | Design |
|---|---|
| Large batches | Process bounded batches. |
| Lock contention | Use row locks or `SKIP LOCKED` equivalent. |
| Multiple workers | Safe if each row is locked before processing. |
| Object store throttling | Bounded concurrency and retry. |

#### High Availability

| Area | Design |
|---|---|
| Health check | Last successful run, failure count, DLQ count. |
| Graceful shutdown | Complete current batch then stop. |
| Retry | Exponential backoff for object-store and DB errors. |
| DLQ | Records failing repeated cleanup go to maintenance queue. |
| Idempotency | Deleting already-deleted objects is treated as success. |

---

### 3.3 S03 — AI Chat Idempotency Record Cleanup Worker

#### Purpose

Clean expired idempotency records used by session creation, image upload, message send, and retry APIs.

#### Business Processing Logic

1. Run on configured schedule.
2. Find idempotency records older than configured TTL.
3. Delete expired records in bounded batches.
4. Emit cleanup metrics.

#### Service Interface

Scheduled job; no user input.

Outputs:

| Destination | Purpose |
|---|---|
| Idempotency store | Delete expired records. |
| Metrics | Record cleanup count and latency. |

#### High Concurrency and Availability

| Area | Design |
|---|---|
| Batch deletion | Small bounded batches to reduce lock contention. |
| Concurrent API use | Delete only records past TTL. |
| Retry | Retry transient store errors. |
| Graceful shutdown | Stop after current batch. |
| Idempotency | Repeated cleanup is safe. |

---

## 4. Cross-Module Data and Permission Summary

### 4.1 ER-Style Relationship Summary

```text
User 1 ─── N AIChatSession
Team 1 ─── N AIChatSession
AIChatSession 1 ─── N AIChatMessage
AIChatSession 1 ─── N AIChatImageAttachment
AIChatMessage 1 ─── N AIChatImageAttachment
AIChatMessage 1 ─── 0..1 AIChatInvocation
APIKey 1 ─── N AIChatMessage
Model 1 ─── N AIChatMessage
GatewayUsageRecord N ─── 1 APIKey
GatewayUsageRecord N ─── 1 Model
GatewayUsageRecord N ─── 1 User
GatewayUsageRecord N ─── 1 Team
```

### 4.2 Cross-Module Permission Matrix

| Resource / Action | System Administrator | Team Manager | Normal User | Enforcement Module |
|---|---:|---:|---:|---|
| Access AI Chat | Yes | Yes | Yes | M01, M02 |
| View own/authorized Keys | Yes | Yes | Yes | M04 |
| View Key secret | No | No | No | M04 |
| Select authorized Key | Yes | Yes | Yes | M04, M05 |
| Select model permitted by Key | Yes | Yes | Yes | M04, M05 |
| Send message in own session | Yes | Yes | Yes | M03, M05 |
| Upload image in own session | Yes | Yes | Yes, if model supports image | M04, M05 |
| View own history | Yes | Yes | Yes | M03 |
| Delete own history | Yes | Yes | Yes | M03 |
| View another user's history | No | No | No | M03 |
| Query platform AI Chat usage | Yes | No | No | M06 |
| Query own team AI Chat usage | Yes | Yes | No by default | M06 |
| Query other team usage | Yes | No | No | M06 |
| Bypass Gateway | No | No | No | M05 |

### 4.3 Common Logging Schema

```json
{
  "timestamp": "2026-05-30T10:00:00Z",
  "level": "INFO",
  "trace_id": "trace-uuid",
  "module": "M05",
  "user_id": "uuid",
  "team_id": "uuid",
  "action": "ACTION_NAME",
  "resource_type": "RESOURCE_TYPE",
  "resource_id": "resource-id",
  "payload_summary": {},
  "result": "SUCCESS",
  "error_code": null,
  "latency_ms": 100
}
```

Sensitive data rules:

| Data Type | Logging Rule |
|---|---|
| API Key secret | Never log. |
| Authorization token/session cookie | Never log. |
| User prompt content | Do not log by default. |
| Assistant response content | Do not log by default. |
| Image binary/base64 | Never log. |
| Image storage URI | Mask or hash. |
| Provider raw error | Sanitize before logging. |
| User ID / team ID / Key ID / model ID | Allowed for audit and traceability. |

### 4.4 Interface Index

| Interface ID | Method | Path | Owner | Consumed By |
|---|---|---|---|---|
| M01-I01 | GET | `/api/v1/platform/session/current` | M01 | M02-M06 |
| M03-I01 | POST | `/api/v1/ai-chat/sessions` | M03 | M02 |
| M03-I02 | GET | `/api/v1/ai-chat/sessions` | M03 | M02 |
| M03-I03 | GET | `/api/v1/ai-chat/sessions/{session_id}` | M03 | M02 |
| M03-I04 | DELETE | `/api/v1/ai-chat/sessions/{session_id}` | M03 | M02 |
| M03-SVC01 | Internal | Build conversation context | M03 | M05 |
| M04-I01 | GET | `/api/v1/ai-chat/keys` | M04 | M02 |
| M04-I02 | GET | `/api/v1/ai-chat/keys/{key_id}/models` | M04 | M02 |
| M04-I03 | POST | `/api/v1/internal/ai-chat/authorization/validate` | M04 | M03, M05 |
| M05-I01 | POST | `/api/v1/ai-chat/sessions/{session_id}/attachments/images` | M05 | M02 |
| M05-I02 | POST | `/api/v1/ai-chat/sessions/{session_id}/messages` | M05 | M02 |
| M05-I03 | POST | `/api/v1/ai-chat/sessions/{session_id}/messages/{assistant_message_id}/retry` | M05 | M02 |
| M06-I01 | GET | `/api/v1/analytics/usage-details` | M06 | Existing analytics UI |
