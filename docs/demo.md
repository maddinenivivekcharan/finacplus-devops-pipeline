# End-to-End Demonstration Procedure

Use this flow if FinacPlus asks for a live demonstration.

## Preparation

- Jenkins job is connected to the GitHub repository.
- GitHub webhook points to `https://<jenkins-host>/github-webhook/`.
- Jenkins credentials exist:
  - `container-registry-credentials`
  - `kubeconfig-finacplus`
- Jenkins agent has Python, Docker, and kubectl.
- Kubernetes cluster can pull images from the configured registry.

## Demo Steps

1. Make a small visible code change, such as changing the service response metadata.
2. Run local tests:

   ```bash
   PYTHONPATH=src pytest -q
   ```

3. Commit and push:

   ```bash
   git add .
   git commit -m "Demonstrate CI/CD pipeline"
   git push
   ```

4. Show GitHub webhook delivery succeeded.
5. Show Jenkins started from the push event.
6. In Jenkins, show these stages:
   - `Validate Parameters`
   - `Checkout`
   - `Install and Test`
   - `Validate Configuration`
   - `Build Image`
   - `Push Image`
   - `Deploy to Kubernetes`
7. Show the image tag equals the real Git commit SHA.
8. Show Jenkins rollout verification completed.
9. Verify Kubernetes:

   ```bash
   kubectl -n finacplus-devops get deploy,svc,hpa,pods
   kubectl -n finacplus-devops rollout status deployment/finacplus-devops-pipeline
   ```

10. Port-forward and verify the app:

    ```bash
    kubectl -n finacplus-devops port-forward svc/finacplus-devops-pipeline 8080:80
    curl http://127.0.0.1:8080/healthz
    curl http://127.0.0.1:8080/version
    ```

## What To Explain

- A failed test stops the pipeline before Docker build and deployment.
- `DEPLOY_TO_K8S=true` requires `PUSH_IMAGE=true`, preventing deployment of an image only present on the Jenkins agent.
- The Git SHA flows from Git to Docker build, Docker tag, Kubernetes environment, and `/version`.
- Kubernetes probes and rollout status provide deployment feedback.
- Secrets are stored in Jenkins credentials, not source control.
