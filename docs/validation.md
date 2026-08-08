# Validation

This file records reproducible validation for the repository. It distinguishes local execution from steps that still require external GitHub/Jenkins network access.

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
- Local Jenkins execution: passed using a Jenkins controller container, Docker socket access, local registry `127.0.0.1:5000`, and Docker Desktop Kubernetes
- Jenkins pipeline stages executed successfully: checkout, parameter validation, test, Kubernetes validation, Docker build, registry push, Kubernetes deploy, rollout verification
- Final Jenkins-deployed Git SHA: `4f1b0b1cdb1fa7b4e9257d03417b01773438464f`
- Final deployed image: `127.0.0.1:5000/finacplus/devops-pipeline:4f1b0b1cdb1fa7b4e9257d03417b01773438464f`

## Helper Script Validation

Rendered manifests were tested with `scripts/set_image.py` and `scripts/set_namespace.py` to confirm they can inject the Jenkins image tag, Git SHA, and target namespace into rendered Kubernetes YAML.

## Security Scan

A focused repository scan was run for common credential patterns such as GitHub tokens, AWS access keys, private keys, and kubeconfig certificate/key data. No matching secrets were found in tracked files.

## Not Executed Locally

- GitHub webhook delivery from github.com to Jenkins: requires a publicly reachable Jenkins webhook endpoint and a configured GitHub repository webhook.
- Push to an authenticated external registry: local validation used a trusted no-auth registry on `127.0.0.1:5000`; production use should keep `REGISTRY_CREDENTIALS_ID` set to a Jenkins username/password credential.

## External Validation Required

To prove the public GitHub-triggered case study end to end, run the Jenkins pipeline with:

- a real Git repository webhook,
- a Docker-capable Jenkins agent,
- a reachable container registry,
- `container-registry-credentials`,
- `kubeconfig-finacplus`,
- and a Kubernetes cluster that can pull the pushed image.
