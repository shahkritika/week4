# Capstone Project Brief: CloudCart Microservices Platform

**Project Name:** CloudCart — Scalable Microservices E-Commerce & Inventory Management  
**Author:** Kritika Shah Halwai  
**Programme:** Full-Stack Developer Internship — Week 4 Capstone  
**Target Completion:** Day 23–24  

---

## 1. Executive Summary & Problem Statement
Traditional monolithic e-commerce platforms suffer from single points of failure, tangled database dependencies, and severe deployment friction. Scaling product catalog reads requires scaling the entire monolith, increasing cloud expenses and deployment risks.

**CloudCart** resolves these operational bottlenecks by implementing a modern, loosely coupled **microservices architecture** consisting of:
1. **Authentication & Identity Service**: Dedicated user management, role-based authorization, and secure JWT generation.
2. **Inventory & Catalog Service**: High-speed product catalog with in-memory Redis caching (60s TTL), stock adjustment, and token-based write protection.
3. **API Gateway & Correlation Tracer**: Ingress routing with universal `X-Request-ID` telemetry.
4. **React Management Console**: Modern, responsive user dashboard providing real-time inventory visualization, stock updates, user authentication, and cache metrics.

---

## 2. Key Objectives & Success Metrics

| Goal | Success Criteria | Verification Method |
| :--- | :--- | :--- |
| **Data Isolation** | Complete database per service pattern (`auth.db` & `inventory.db` / PostgreSQL instances) | Zero cross-database foreign keys; strict API boundary enforcement |
| **Authentication Security** | Encrypted password storage (SHA-256 with salt) and RFC 7519 compliant JWT tokens | Automated failed-auth test cases (invalid password, forged tokens) |
| **High Read Throughput** | Sub-millisecond response latency on cached catalog reads | Redis cache hit verification with 60s TTL and cache invalidation on write |
| **Observability** | Universal distributed tracing via `X-Request-ID` correlation headers | End-to-end request logging across Gateway, Inventory, and Auth services |
| **Portability** | Multi-container Docker Compose deployment | Entire stack boots cleanly via `docker compose up` in under 3 minutes |

---

## 3. Technology Stack

* **Backend Framework:** FastAPI (Python 3.12) with asynchronous ASGI handling
* **Authentication:** JSON Web Tokens (PyJWT), SHA-256 password salting
* **Databases:** PostgreSQL 15 (Docker) / SQLite 3 (Local testing)
* **Caching Layer:** Redis 7 (In-Memory Key-Value with TTL)
* **Frontend:** React 18 / Modern Single Page Application with Axios/Fetch
* **Testing & CI:** Pytest, Unittest, Flake8, GitHub Actions
* **DevOps & Containers:** Docker, Docker Compose, Swagger/OpenAPI, Postman Collection

