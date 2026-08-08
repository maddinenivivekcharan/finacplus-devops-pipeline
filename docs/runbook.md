# Runbook

This guide explains how to run, test, build, deploy, and demonstrate the FinacPlus DevOps CI/CD assignment.

## A. Prerequisites

- Python 3.14 or compatible Python 3.x
- Git
- Docker Desktop or another running Docker daemon
- kubectl
- A Kubernetes cluster for live deployment, such as minikube, kind, GKE, EKS, AKS, or an existing lab cluster
- Jenkins with Pipeline, Git integration, GitHub plugin, Credentials Binding, and a Docker-capable Linux agent
- A container registry reachable by the Kubernetes cluster
- GitHub repository access for webhook-based triggering

## B. Run the Python Application Locally

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
flask --app finacplus_pipeline.app:app run --host 127.0.0.1 --port 8080
```

Bash:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src flask --app finacplus_pipeline.app:app run --host 127.0.0.1 --port 8080
```

Verify:

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/readyz
curl http://127.0.0.1:8080/version
curl http://127.0.0.1:8080/metrics
```

## C. Run Tests

PowerShell:

```powershell
$env:PYTHONPATH = "src"
pytest -q
python scripts\smoke_test.py
python scripts\validate_k8s.py
python scripts\validate_jenkinsfile.py Jenkinsfile
python -m compileall -q src scripts tests
```

Bash:

```bash
PYTHONPATH=src pytest -q
python scripts/smoke_test.py
python scripts/validate_k8s.py
python scripts/validate_jenkinsfile.py Jenkinsfile
python -m compileall -q src scripts tests
```

## D. Build and Run Docker Locally

Requires Docker daemon to be running.

PowerShell:

```powershell
$sha = git rev-parse HEAD
docker build --build-arg BUILD_SHA=$sha -t finacplus-devops-pipeline:local .
docker run --rm -p 8080:8080 finacplus-devops-pipeline:local
```

Bash:

```bash
sha="$(git rev-parse HEAD)"
docker build --build-arg BUILD_SHA="$sha" -t finacplus-devops-pipeline:local .
docker run --rm -p 8080:8080 finacplus-devops-pipeline:local
```

Verify in another terminal:

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/version
```

## E. Validate Kubernetes Manifests

These render checks do not require a live cluster:

```bash
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

With a configured cluster:

```bash
kubectl apply --dry-run=server -k k8s/overlays/dev
```

## F. Run Kubernetes Locally

Example with Docker Desktop Kubernetes:

```powershell
$sha = git rev-parse HEAD
docker build --build-arg BUILD_SHA=$sha -t finacplus-devops-pipeline:local .
docker save finacplus-devops-pipeline:local -o $env:TEMP\finacplus-devops-pipeline-local.tar
docker cp $env:TEMP\finacplus-devops-pipeline-local.tar desktop-control-plane:/tmp/finacplus-devops-pipeline-local.tar
docker exec desktop-control-plane ctr -n k8s.io images import /tmp/finacplus-devops-pipeline-local.tar
kubectl kustomize k8s/overlays/dev > $env:TEMP\finacplus-rendered.yaml
python scripts\set_image.py $env:TEMP\finacplus-rendered.yaml finacplus-devops-pipeline finacplus-devops-pipeline:local $sha > $env:TEMP\finacplus-local.yaml
kubectl apply -f $env:TEMP\finacplus-local.yaml
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
kubectl -n finacplus-devops port-forward svc/finacplus-devops-pipeline 8080:80
```

Example with minikube:

```bash
minikube start
eval "$(minikube docker-env)"
sha="$(git rev-parse HEAD)"
docker build --build-arg BUILD_SHA="$sha" -t finacplus-devops-pipeline:local .
kubectl kustomize k8s/overlays/dev >/tmp/finacplus-rendered.yaml
python scripts/set_image.py /tmp/finacplus-rendered.yaml finacplus-devops-pipeline finacplus-devops-pipeline:local "$sha" >/tmp/finacplus-local.yaml
kubectl apply -f /tmp/finacplus-local.yaml
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
kubectl -n finacplus-devops port-forward svc/finacplus-devops-pipeline 8080:80
```

Verify:

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/version
```

For kind, build and load the image into the cluster before applying:

```bash
kind create cluster
sha="$(git rev-parse HEAD)"
docker build --build-arg BUILD_SHA="$sha" -t finacplus-devops-pipeline:local .
kind load docker-image finacplus-devops-pipeline:local
kubectl kustomize k8s/overlays/dev >/tmp/finacplus-rendered.yaml
python scripts/set_image.py /tmp/finacplus-rendered.yaml finacplus-devops-pipeline finacplus-devops-pipeline:local "$sha" >/tmp/finacplus-local.yaml
kubectl apply -f /tmp/finacplus-local.yaml
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
```

## G. Configure Jenkins

Create a Pipeline or Multibranch Pipeline job.

Required configuration:

- SCM: this Git repository
- Script path: `Jenkinsfile`
- Agent: Linux worker with Python, Docker, and kubectl
- Trigger: GitHub hook trigger for GitScm polling, provided by the Jenkins GitHub plugin and declared in `Jenkinsfile`
- Credentials:
  - `container-registry-credentials`: username/password for the registry
  - `kubeconfig-finacplus`: secret file containing kubeconfig for the target cluster

Parameters:

- `IMAGE_REGISTRY`: registry host, for example `registry.example-company.com`
- `IMAGE_REPOSITORY`: repository path, for example `finacplus/devops-pipeline`
- `K8S_NAMESPACE`: target namespace, default `finacplus-devops`
- `KUSTOMIZE_OVERLAY`: `dev` or `prod`
- `PUSH_IMAGE`: true when pushing to a registry
- `DEPLOY_TO_K8S`: true only when `PUSH_IMAGE` is also true
- `REGISTRY_CREDENTIALS_ID`: username/password credential for authenticated registries; leave blank only for a trusted local no-auth registry

The pipeline fails early if `DEPLOY_TO_K8S=true` and `PUSH_IMAGE=false`.

## H. Configure GitHub Webhook

In the GitHub repository:

1. Open Settings -> Webhooks -> Add webhook.
2. Payload URL: `https://<jenkins-host>/github-webhook/`
3. Content type: `application/json`
4. Events: push events
5. Save the webhook.

In Jenkins, enable GitHub hook trigger for a single Pipeline job, or use a Multibranch Pipeline with webhook indexing configured.

## I. Run the Complete CI/CD Flow

1. Commit and push a change to GitHub.
2. GitHub sends a push webhook to Jenkins.
3. Jenkins checks out the repository.
4. Jenkins validates parameters.
5. Jenkins installs dependencies and runs tests.
6. Jenkins renders and statically validates Kubernetes configuration.
7. Jenkins builds the Docker image using the real Git commit SHA.
8. If `PUSH_IMAGE=true`, Jenkins pushes the image to the registry.
9. If `DEPLOY_TO_K8S=true`, Jenkins deploys the rendered manifest with that image and Git SHA.
10. Jenkins waits for Kubernetes rollout status.

## J. Verify Deployment

```bash
kubectl -n finacplus-devops get pods
kubectl -n finacplus-devops get deployment finacplus-devops-pipeline
kubectl -n finacplus-devops get service finacplus-devops-pipeline
kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
kubectl -n finacplus-devops port-forward svc/finacplus-devops-pipeline 8080:80
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/version
```

Note: the HPA resource can show CPU metrics as `<unknown>` on local clusters without Metrics Server. That does not block Deployment rollout or Service verification.

## K. What Requires External Infrastructure

- GitHub webhook delivery requires a pushed GitHub repository and reachable Jenkins endpoint.
- Jenkins execution requires a Jenkins controller and agent; local validation used a controller container with Docker and kubectl available.
- Docker build/run requires Docker daemon access.
- Authenticated registry push requires real registry credentials. Local validation used a trusted no-auth registry on `127.0.0.1:5000`.
- Kubernetes deployment requires a live cluster and kubeconfig.
- The cluster must be able to pull the pushed image.

## Optional Monitoring Enhancement

The application exposes Prometheus-compatible metrics at `/metrics`. In a production cluster with Prometheus/Grafana, add a scrape configuration or Prometheus Operator resources outside the default deployment path. The default manifests intentionally avoid Prometheus CRDs so they work on a standard Kubernetes cluster.
