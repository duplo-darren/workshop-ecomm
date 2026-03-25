# AnyCompany E-Commerce Platform v2

This repository contains AnyCompany's decomposed e-commerce microservices — the result of breaking apart a legacy monolithic application into independently deployable services. The microservices are complete and containerized. The current phase of work is **deploying these services to AWS** using Amazon EKS for compute, Amazon RDS for managed PostgreSQL databases, and Amazon S3 for product image storage.

---

## Project Context

AnyCompany is migrating from a single monolithic e-commerce application to a microservices architecture. The microservice code has been written and validated locally. The next milestone is cloud deployment: provisioning infrastructure, pushing container images to ECR, and running the services on EKS with RDS backends.

A data migration script (`migrate.py`) is included in this repository to move existing data from the monolith's database to the new per-service databases. This script is already present on the system running the monolith and should be run as part of the cutover process.

---

## Architecture

The application follows a **database-per-service** pattern with three Flask-based services:

| Service | Port | Responsibility |
|---|---|---|
| **Frontend** | 8000 | UI, API Gateway / BFF — aggregates data from backend services |
| **Catalog** | 8001 | Product catalog — create, read, update, delete products |
| **Inventory** | 8002 | Stock tracking — manages quantity per product |

Each backend service owns its own PostgreSQL database. Product images — previously stored on the monolith's local filesystem — are offloaded to **Amazon S3 (public access)** to eliminate local disk dependency and support horizontal scaling of the Catalog and Frontend pods.

```
                    ┌─────────────────┐
                    │    Frontend     │  ← Entry point (port 8000)
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌────────────────┐           ┌─────────────────┐
     │    Catalog     │           │    Inventory    │
     │  (port 8001)   │           │  (port 8002)    │
     └───────┬────────┘           └────────┬────────┘
             │                             │
     ┌───────▼────────┐           ┌────────▼────────┐
     │  RDS Postgres  │           │  RDS Postgres   │
     │  (catalog db)  │           │  (inventory db) │
     └────────────────┘           └─────────────────┘

              ┌──────────────────────────────────┐
              │   Amazon S3 (public access)      │
              │   Product image storage          │
              │   ← Catalog (upload/manage)      │
              │   ← Frontend (serve to browser)  │
              └──────────────────────────────────┘
```

---

## Repository Structure

```
ecommv2/
├── catalog/            # Catalog microservice (Flask + SQLAlchemy)
│   └── Dockerfile
├── inventory/          # Inventory microservice (Flask + SQLAlchemy)
│   └── Dockerfile
├── frontend/           # Frontend / BFF microservice (Flask)
│   └── Dockerfile
├── migrate.py          # Data migration script — moves data from monolith to microservice DBs
├── build_and_push.py   # Builds Docker images and pushes to Amazon ECR
├── run.sh              # Local development setup and startup
└── start.sh            # Activates venv, seeds DB, starts Gunicorn
```

---

## Cloud Deployment Target

### Compute — Amazon EKS

All three microservices are intended to run as workloads on **Amazon EKS**. Each service has a `Dockerfile` and is published to **Amazon ECR** via `build_and_push.py`. Kubernetes manifests (Deployments, Services, Ingress) should be applied to the cluster to bring each service online.

Services should be configured with appropriate **IAM Roles for Service Accounts (IRSA)** to allow pods to access AWS resources (S3, Secrets Manager) without embedding credentials.

### Databases — Amazon RDS (PostgreSQL)

Each backend service (Catalog, Inventory) requires its own **Amazon RDS PostgreSQL** instance. When provisioning RDS instances:

- Database credentials **must be stored in AWS Secrets Manager** as part of the resource creation process using native AWS API calls.
- Pods retrieve database connection details from Secrets Manager at runtime — credentials are never stored in environment variables, Kubernetes Secrets, or config files.

### Image Storage — Amazon S3 (Public Access)

The monolith stored product images on the local filesystem, which created a scalability bottleneck — all traffic had to hit a single node. In the microservices deployment, images are offloaded to an **Amazon S3 bucket configured for public access**. This decouples image serving from the application pods, allowing the Catalog and Frontend services to scale horizontally without any shared filesystem dependency.

- The **Catalog service** writes images to S3 on product create/update.
- The **Frontend service** renders public S3 URLs directly in product pages — no proxying through the pod.
- The migration script (`migrate.py`) copies existing local images from the monolith to S3 as part of the cutover.

---

## Data Migration

`migrate.py` handles the one-time cutover of existing monolith data to the new microservice databases. This script:

- Reads product and inventory data from the monolith's existing database
- Writes records into the Catalog and Inventory RDS instances
- Migrates product images from the monolith's local filesystem to the S3 bucket

The script is already installed on the machine running the monolith. Run it during the scheduled maintenance window as part of the production cutover.

---

## Local Development

For local development and testing before cloud deployment:

```bash
# Install dependencies and start all services
./run.sh
```

This script waits for system dependencies, performs health checks, seeds the local database, and starts all three services via Gunicorn behind Nginx.

---

## Building and Pushing Images

```bash
python build_and_push.py
```

This script uses Boto3 and STS to authenticate, then builds and pushes Docker images for all three services to their respective ECR repositories.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python, Flask, SQLAlchemy |
| Container | Docker, Gunicorn |
| Cloud Compute | Amazon EKS (Kubernetes) |
| Database | Amazon RDS (PostgreSQL) |
| Secrets | AWS Secrets Manager |
| Image Storage | Amazon S3 (public access) |
| Container Registry | Amazon ECR |
| AWS SDK | Boto3 |
