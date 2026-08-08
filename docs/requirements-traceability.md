# Requirements Traceability

| Assignment requirement | Implementation |
| --- | --- |
| Trigger Jenkins build on commits to a Git repository | `Jenkinsfile` uses `checkout scm` and is compatible with GitHub webhook or multibranch pipeline triggers. Setup steps are in `README.md`. |
| Build artifact after commit | `Install and Test` runs Python dependency installation and tests. `Build Image` produces the deployable Docker image. |
| Deploy successful artifact to Kubernetes | `Deploy to Kubernetes` applies the selected Kustomize overlay and waits for rollout status. Deployment is gated by `DEPLOY_TO_K8S`. |
| Scalable and adaptable for different repositories/clusters | Pipeline parameters configure registry, image repository, namespace, and overlay. Jenkins credentials isolate registry and cluster access. |
| Use Groovy/Jenkins automation | Declarative Groovy pipeline is implemented in `Jenkinsfile`, with stages, parameters, post actions, credentials, and failure feedback. |
| Robust error handling and clear feedback | Pipeline has timeouts, disabled concurrent builds, rollout verification, post-failure messaging, and validation stages before deploy. |
| Security best practices | Non-root Docker/Kubernetes runtime, read-only root filesystem, dropped Linux capabilities, no committed secrets, credential binding, `.gitignore`, network policy, and resource limits. |
| Test cases and validation | `tests/test_app.py`, `scripts/validate_k8s.py`, `scripts/validate_jenkinsfile.py`, `scripts/smoke_test.py`, and kubectl kustomize/client dry-run where available. |
| Monitoring/logging recommendations | `/metrics`, `ServiceMonitor`, `PrometheusRule`, structured health endpoints, stdout/stderr container logging, and README operating notes. |
