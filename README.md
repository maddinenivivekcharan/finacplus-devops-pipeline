# FinacPlus DevOps CI/CD Pipeline

Implementation of the FinacPlus SRE/DevOps Intern case study: a Jenkins/Groovy pipeline that builds a deployable artifact from Git commits and deploys it to Kubernetes after successful validation.

The repository includes a small Flask service only so the pipeline has a real artifact to test, containerize, and deploy. The service exposes `/healthz`, `/readyz`, `/version`, and `/metrics`.

## Architecture

```text
Git commit / GitHub webhook
        |
        v
Jenkins declarative pipeline
        |
        +-- validate parameters
        +-- checkout source
        +-- install dependencies and run tests
        +-- render/validate Kubernetes configuration
        +-- build Docker image with the real Git SHA
        +-- optionally push image to a registry
        +-- optionally deploy to Kubernetes after image push
        v
Kubernetes Deployment + Service + HPA + NetworkPolicy
```

## Repository Structure

```text
src/finacplus_pipeline/     Application used as the deployable artifact
tests/                      Application tests
k8s/base/                   Standard Kubernetes resources
k8s/overlays/dev/           Development overlay
k8s/overlays/prod/          Production-style overlay
scripts/                    Validation and manifest mutation helpers
docs/                       Runbook, demo plan, validation, traceability
Jenkinsfile                 Jenkins declarative Groovy pipeline
Dockerfile                  Runtime image definition
```

## Quick Local Validation

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
pytest -q
python scripts\smoke_test.py
python scripts\validate_k8s.py
python scripts\validate_jenkinsfile.py Jenkinsfile
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

Bash:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src pytest -q
python scripts/smoke_test.py
python scripts/validate_k8s.py
python scripts/validate_jenkinsfile.py Jenkinsfile
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

## Docker

Requires a running Docker daemon:

```bash
docker build --build-arg BUILD_SHA="$(git rev-parse HEAD)" -t finacplus-devops-pipeline:local .
docker run --rm -p 8080:8080 finacplus-devops-pipeline:local
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/version
```

The image runs as a non-root user. Kubernetes also runs it with privilege escalation disabled, all Linux capabilities dropped, and a read-only root filesystem.

## Kubernetes

Render manifests without needing a cluster:

```bash
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

Deploy to a configured cluster after the image has been pushed to a registry the cluster can pull from:

```bash
sha="$(git rev-parse HEAD)"
image="<registry>/<repository>:$sha"
kubectl kustomize k8s/overlays/dev >/tmp/finacplus-rendered.yaml
python scripts/set_image.py /tmp/finacplus-rendered.yaml finacplus-devops-pipeline "$image" "$sha" >/tmp/finacplus-deploy.yaml
kubectl apply -f /tmp/finacplus-deploy.yaml
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
kubectl -n finacplus-devops get deploy,svc,hpa,pods
```

The default Kubernetes path does not require Prometheus Operator CRDs. The app still exposes `/metrics`; Prometheus/Grafana integration is documented as an optional production enhancement in [docs/runbook.md](docs/runbook.md).

## Jenkins

Create a Pipeline or Multibranch Pipeline job that uses this repository and `Jenkinsfile`.

Required Jenkins capabilities:

- Pipeline
- Git integration
- GitHub plugin for `githubPush()` webhook triggers
- Docker-capable Linux agent
- Credentials Binding
- `kubectl` available on the deploying agent

Credential IDs used by the Jenkinsfile:

| Credential ID | Type | Purpose |
| --- | --- | --- |
| `container-registry-credentials` | Username/password | Registry login for image push |
| `kubeconfig-finacplus` | Secret file | Kubernetes cluster access |

Important parameters:

| Parameter | Purpose |
| --- | --- |
| `IMAGE_REGISTRY` | Registry host reachable by the Kubernetes cluster |
| `IMAGE_REPOSITORY` | Registry repository path |
| `K8S_NAMESPACE` | Target namespace |
| `KUSTOMIZE_OVERLAY` | `dev` or `prod` |
| `PUSH_IMAGE` | Push the image after build |
| `DEPLOY_TO_K8S` | Deploy after the image has been pushed |
| `REGISTRY_CREDENTIALS_ID` | Registry credential ID; leave blank only for a trusted local no-auth registry |

Safety rule: `DEPLOY_TO_K8S=true` requires `PUSH_IMAGE=true`. This prevents deploying an image tag that only exists on the Jenkins agent.

## Build Metadata

Jenkins reads the real commit with `git rev-parse HEAD`, uses that SHA as the Docker tag, passes it into the Docker build, and writes it into the Kubernetes Deployment environment. The `/version` endpoint reports that value after deployment.

## Validation Status

See [docs/validation.md](docs/validation.md) for commands run locally, passing results, and items that require external infrastructure.

## Full Run Guide

See [docs/runbook.md](docs/runbook.md) for local execution, Docker, Kubernetes, Jenkins, GitHub webhook setup, and deployment verification steps.
