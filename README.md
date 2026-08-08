# FinacPlus DevOps CI/CD Pipeline

Submission repository for the FinacPlus SRE/DevOps Intern problem statement: automate build and Kubernetes deployment from Git commits using Jenkins, Groovy, Docker, and Kubernetes.

## What This Project Does

This repository contains a small Python web service plus the CI/CD and Kubernetes assets needed to demonstrate a production-minded deployment workflow. The service exposes health, readiness, version, and Prometheus-compatible metrics endpoints so the pipeline has a real artifact to build, test, containerize, and deploy.

## Architecture

```text
Git commit / webhook
        |
        v
Jenkins declarative Groovy pipeline
        |
        +-- install dependencies
        +-- run tests
        +-- validate Jenkinsfile and Kubernetes manifests
        +-- build Docker image
        +-- optionally push image
        +-- optionally deploy selected Kustomize overlay
        v
Kubernetes Deployment + Service + HPA + NetworkPolicy + Prometheus monitoring
```

## Repository Structure

```text
src/finacplus_pipeline/     Flask service
tests/                      Automated application tests
k8s/base/                   Shared Kubernetes resources
k8s/overlays/dev/           Dev deployment overlay
k8s/overlays/prod/          Production-style deployment overlay
scripts/                    Local and CI validation helpers
docs/                       Traceability and final review notes
Jenkinsfile                 Groovy pipeline definition
Dockerfile                  Runtime image definition
```

## Local Setup

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
set PYTHONPATH=src
pytest -q
python scripts/smoke_test.py
python scripts/validate_k8s.py
python scripts/validate_jenkinsfile.py Jenkinsfile
```

## Docker

```bash
docker build -t finacplus-devops-pipeline:local .
docker run --rm -p 8080:8080 finacplus-devops-pipeline:local
curl http://127.0.0.1:8080/healthz
```

The image runs as a non-root user and includes a Docker health check.

## Kubernetes

Render and validate an overlay:

```bash
kubectl kustomize k8s/overlays/dev
kubectl apply --dry-run=client --validate=false -k k8s/overlays/dev
```

Deploy to a configured cluster:

```bash
kubectl apply -k k8s/overlays/dev
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
```

The manifests include:

- `Deployment` with liveness/readiness probes
- `Service`
- `HorizontalPodAutoscaler`
- `ServiceAccount` with token automount disabled
- `NetworkPolicy`
- `ServiceMonitor` and `PrometheusRule` for Prometheus Operator clusters

## Jenkins Configuration

Create a Jenkins Pipeline or Multibranch Pipeline job pointing to this repository. Configure a webhook from GitHub to Jenkins so commits trigger builds automatically.

Minimum Jenkins capabilities: Pipeline, Git integration, Docker-capable agent, and Credentials Binding for registry and kubeconfig credentials.

Recommended Jenkins credentials:

| Credential ID | Type | Purpose |
| --- | --- | --- |
| `container-registry-credentials` | Username/password | Docker registry login for image push |
| `kubeconfig-finacplus` | Secret file | Kubernetes cluster access |

Useful pipeline parameters:

| Parameter | Purpose |
| --- | --- |
| `IMAGE_REGISTRY` | Registry host |
| `IMAGE_REPOSITORY` | Registry repository path |
| `K8S_NAMESPACE` | Target namespace |
| `KUSTOMIZE_OVERLAY` | `dev` or `prod` |
| `PUSH_IMAGE` | Push image when registry credentials are configured |
| `DEPLOY_TO_K8S` | Deploy when kubeconfig credentials and cluster are available |

## Security Notes

- Secrets are not stored in this repository.
- Jenkins uses scoped credentials for registry and Kubernetes access.
- Containers run as non-root, cannot escalate privileges, drop Linux capabilities, and use a read-only root filesystem.
- Kubernetes resources set CPU/memory requests and limits.
- `.gitignore` excludes common local credentials, virtual environments, logs, and generated files.

## Observability

The service exposes:

- `/healthz` for liveness checks
- `/readyz` for readiness checks
- `/version` for build metadata
- `/metrics` for Prometheus scraping

Kubernetes includes Prometheus Operator resources. In clusters without those CRDs, remove or skip `k8s/base/monitoring.yaml`.

## Troubleshooting

- Docker build fails locally: ensure Docker Desktop or another Docker daemon is running.
- Kubernetes dry-run contacts `localhost:8080`: no cluster is configured; use client-side rendering with `kubectl kustomize` or configure kubeconfig.
- Jenkins deployment fails at credentials: confirm the credential IDs match the Jenkinsfile.
- Monitoring manifests fail: install Prometheus Operator CRDs or omit `monitoring.yaml`.

## Limitations

This repository does not include cloud credentials, Jenkins credentials, a running Jenkins controller, a public webhook endpoint, or a live Kubernetes cluster. Those are environment-specific and must be configured outside source control.

## Future Improvements

- Add Terraform modules for GCP project, GKE, Artifact Registry, and Jenkins worker infrastructure.
- Add image vulnerability scanning with Trivy or a registry-native scanner.
- Add deployment promotion approvals between dev and prod overlays.
- Add SLO dashboards and alert routing through Alertmanager.
