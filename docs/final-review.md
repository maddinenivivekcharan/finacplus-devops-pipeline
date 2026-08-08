# Final Hiring Review

Reviewer lens: FinacPlus Senior SRE/DevOps interviewer evaluating six shortlisted candidates for a DevOps/SRE internship.

## Strengths

- The repository contains a real deployable service instead of only abstract pipeline snippets.
- Jenkins stages cover checkout, dependency installation, automated tests, manifest validation, image build, optional push, optional Kubernetes deployment, and rollout verification.
- Kubernetes manifests include probes, resource requests/limits, HPA, service account, network policy, and Prometheus Operator monitoring resources.
- Security choices are visible and practical: Jenkins credentials, non-root runtime, read-only filesystem, dropped capabilities, `.dockerignore`, and no secret files.
- Documentation explains actual local validation results separately from infrastructure-dependent steps.

## Improvement Areas

- A real Jenkins controller, registry, and Kubernetes cluster are still required to prove webhook-triggered deployment end to end.
- Terraform/GCP are covered conceptually in documentation because the assignment focuses on Jenkins/Kubernetes and no cloud project credentials are available locally.
- Prometheus Operator CRDs must be installed in the cluster before applying `ServiceMonitor` and `PrometheusRule`.

## Shortlist Decision

Yes. This should be strong enough for the next technical round because it demonstrates production-minded CI/CD design, practical Kubernetes deployment hygiene, security awareness, and honest validation boundaries.

Final score: 8.5/10.
