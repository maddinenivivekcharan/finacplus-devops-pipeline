# Validation

This file records reproducible validation for the repository. It is factual and does not claim that external infrastructure was tested locally.

## Executed Successfully Locally

Environment used: Windows PowerShell, Python 3.14.6, kubectl v1.36.0 client, Git 2.54.0, Docker 29.4.1, Docker Desktop Kubernetes context `docker-desktop`.

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe scripts\validate_k8s.py
.\.venv\Scripts\python.exe scripts\validate_jenkinsfile.py Jenkinsfile
.\.venv\Scripts\python.exe -m compileall -q src scripts tests
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

Latest local results:

- `pytest`: 4 passed
- smoke test: passed
- Kubernetes static validation: passed
- Jenkinsfile static validation: passed
- Python compilation: passed
- Kustomize render for `dev`: passed
- Kustomize render for `prod`: passed
- Docker image build: passed with `finacplus-devops-pipeline:local`
- Docker container endpoint checks: `/healthz`, `/readyz`, `/version`, and `/metrics` passed
- Docker Desktop Kubernetes deployment: rollout passed
- Kubernetes Service endpoint checks: `/healthz`, `/readyz`, `/version`, and `/metrics` passed through `svc/finacplus-devops-pipeline`
- Deployed `/version` reported the Git SHA used for the build

## Helper Script Validation

Rendered manifests were tested with `scripts/set_image.py` and `scripts/set_namespace.py` to confirm they can inject the Jenkins image tag, Git SHA, and target namespace into rendered Kubernetes YAML.

## Security Scan

A focused repository scan was run for common credential patterns such as GitHub tokens, AWS access keys, private keys, and kubeconfig certificate/key data. No matching secrets were found in tracked files.

## Not Executed Locally

- Jenkins job execution: requires a Jenkins controller and configured agents/credentials.
- GitHub webhook trigger: requires a pushed GitHub repository and publicly reachable Jenkins webhook endpoint.
- Registry push: requires real registry credentials.

## External Validation Required

To prove the complete case study end to end, run the Jenkins pipeline with:

- a real Git repository webhook,
- a Docker-capable Jenkins agent,
- a reachable container registry,
- `container-registry-credentials`,
- `kubeconfig-finacplus`,
- and a Kubernetes cluster that can pull the pushed image.
