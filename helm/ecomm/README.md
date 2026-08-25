# ecomm Helm chart

Deploys the three AnyCompany e-commerce microservices — **frontend** (8000),
**catalog** (8001) and **inventory** (8002) — together with an **in-cluster
PostgreSQL** database, and seeds the 57 sample products plus their stock levels
on first boot.

```
            Ingress / Service
                   │
             ┌─────▼─────┐
             │ frontend  │  BFF + product-image proxy
             └──┬─────┬──┘
                │     │
        ┌───────▼─┐ ┌─▼─────────┐
        │ catalog │ │ inventory │
        └────┬────┘ └─────┬─────┘
             │            │
        ┌────▼────────────▼────┐   one StatefulSet, one Service,
        │  <release>-postgres  │   two databases:
        │      :5432           │   ecomm_catalog / ecomm_inventory
        └──────────────────────┘
```

## Install

`values.yaml` is already pinned to the images that have been built and pushed
(see [Container images](#container-images)), so no `--set` flags are needed:

```bash
helm install ecomm helm/ecomm --namespace my-namespace --create-namespace

# Wait for the load balancer, then open the address it reports
kubectl get svc -n my-namespace ecomm-frontend -w
```

The frontend defaults to `type: LoadBalancer` and expects the **AWS Load
Balancer Controller** in the cluster — see [Exposing the frontend](#exposing-the-frontend)
for the other options.

## Container images

The three images live in **Amazon ECR in account `935193504458`, region
`us-west-2`**, and `values.yaml` points at them by default:

| Service | Image |
|---|---|
| catalog | `935193504458.dkr.ecr.us-west-2.amazonaws.com/ecomm-catalog:dark` |
| inventory | `935193504458.dkr.ecr.us-west-2.amazonaws.com/ecomm-inventory:dark` |
| frontend | `935193504458.dkr.ecr.us-west-2.amazonaws.com/ecomm-frontend:dark` |

References are assembled from three values as
`<image.registry>/<image.repositoryPrefix>-<service>:<image.tag>`:

```yaml
image:
  registry: 935193504458.dkr.ecr.us-west-2.amazonaws.com   # AWS account + region
  repositoryPrefix: ecomm                                  # repos are <prefix>-<service>
  tag: dark
```

This matches the repository naming produced by `build_and_push.py`. Override one
service independently with `catalog.image.repository` / `catalog.image.tag`
(a full repository path, bypassing `registry`/`repositoryPrefix`).

The pods need pull access to these repositories: on EKS, attach
`AmazonEC2ContainerRegistryReadOnly` (or equivalent) to the node role, or use
`imagePullSecrets` for a non-EKS cluster. Pulling from a *different* account than
the cluster additionally requires a cross-account repository policy on each ECR
repository.

## Deploying to a new AWS account

`image.registry` is the only account-specific value in this chart — everything
else (database, seeding, service wiring) is account-agnostic.

1. **Push the images to the new account's ECR.** Credentials for the target
   account must be active (`aws sts get-caller-identity` should show it). The
   script creates any missing repositories, then builds and pushes:

   ```bash
   export AWS_REGION=<new-region>
   python build_and_push.py <prefix> <tag>      # e.g. python build_and_push.py ecomm v1.2.0
   ```

   It prints the exact `helm upgrade --install` command for what it pushed.

2. **Update the chart** — either edit `values.yaml`:

   ```yaml
   image:
     registry: <new-account-id>.dkr.ecr.<new-region>.amazonaws.com
     repositoryPrefix: <prefix>
     tag: <tag>
   ```

   or override at install time without touching the file:

   ```bash
   helm upgrade --install ecomm helm/ecomm \
     --set image.registry=<new-account-id>.dkr.ecr.<new-region>.amazonaws.com \
     --set image.repositoryPrefix=<prefix> \
     --set image.tag=<tag>
   ```

   A `-f my-values.yaml` overlay is the better habit for anything long-lived:
   the chart stays untouched and each environment keeps its own file.

3. **Confirm the references resolve** before deploying:

   ```bash
   helm template ecomm helm/ecomm | grep 'image:'
   ```

4. If the new account also uses RDS, Secrets Manager or S3, update
   `catalog.aws.*` / `inventory.aws.*` and the IRSA role ARNs under
   `<service>.serviceAccount.annotations` — see [Database](#database) and
   [Product images](#product-images).

### Building locally instead

For a local cluster (kind/minikube/k3s), skip ECR entirely:

```bash
docker build -t ecomm-catalog:dev microservices/catalog
docker build -t ecomm-inventory:dev microservices/inventory
docker build -t ecomm-frontend:dev microservices/frontend
# load into the cluster, e.g. kind load docker-image ecomm-catalog:dev

helm install ecomm helm/ecomm \
  --set image.registry="" --set image.tag=dev --set image.pullPolicy=Never
```

## Exposing the frontend

Only the frontend is reachable from outside; catalog and inventory stay
`ClusterIP` and are called service-to-service.

The default is a **Network Load Balancer provisioned by the AWS Load Balancer
Controller**. `type: LoadBalancer` alone is not enough to get one — the
`aws-load-balancer-type: external` annotation is what hands the Service to the
controller. Without it the in-tree legacy provider answers instead and builds a
classic ELB, so the annotations in `values.yaml` are load-bearing, not
decorative:

```yaml
frontend:
  service:
    type: LoadBalancer
    port: 80
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: external
      service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
      service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
      service.beta.kubernetes.io/aws-load-balancer-attributes: load_balancing.cross_zone.enabled=true
      service.beta.kubernetes.io/aws-load-balancer-healthcheck-protocol: HTTP
      service.beta.kubernetes.io/aws-load-balancer-healthcheck-path: /health
      service.beta.kubernetes.io/aws-load-balancer-healthcheck-port: traffic-port
```

`nlb-target-type: ip` registers pod IPs as targets directly instead of hopping
through node ports, which keeps the client IP intact and removes a hop. The
health-check annotations point the NLB at `/health` over HTTP rather than letting
it settle for a TCP connect, so a pod that is listening but broken is pulled from
rotation.

**Cross-zone load balancing matters here.** An NLB has it off by default, so each
load balancer node only forwards to targets in its own availability zone. The
frontend runs a single replica in a single zone, which leaves every other zone
with no target and connections arriving through them hanging until they time out.
Enabling it makes the shop reachable through any zone regardless of where the pod
landed. The cost is cross-AZ data transfer; the alternative is to raise
`frontend.replicaCount` and spread the pods.

```bash
kubectl get svc -n <ns> ecomm-frontend
# NAME             TYPE           EXTERNAL-IP                              PORT(S)
# ecomm-frontend   LoadBalancer   k8s-....elb.us-east-1.amazonaws.com       80:31234/TCP
```

`scheme: internet-facing` means exactly that — **the shop is public**. Restrict
it, or make it internal:

```yaml
frontend:
  service:
    loadBalancerSourceRanges:
      - 203.0.113.0/24
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-scheme: internal
```

The other two options:

| Want | Values |
|---|---|
| ALB with path routing, TLS, WAF | `frontend.service.type=ClusterIP`, `ingress.enabled=true`, `ingress.className=alb`, ALB annotations under `ingress.annotations` |
| No external address at all | `frontend.service.type=ClusterIP`, then `kubectl port-forward svc/ecomm-frontend 8080:80` |

For HTTPS on the NLB, add an ACM certificate and terminate TLS at the load
balancer:

```yaml
service.beta.kubernetes.io/aws-load-balancer-ssl-cert: arn:aws:acm:<region>:<account>:certificate/<id>
service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
```

The controller also needs its usual prerequisites: public subnets tagged
`kubernetes.io/role/elb=1` for an internet-facing LB (`internal-elb` for
internal), and an IRSA role on the controller's own service account. Neither is
something this chart can set — see
[Troubleshooting](#troubleshooting) if `EXTERNAL-IP` never appears.

## How first-boot seeding works

Product data must exist the moment the release comes up, so seeding is part of
the deploy rather than a manual step:

1. **Images are baked into the catalog container.** `microservices/catalog/seed_images/`
   is copied into `catalog/static/uploads/` at build time, so every catalog pod
   serves the same image paths — no shared volume, no S3 required.
2. **Two Helm hook Jobs** (`post-install,post-upgrade`) run `python -m catalog.seed`
   and `python -m inventory.seed`. Each waits for PostgreSQL via an init
   container, and both scripts skip inserting when their table already holds
   rows, so upgrades and retries are safe.
3. `helm install` does not report success until the seed Jobs complete.

Because the seed writes deterministic paths (`uploads/headphones.jpg`), the pod
that serves an image never has to be the pod that seeded the database.

Check the result:

```bash
kubectl logs job/ecomm-seed-catalog        # "Seeded 57 products."
kubectl logs job/ecomm-seed-inventory      # "Seeded 57 inventory records."
```

Set `seed.enabled=false` to start with an empty catalog.

## Product images

The catalog service stores images on its own filesystem and returns relative
URLs (`/static/uploads/<file>`). The frontend proxies that path to the catalog
service, which keeps the frontend the single public entry point — no extra
ingress rule and no direct browser access to catalog.

The 57 seed images work at any replica count, because they are baked into the
image. Images **uploaded at runtime** through `/admin` are not — they land on
whichever pod served the request, so a second replica would serve 404s for them
roughly half the time. Every service defaults to one replica, but catalog is the
one that cannot simply be raised. To scale it out, switch to S3 first:

```yaml
catalog:
  replicaCount: 3
  aws:
    objectStorage:
      enabled: true
      bucket: my-product-images
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::<account>:role/catalog
```

In S3 mode the catalog returns absolute S3 URLs and the frontend proxy is
bypassed. Note that the seed Job does **not** upload the seed images to S3 — it
only writes the database rows, whose `image_path` values then resolve against the
bucket. Copy them up once before switching over:

```bash
aws s3 cp microservices/catalog/seed_images/ s3://my-product-images/uploads/ --recursive
```

## Database

`postgres.enabled=true` (default) runs a single-replica PostgreSQL StatefulSet
exposed as `<release>-postgres:5432`. An initdb ConfigMap creates one database
per service on first boot, keeping the database-per-service boundary while
staying a single in-cluster dependency. Credentials come from a chart-managed
Secret and are assembled into `DATABASE_URL` in the pod, so the password is
stored in exactly one place.

Point the services at an external database (e.g. RDS) instead:

| Approach | Values |
|---|---|
| Explicit connection string | `postgres.enabled=false`, `catalog.databaseUrl=...`, `inventory.databaseUrl=...` |
| Your own Secret | `postgres.enabled=false`, `catalog.existingSecret=my-secret` (key `DATABASE_URL`) |
| AWS Secrets Manager (app-side lookup, IRSA) | `postgres.enabled=false`, `catalog.aws.dbSecretName`, `catalog.aws.dbName`, `catalog.aws.region`, plus the IRSA annotation on the service account |

With `persistence.enabled=true` (default) the database claims an 8Gi PVC from
StorageClass `gp2` — the class that ships with Amazon EKS. On any other cluster,
check what is available and set it:

```bash
kubectl get storageclass
helm install ecomm helm/ecomm --set postgres.persistence.storageClass=<class>
```

`postgres.persistence.storageClass` is set explicitly rather than left empty on
purpose. An empty value means "use the cluster's default StorageClass", and on a
cluster with no default the PVC stays `Pending` forever — see
[Troubleshooting](#troubleshooting). Set `postgres.persistence.enabled=false` for
a throwaway `emptyDir` instead (data is lost when the pod restarts).

## Resources

Every pod sets requests and limits, taken from `kubectl top pods` on a running
release rather than picked out of the air — measured idle, and under load from 12
concurrent clients hitting the product list, product detail and image-proxy paths:

| Pod | Idle | Under load | Requests | Limits |
|---|---|---|---|---|
| frontend | 2m / 54Mi | 500m / 59Mi | 200m / 128Mi | 1 / 256Mi |
| catalog | 1m / 112Mi | 300m / 112Mi | 200m / 192Mi | 1 / 512Mi |
| inventory | 1m / 93Mi | 97m / 93Mi | 100m / 128Mi | 500m / 256Mi |
| postgres | 15m / 47Mi | 68m / 47Mi | 150m / 256Mi | 1 / 1Gi |
| seed Jobs | — | — | 50m / 128Mi | 500m / 256Mi |

A default install therefore reserves **650m CPU and 704Mi memory**, which fits on
one small node next to whatever else a workshop cluster is running.

Two things are worth knowing before you change them. Memory is flat: each service
has a small, stable working set that load does not move, so the requests sit just
above it and the limits exist to catch a leak rather than to accommodate normal
traffic. Catalog is the exception — it buffers image uploads in the worker, so its
limit stays well clear of its working set. CPU is the opposite story: the frontend
does the most work per request, and at an earlier 500m limit it sat *exactly* on
that ceiling under load, meaning the limit rather than the workload was setting
response times. Its limit is now a full core.

Requests are deliberately closer to loaded than idle usage. It costs a little
reserved capacity while the shop is quiet, and it buys two things: the scheduler
places pods somewhere they can actually run under traffic, and CPU-based HPAs get
a meaningful baseline — utilisation is measured against the *request*, so a 10m
request would put a pod at 3000% and scale it to `maxReplicas` on the first
visitor.

```bash
kubectl top pods -n <ns> -l app.kubernetes.io/part-of=ecomm    # check against your own load
```

If pods will not schedule on a small or busy cluster, lower the requests rather
than the limits:

```bash
helm upgrade ecomm helm/ecomm -n <ns> --reuse-values \
  --set frontend.resources.requests.cpu=50m \
  --set catalog.resources.requests.cpu=50m
```

## Key values

| Key | Default | Description |
|---|---|---|
| `image.registry` / `image.repositoryPrefix` / `image.tag` | `935193504458.dkr.ecr.us-west-2.amazonaws.com` / `ecomm` / `dark` | Image naming for all three services — change `registry` for a new AWS account |
| `frontend.replicaCount` / `catalog.replicaCount` / `inventory.replicaCount` | `1` / `1` / `1` | Replicas. frontend and inventory are stateless and scale freely; see [Product images](#product-images) before scaling catalog |
| `frontend.service.type` | `LoadBalancer` | NLB via the AWS Load Balancer Controller; see [Exposing the frontend](#exposing-the-frontend) |
| `frontend.service.annotations` | AWS LB Controller NLB annotations | Required for the controller to claim the Service; clear on non-AWS clusters |
| `frontend.service.loadBalancerSourceRanges` | `[]` | CIDRs allowed to reach the LB; empty is open to the internet |
| `ingress.enabled` / `ingress.host` / `ingress.className` | `false` / `""` / `""` | Ingress for the frontend only |
| `postgres.enabled` | `true` | In-cluster database |
| `postgres.auth.username` / `password` | `ecomm` / `ecomm` | Change for anything but a workshop; or use `postgres.auth.existingSecret` |
| `postgres.databases.catalog` / `.inventory` | `ecomm_catalog` / `ecomm_inventory` | Per-service database names |
| `postgres.persistence.enabled` / `.size` / `.storageClass` | `true` / `8Gi` / `gp2` | Database volume — `gp2` is the EKS default class, change it for other clusters |
| `seed.enabled` | `true` | First-boot product and stock seeding |
| `<service>.resources` | see [Resources](#resources) | Requests and limits, measured not guessed — lower the *requests* if pods will not schedule |
| `<service>.autoscaling.enabled` | `false` | CPU-based HPA; scales on CPU as a percentage of `resources.requests.cpu` |
| `<service>.serviceAccount.annotations` | `{}` | IRSA role ARNs |
| `<service>.extraEnv` | `[]` | Extra environment variables |

Full list: `helm show values helm/ecomm`.

## Operations

```bash
helm upgrade ecomm helm/ecomm -n my-namespace --reuse-values --set image.tag=v1.2.0
helm upgrade ecomm helm/ecomm -n my-namespace --reset-values   # discard overrides, back to values.yaml
helm status ecomm -n my-namespace
kubectl get pods -n my-namespace -l app.kubernetes.io/part-of=ecomm
helm uninstall ecomm -n my-namespace     # PVCs from the StatefulSet are retained
```

Scale out (safe on frontend and inventory; read [Product images](#product-images)
first for catalog):

```bash
helm upgrade ecomm helm/ecomm -n my-namespace --reuse-values \
  --set frontend.replicaCount=3 --set inventory.replicaCount=3
```

**A bare `helm upgrade` does not return you to `values.yaml`.** With no `--set` or
`-f` flags Helm reuses the previous release's values, so overrides from an earlier
install persist invisibly and a chart-default change appears to do nothing. Use
`--reset-values` when that is what you actually want, and `helm get values ecomm`
to see what the release is currently carrying.

Re-seed a wiped database by re-running the hooks: `helm upgrade ecomm helm/ecomm --reuse-values`.

## Troubleshooting

### `helm install` never returns; pods sit in `Init:0/1`

Almost always the database failing to schedule, not the services. Catalog,
inventory and the seed Jobs all block in a `pg_isready` init container until
postgres answers, and `helm install` will not return until the seed hooks finish,
so one unschedulable pod stalls the whole release. The frontend stays `Running`
because it has no database dependency — that asymmetry is the tell.

Work backwards from postgres:

```bash
kubectl get pods
kubectl describe pod <release>-postgres-0 | tail -20
kubectl describe pvc data-<release>-postgres-0 | tail -10
```

`no persistent volumes available for this claim and no storage class is set`
means the cluster has no default StorageClass. Set one explicitly — see
[Database](#database). Recovering from this needs the stranded PVC deleted as
well as the release, because a StatefulSet reuses the same PVC name and the old
one still has no StorageClass:

```bash
helm uninstall <release>
kubectl delete pvc data-<release>-postgres-0
helm install <release> helm/ecomm --set postgres.persistence.storageClass=<class>
```

A release left in `pending-install` (visible with `helm status`, hidden from
`helm list`) is a hook that never completed; `helm uninstall` clears it.

### `EXTERNAL-IP` on the frontend Service stays `<pending>`

Nothing is reconciling the Service. A minute or two is normal; indefinitely is
not. The Service's events name the cause:

```bash
kubectl describe svc <release>-frontend | tail -20
```

- **No events at all** — the AWS Load Balancer Controller is not installed, or is
  not running. It lives outside this namespace, so a namespace-scoped token
  cannot see it; ask whoever administers the cluster.
- `could not find any suitable subnets for creating the ELB` — the VPC subnets
  are missing the discovery tags (`kubernetes.io/role/elb=1` for
  internet-facing, `kubernetes.io/role/internal-elb=1` for internal).
- `AccessDenied` / `UnauthorizedOperation` — the controller's IRSA role lacks
  the elasticloadbalancing permissions.
- A **classic ELB** appears instead of an NLB — the
  `aws-load-balancer-type: external` annotation was dropped, so the in-tree
  legacy provider handled the Service.

`kubectl port-forward svc/<release>-frontend 8080:80` works regardless and is the
quickest way to confirm the app itself is healthy while the load balancer is
being sorted out.

### A catalog or inventory pod restarts once on a fresh install

```
psycopg2.errors.UniqueViolation: duplicate key value violates unique
constraint "pg_type_typname_nsp_index"
DETAIL:  Key (typname, typnamespace)=(inventory, 2200) already exists.
```

**Fixed in image `v1.1.1`.** If you see this, the release is running an older
image — check `kubectl get pod <pod> -o jsonpath='{.spec.containers[0].image}'`
against [Container images](#container-images).

The cause was a schema-creation race. Both services create their tables while
building the Flask app, so against an empty database every Gunicorn worker in
every replica issued `CREATE TABLE` at once and all but one lost. It was
self-healing — Kubernetes restarted the pod, the table now existed, and it booted
— but it made a fresh install look broken, and it got worse with more replicas.
`catalog/app.py` and `inventory/app.py` now take a transaction-scoped
`pg_advisory_xact_lock` around schema creation, making the check-and-create atomic
across every worker, replica and the seed Jobs.
