# Capstone Repository Structure & Architecture Blueprint

**Project:** CloudCart Microservices Architecture  

## 1. Monorepo Directory Layout

```
Week4/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automated CI/CD pipeline running pytest on push/PR
├── Day19_Microservices_Architecture/
│   ├── microservices_design_note.md # One-page architectural specification
│   └── services/
│       ├── auth_service/          # Autonomous Auth service (Port 8001)
│       └── inventory_service/     # Autonomous Inventory service (Port 8002)
├── Day20_Service_Communication_and_Caching/
│   ├── redis_mongodb_awareness_note.md # Database selection & caching strategies
│   ├── auth_service/              # Auth service with X-Request-ID logging
│   ├── inventory_service/         # Inventory service with token validation & Redis 60s cache
│   └── gateway.py                 # API Gateway routing & header correlation
├── Day21_Testing_and_Docker/
│   ├── tests/
│   │   └── test_services.py       # 8 unit & API integration test cases
│   ├── run_tests.py               # Test runner with pass/fail reporting
│   ├── docker-compose.yml         # Multi-service container orchestration
│   ├── auth_service/Dockerfile    # Multi-stage image build for Auth service
│   └── inventory_service/Dockerfile # Multi-stage image build for Inventory service
├── Day22_CI_CD_and_Capstone_Planning/
│   ├── .github/workflows/ci.yml   # Continuous integration definition
│   └── capstone_planning/
│       ├── capstone_brief.md      # Project overview and business goals
│       ├── ticket_list.md         # Agile sprint tickets, epics & estimates
│       └── repo_architecture.md   # Architectural design and repository layout
├── Day23_Capstone_Build/
│   ├── backend/
│   │   ├── auth_service/          # Production Auth API (FastAPI)
│   │   └── inventory_service/     # Production Inventory API (FastAPI + Redis)
│   ├── frontend/                  # React / Modern Interactive Dashboard
│   ├── postman_collection.json    # Ready-to-import Postman API collection
│   └── docker-compose.yml         # Capstone production compose orchestration
└── Day24_Polish_Demo_and_Retro/
    ├── README.md                  # 5-minute quickstart guide
    ├── demo_script.md             # 10-minute presentation & demonstration flow
    └── retrospective.md           # Engineering lessons learned & reflections
```

---

## 2. Sequence Diagram: Inter-Service Authenticated Write

```
[User / React UI]      [API Gateway]     [Inventory Svc]      [Auth Svc]        [Redis Cache]
       |                      |                  |                  |                  |
       | 1. POST /items       |                  |                  |                  |
       | Bearer <JWT>         |                  |                  |                  |
       |--------------------->|                  |                  |                  |
       |                      | 2. Inject X-Req  |                  |                  |
       |                      |----------------->|                  |                  |
       |                      |                  | 3. GET /verify   |                  |
       |                      |                  |    Bearer <JWT>  |                  |
       |                      |                  |----------------->|                  |
       |                      |                  |                  |                  |
       |                      |                  | 4. 200 OK (User) |                  |
       |                      |                  |<-----------------|                  |
       |                      |                  |                                     |
       |                      |                  | 5. Insert Item into inventory.db    |
       |                      |                  |                                     |
       |                      |                  | 6. Invalidate Cache                 |
       |                      |                  |------------------------------------>|
       |                      |                  |                                     |
       |                      | 7. 201 Created   |                                     |
       |                      |<-----------------|                                     |
       | 8. 201 Response      |                  |                                     |
       |<---------------------|                  |                  |                  |
```

