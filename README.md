# AIOps Platform

> Production-ready Kubernetes observability platform on AWS EKS, built and committed entirely by AI agents using atomic GitOps workflows.

![Architecture](images/architecture.svg)

---

## Overview

This project provisions a complete cloud-native observability stack on AWS EKS using Terraform, Kubernetes manifests, and Helm charts. A Flask application (`traffic-simulator`) serves as the workload, exposing rich Prometheus metrics and structured logs — designed to trigger real alerts, test autoscaling, and validate the observability pipeline end-to-end.

The entire codebase was structured, committed, and merged by AI agents: **Platform Engineer** (Claude Code) handled atomic commits and GitOps workflow, **SRE Specialist** analyzed metrics and observability signals, and **Kubernetes Specialist** monitored workload health.

---

## Stack

| Layer | Technology |
|---|---|
| Cloud | AWS (EKS, S3, ECR, Route53, ACM, NLB) |
| IaC | Terraform (remote state on S3 + DynamoDB) |
| Container Orchestration | Amazon EKS 1.34 |
| Application | Flask + Gunicorn + Prometheus client |
| Metrics | Prometheus (kube-prometheus-stack) |
| Dashboards | Grafana (RED + USE dashboards) |
| Logs | Grafana Loki + Alloy DaemonSet |
| CI/CD | GitHub Actions (OIDC → ECR) |
| Ingress | Nginx Ingress Controller + NLB (TLS) |
| Autoscaling | HPA (CPU 70% / Memory 80%) |
| IAM | IRSA via EKS OIDC Provider |

---

## Project Structure

```
.
├── terraform/
│   ├── 00-remote-stack/     # S3 bucket + DynamoDB for Terraform state
│   ├── 01-networking/       # VPC, subnets, IGW, NAT Gateway, S3 endpoint
│   └── 02-eks/              # EKS cluster, node group, IRSA, addons, ACM, DNS
├── app/
│   ├── main.py              # Flask traffic simulator with Prometheus metrics
│   ├── Dockerfile           # Container image
│   ├── gunicorn.conf.py     # Gunicorn + multiprocess metrics setup
│   └── requirements.txt
├── k8s/
│   ├── deployment.yaml      # Deployment + Service
│   ├── ingress.yaml         # Nginx ingress (TLS, gabrielstudying.click)
│   ├── hpa.yaml             # HorizontalPodAutoscaler
│   ├── pdb.yaml             # PodDisruptionBudget
│   ├── servicemonitor.yaml  # Prometheus ServiceMonitor
│   ├── prometheusrule.yaml  # Alerting rules
│   ├── recording-rules.yaml # Recording rules
│   ├── grafana-dashboard-app.yaml   # RED method dashboard
│   └── grafana-dashboard-infra.yaml # USE method dashboard
├── charts/
│   ├── kube-prometheus-stack/values.yaml
│   ├── loki/values.yaml
│   └── alloy/values.yaml
└── images/
    └── architecture.svg
```

---

## Infrastructure

### Terraform Modules

**`00-remote-stack`** — bootstraps remote state backend before any other module.

**`01-networking`** — VPC `10.0.0.0/16` with 3 public + 3 private subnets across AZs, NAT Gateway, S3 VPC endpoint for private ECR/S3 access without traversing the internet.

**`02-eks`** — EKS cluster `studying-cluster` with managed node group (`t3.medium x2`), EBS CSI Driver addon, Nginx Ingress via Helm, ACM wildcard certificate (`*.gabrielstudying.click`), NLB with TLS listener, Route53 DNS, OIDC provider for IRSA, GitHub OIDC for CI/CD federation.

```bash
cd terraform/00-remote-stack && terraform apply
cd terraform/01-networking   && terraform apply
cd terraform/02-eks          && terraform apply
```

> Requires AWS profile `studying` (`export AWS_PROFILE=studying`)

---

## Application

`traffic-simulator` is a Flask app built to stress-test the observability stack. It exposes:

- `GET /metrics` — Prometheus metrics endpoint
- `GET /api/health` — Liveness/readiness probe
- `GET /api/stress/cpu?seconds=N` — CPU burn (triggers HPA)
- `GET /api/error/500` — Forces HTTP 500 (triggers error rate alert)
- `GET /api/error/timeout?seconds=N` — Slow request simulation
- `GET /api/error/oom?mb=N` — Memory allocation stress
- `GET /api/error/cascade?count=N` — Random 4xx/5xx cascade
- `POST /api/traffic/start` — Background load generation
- `POST /api/traffic/stop` — Stop load + return stats

### Build & Push

```bash
docker build -t traffic-simulator ./app
docker tag traffic-simulator <account>.dkr.ecr.us-east-1.amazonaws.com/traffic-simulator:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/traffic-simulator:latest
```

CI/CD runs automatically on push to `main` via GitHub Actions with OIDC authentication — no long-lived AWS credentials stored.

---

## Observability

### Metrics (Prometheus + Grafana)

Install kube-prometheus-stack:
```bash
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -f charts/kube-prometheus-stack/values.yaml \
  -n monitoring --create-namespace
```

Grafana is exposed at `https://grafana.gabrielstudying.click` with two provisioned dashboards:

- **App Dashboard (RED)** — Request Rate, Error Rate, P99 Latency, Active Requests
- **Infra Dashboard (USE)** — CPU/Memory Utilization, Saturation (throttling), Pod restarts

### Logs (Loki + Alloy)

Install Loki:
```bash
helm upgrade --install loki grafana/loki \
  -f charts/loki/values.yaml \
  -n logging --create-namespace
```

Install Alloy (DaemonSet log collector):
```bash
helm upgrade --install alloy grafana/alloy \
  -f charts/alloy/values.yaml \
  -n logging
```

Alloy discovers all pods per node, parses CRI logs, extracts structured JSON from `traffic-simulator`, and ships to Loki. Loki persists chunks to S3 via IRSA (no stored credentials).

### Alerting Rules

| Alert | Condition |
|---|---|
| `HighErrorRate` | Error rate > 5% for 2 min |
| `HighLatencyP99` | P99 latency > 2s for 2 min |
| `PodRestartingTooOften` | Restarts > 3 in 15 min |
| `TrafficSaturation` | Active requests > 100 for 5 min |
| `CPUThrottling` | Throttling > 20% for 5 min |

---

## Apply Kubernetes Manifests

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/servicemonitor.yaml
kubectl apply -f k8s/recording-rules.yaml
kubectl apply -f k8s/prometheusrule.yaml
kubectl apply -f k8s/grafana-dashboard-app.yaml
kubectl apply -f k8s/grafana-dashboard-infra.yaml
```

The app will be available at `https://app.gabrielstudying.click`.

---

## Security

- **IRSA** — Loki and EBS CSI Driver authenticate to AWS via EKS OIDC, no static credentials
- **GitHub OIDC** — GitHub Actions assumes an IAM role via federation, no long-lived secrets
- **TLS everywhere** — ACM wildcard cert attached to NLB, HTTPS enforced via ingress annotation
- **PDB** — Ensures at least 1 replica available during node drains or rolling updates

---

## AI Agents

This project was built and operated by three specialized AI agents powered by Claude:

### Git Agent (Claude)
Responsible for the entire version control lifecycle — creating feature branches, making atomic commits (one per file), opening PRs.

### SRE Specialist (Claude)
Analyzes the observability stack using the RED and USE methodologies. Queries Prometheus metrics to detect high error rates, latency spikes, and resource saturation. Generates structured reports with root cause analysis, alerting recommendations, and remediation steps based on real-time signals from Grafana, Prometheus, and Loki.

### Kubernetes Specialist (Claude)
Monitors workload health across the cluster — pod status, resource utilization, HPA scaling events, and container restarts. Performs rightsizing analysis by comparing actual CPU/memory usage against configured requests and limits, and validates that critical components like PDB, ServiceMonitor, and PrometheusRules are correctly configured.
