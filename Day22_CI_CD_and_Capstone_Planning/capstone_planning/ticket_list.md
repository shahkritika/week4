# Capstone Agile Ticket List & Sprint Backlog

**Project:** CloudCart Microservices Platform  
**Sprint Cycle:** Week 4 Sprint (Days 22–24)  
**Lead Engineer:** Kritika Shah Halwai  

---

## Sprint Summary & Story Point Allocation

| Epic ID | Epic Name | Story Points | Status |
| :--- | :--- | :---: | :---: |
| **EPIC-01** | Core Authentication & Security Service | 8 | Done |
| **EPIC-02** | Inventory Catalog & Stock Service | 8 | Done |
| **EPIC-03** | Distributed Communication, Gateway & Caching | 8 | Done |
| **EPIC-04** | Quality Assurance, Automated Tests & CI | 5 | Done |
| **EPIC-05** | React Client & Postman Documentation | 5 | Done |
| **EPIC-06** | Dockerization & Deployment Operations | 5 | Done |
| **TOTAL** | | **39 SP** | **Complete** |

---

## Detailed User Stories & Engineering Tickets

### Epic 1: Authentication & Security (AUTH)
* **AUTH-101: User Registration Endpoint**
  * *Type:* Story | *Priority:* High | *Estimate:* 3 SP
  * *Description:* As a new user, I want to register with my username, email, and password so that I can access protected endpoints.
  * *Acceptance Criteria:* Return 201 Created on valid input; return 400 Bad Request if username or email already exists; passwords hashed before storage.
* **AUTH-102: JWT Login & Issue Token**
  * *Type:* Story | *Priority:* High | *Estimate:* 3 SP
  * *Description:* As a registered user, I want to authenticate with credentials and receive a JWT token.
  * *Acceptance Criteria:* Return 200 OK with `access_token` and `token_type: bearer`; return 401 Unauthorized for incorrect password.
* **AUTH-103: Inter-Service Token Verification Endpoint**
  * *Type:* Story | *Priority:* Critical | *Estimate:* 2 SP
  * *Description:* As downstream microservices, I want to verify JWT authenticity via `GET /verify-token`.
  * *Acceptance Criteria:* Return decoded payload on valid token; return 401 Unauthorized on invalid/expired token.

### Epic 2: Inventory & Catalog Service (INV)
* **INV-201: Inventory Data Model & Schema Migration**
  * *Type:* Task | *Priority:* High | *Estimate:* 2 SP
  * *Description:* Create `items` table with columns: `id`, `sku`, `name`, `description`, `price`, `stock_quantity`, `category`.
  * *Acceptance Criteria:* Auto-seeds sample items upon startup if empty; unique constraint on `sku`.
* **INV-202: Public Catalog Browsing (GET /items)**
  * *Type:* Story | *Priority:* High | *Estimate:* 3 SP
  * *Description:* As a customer/client, I want to fetch all available inventory items.
  * *Acceptance Criteria:* Fast response returning array of JSON items; supports category filtering.
* **INV-203: Authenticated Item Creation & Stock Update**
  * *Type:* Story | *Priority:* High | *Estimate:* 3 SP
  * *Description:* As an authorized warehouse manager, I want to add new products and adjust stock quantities.
  * *Acceptance Criteria:* Requires valid JWT token; validates token with Auth Service; updates stock with atomic boundary guard.

### Epic 3: Communication & Redis Caching (COMM)
* **COMM-301: Distributed Correlation ID Middleware (X-Request-ID)**
  * *Type:* Task | *Priority:* High | *Estimate:* 3 SP
  * *Description:* Implement ASGI middleware that captures or injects `X-Request-ID` and includes it in all structured log lines and response headers.
* **COMM-302: Redis Read Caching on GET /items (60s TTL)**
  * *Type:* Story | *Priority:* High | *Estimate:* 5 SP
  * *Description:* Cache inventory items in Redis with a 60-second TTL.
  * *Acceptance Criteria:* First call results in Cache Miss and DB query; subsequent calls within 60s return Cache Hit; cache invalidated when new item is created.

### Epic 4: Quality & Automated Testing (QA)
* **QA-401: 8 Automated Unit & API Integration Tests**
  * *Type:* Task | *Priority:* Critical | *Estimate:* 5 SP
  * *Description:* Write comprehensive automated test suite covering health, registration, duplicate checks, login, failed-auth cases, token verification, and inventory CRUD.

### Epic 5: React Frontend & Client Experience (FE)
* **FE-501: Responsive React Management Console**
  * *Type:* Story | *Priority:* High | *Estimate:* 5 SP
  * *Description:* Provide modern UI for authentication, live catalog viewing, cache inspection, and item creation.

