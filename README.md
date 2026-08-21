# AnyCompany E-Commerce Platform v2

AnyCompany's e-commerce application, decomposed into three containerised Flask
microservices and deployed to Kubernetes with Helm. A single `helm install`
brings up the services, a PostgreSQL database, and 57 sample products with stock
levels — no manual seeding step.

```bash
helm install ecomm helm/ecomm --namespace <namespace> --create-namespace
kubectl get svc -n <namespace> ecomm-frontend -w     # wait for the load balancer
```

---

## Architecture

The application follows a **database-per-service** pattern. Only the frontend is
reachable from outside the cluster; it aggregates the two backend services and
proxies their product images, which keeps it the single public entry point.

| Service | Port | Responsibility |
|---|---|---|
| **Frontend** | 8000 | UI and BFF / API gateway — renders pages, aggregates the backends |
| **Catalog** | 8001 | Product catalog — CRUD plus product image storage |
| **Inventory** | 8002 | Stock tracking — quantity and warehouse per product |

```
                    ┌─────────────────┐
                    │    Frontend     │  ← LoadBalancer (NLB) → :8000
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌────────────────┐           ┌─────────────────┐
     │    Catalog     │           │    Inventory    │
     │  (port 8001)   │           │  (port 8002)    │
     └───────┬────────┘           └────────┬────────┘
             │                             │
             ▼                             ▼
      ┌──────────────────────────────────────────┐
      │      ecomm-postgres StatefulSet          │
      │  ecomm_catalog        ecomm_inventory    │
      └──────────────────────────────────────────┘
```

The default deployment is entirely self-contained: one in-cluster PostgreSQL
StatefulSet holding one logical database per service, and product images baked
into the catalog container image. The chart can be pointed at **RDS** (with
credentials from **Secrets Manager**) and **S3** instead, one value at a time —
see [`helm/ecomm/README.md`](helm/ecomm/README.md).

---

## Repository Structure

```
ecomm-workshopv2/
├── microservices/
│   ├── catalog/          # Catalog service (Flask + SQLAlchemy) + Dockerfile
│   │   └── seed_images/  # 57 sample product images, baked into the image
│   ├── inventory/        # Inventory service (Flask + SQLAlchemy) + Dockerfile
│   └── frontend/         # Frontend / BFF service (Flask + Jinja2) + Dockerfile
├── helm/ecomm/           # Helm chart — services, PostgreSQL, seed Jobs, HPAs
└── build_and_push.py     # Builds the three images and pushes them to Amazon ECR
```

Each service directory has its own README covering its API, environment
variables and IAM requirements.

Everything needed to stand the shop up is in this repository — application code,
Dockerfiles, the chart, and the 57 product images in
`microservices/catalog/seed_images/`. Nothing is fetched from an external source
at build or deploy time, so the only external dependencies are a container
registry to push to and a cluster to deploy into.

---

## Deploying

The chart is the deployment mechanism; `helm/ecomm/README.md` is the reference.
The short version:

```bash
helm install ecomm helm/ecomm --namespace <namespace> --create-namespace
```

`values.yaml` is pre-pinned to the images already in ECR (see
[Container Images](#container-images)), so no `--set` flags are needed. What you
get by default:

- **Three Deployments**, one replica each, with liveness and readiness probes on
  `/health` and resource requests derived from measured usage.
- **A PostgreSQL StatefulSet** with a database per service, claiming an 8Gi
  volume from StorageClass `gp2` — the class Amazon EKS ships with. On any other
  cluster, check `kubectl get storageclass` and set
  `postgres.persistence.storageClass`, or disable persistence for an `emptyDir`.
- **Seeding as part of the install.** Post-install hook Jobs load the 57 products
  and their stock levels, so the shop has data the moment it comes up. The Jobs
  are idempotent and re-run safely on upgrade.
- **A public NLB** in front of the frontend, provisioned by the AWS Load Balancer
  Controller. Restrict it with `frontend.service.loadBalancerSourceRanges`, or
  switch to an internal scheme, an ALB via Ingress, or plain `ClusterIP` plus
  `kubectl port-forward`.

To move off the in-cluster defaults: `postgres.enabled=false` plus
`catalog.aws.*` / `inventory.aws.*` for RDS and Secrets Manager, and
`catalog.aws.objectStorage.*` for S3-backed images. Both paths expect **IAM Roles
for Service Accounts (IRSA)**, set via `<service>.serviceAccount.annotations`, so
pods reach AWS without embedded credentials.

`helm/ecomm/README.md` also has a troubleshooting section for the failures that
actually come up — a `Pending` database PVC stalling the whole install, an
`EXTERNAL-IP` that never arrives.

---

## Container Images

The images referenced by the chart live in **Amazon ECR in account
`803817915563`, region `us-east-1`**:

| Service | Image |
|---|---|
| Catalog | `803817915563.dkr.ecr.us-east-1.amazonaws.com/ecomm-catalog:v1.1.1` |
| Inventory | `803817915563.dkr.ecr.us-east-1.amazonaws.com/ecomm-inventory:v1.1.1` |
| Frontend | `803817915563.dkr.ecr.us-east-1.amazonaws.com/ecomm-frontend:v1.1.1` |

These come from three values in `helm/ecomm/values.yaml`, assembled as
`<image.registry>/<image.repositoryPrefix>-<service>:<image.tag>`:

```yaml
image:
  registry: 803817915563.dkr.ecr.us-east-1.amazonaws.com   # account + region
  repositoryPrefix: ecomm                                  # repos are <prefix>-<service>
  tag: v1.1.1
```

### Building and Pushing Images

```bash
python build_and_push.py                    # prompts for prefix and tag
python build_and_push.py ecomm v1.2.0       # non-interactive
```

The script authenticates with Boto3 and STS, creates each ECR repository if it
does not already exist, then builds and pushes all three images. It prints the
matching `helm upgrade --install` command when it finishes.

For a local cluster, skip ECR and build straight into it:

```bash
docker build -t ecomm-catalog:dev microservices/catalog
docker build -t ecomm-inventory:dev microservices/inventory
docker build -t ecomm-frontend:dev microservices/frontend
# then e.g. kind load docker-image ecomm-catalog:dev

helm install ecomm helm/ecomm \
  --set image.registry="" --set image.tag=dev --set image.pullPolicy=Never
```

### Deploying to a New AWS Account

`image.registry` is the only account-specific value in the chart. With
credentials for the target account active:

```bash
export AWS_REGION=<new-region>
python build_and_push.py <prefix> <tag>

helm upgrade --install ecomm helm/ecomm \
  --set image.registry=<new-account-id>.dkr.ecr.<new-region>.amazonaws.com \
  --set image.repositoryPrefix=<prefix> \
  --set image.tag=<tag>
```

Update the `image:` block in `values.yaml` (or keep a per-environment
`-f my-values.yaml` overlay) to make it the new default, and verify with
`helm template ecomm helm/ecomm | grep 'image:'`. Pods also need pull access —
on EKS, `AmazonEC2ContainerRegistryReadOnly` on the node role; pulling across
accounts additionally needs a cross-account ECR repository policy. Full detail in
`helm/ecomm/README.md`.

---

## Local Development

Each service is a plain Flask app and runs on its own with a PostgreSQL instance
reachable at `DATABASE_URL`; see the per-service README for the exact commands.
Running the whole application locally is best done through the chart against
kind, minikube or k3s, using the local-build recipe above — that way you exercise
the same wiring, seeding and probes that a real deployment uses.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python, Flask, SQLAlchemy, Jinja2 |
| Container | Docker, Gunicorn |
| Orchestration | Kubernetes (Amazon EKS), Helm 3 |
| Database | PostgreSQL — in-cluster StatefulSet, or Amazon RDS |
| Secrets | Kubernetes Secrets, or AWS Secrets Manager |
| Image Storage | Container filesystem, or Amazon S3 |
| Ingress | AWS Load Balancer Controller (NLB or ALB) |
| Container Registry | Amazon ECR |
| AWS SDK | Boto3 |
