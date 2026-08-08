pipeline {
  agent any

  options {
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
    timeout(time: 30, unit: 'MINUTES')
  }

  parameters {
    string(name: 'IMAGE_REGISTRY', defaultValue: 'registry.example.com', description: 'Container registry host.')
    string(name: 'IMAGE_REPOSITORY', defaultValue: 'finacplus/devops-pipeline', description: 'Repository path in the registry.')
    string(name: 'K8S_NAMESPACE', defaultValue: 'finacplus-devops', description: 'Target Kubernetes namespace.')
    choice(name: 'KUSTOMIZE_OVERLAY', choices: ['dev', 'prod'], description: 'Kubernetes overlay to deploy.')
    booleanParam(name: 'PUSH_IMAGE', defaultValue: false, description: 'Push image to registry. Requires registry credentials.')
    booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy to Kubernetes. Requires kubeconfig credentials.')
    string(name: 'REGISTRY_CREDENTIALS_ID', defaultValue: 'container-registry-credentials', description: 'Jenkins username/password credential ID for authenticated registries. Leave blank only for a trusted local no-auth registry.')
  }

  environment {
    APP_NAME = 'finacplus-devops-pipeline'
    DOCKER_BUILDKIT = '1'
    KUBECONFIG_CREDENTIALS_ID = 'kubeconfig-finacplus'
  }

  stages {
    stage('Validate Parameters') {
      steps {
        script {
          if (params.PUSH_IMAGE && params.IMAGE_REGISTRY == 'registry.example.com') {
            error('PUSH_IMAGE requires IMAGE_REGISTRY to be set to a real registry reachable by Kubernetes.')
          }
          if (params.DEPLOY_TO_K8S && !params.PUSH_IMAGE) {
            error('DEPLOY_TO_K8S requires PUSH_IMAGE=true so the target cluster can pull the image built by this run.')
          }
          if (!(params.IMAGE_REGISTRY ==~ /^[A-Za-z0-9][A-Za-z0-9._:-]*$/)) {
            error('IMAGE_REGISTRY contains unsupported characters.')
          }
          if (!(params.IMAGE_REPOSITORY ==~ /^[a-z0-9][a-z0-9._\/-]*$/)) {
            error('IMAGE_REPOSITORY must use lowercase registry path characters only.')
          }
          if (!(params.K8S_NAMESPACE ==~ /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/)) {
            error('K8S_NAMESPACE must be a valid Kubernetes namespace name.')
          }
        }
      }
    }

    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.GIT_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
          env.IMAGE_TAG = "${params.IMAGE_REGISTRY}/${params.IMAGE_REPOSITORY}:${env.GIT_SHA}"
        }
      }
    }

    stage('Install and Test') {
      steps {
        sh '''
          python -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
          PYTHONPATH=src pytest -q
        '''
      }
    }

    stage('Validate Configuration') {
      steps {
        sh '''
          . .venv/bin/activate
          python scripts/validate_k8s.py
          python scripts/validate_jenkinsfile.py Jenkinsfile
          kubectl kustomize k8s/overlays/${KUSTOMIZE_OVERLAY} >/tmp/rendered.yaml
        '''
      }
    }

    stage('Build Image') {
      steps {
        sh 'docker build --build-arg BUILD_SHA=${GIT_SHA} -t ${IMAGE_TAG} .'
      }
    }

    stage('Push Image') {
      when { expression { return params.PUSH_IMAGE } }
      steps {
        script {
          if (params.REGISTRY_CREDENTIALS_ID?.trim()) {
            withCredentials([usernamePassword(credentialsId: params.REGISTRY_CREDENTIALS_ID, usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASSWORD')]) {
              sh '''
                echo "${REGISTRY_PASSWORD}" | docker login "${IMAGE_REGISTRY}" --username "${REGISTRY_USER}" --password-stdin
                docker push "${IMAGE_TAG}"
                docker logout "${IMAGE_REGISTRY}"
              '''
            }
          } else {
            sh '''
              echo "Pushing to no-auth registry ${IMAGE_REGISTRY}"
              docker push "${IMAGE_TAG}"
            '''
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      when { expression { return params.DEPLOY_TO_K8S } }
      steps {
        withCredentials([file(credentialsId: env.KUBECONFIG_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
          sh '''
            kubectl create namespace "${K8S_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
            kubectl kustomize "k8s/overlays/${KUSTOMIZE_OVERLAY}" >/tmp/rendered.yaml
            . .venv/bin/activate
            python scripts/set_image.py /tmp/rendered.yaml "${APP_NAME}" "${IMAGE_TAG}" "${GIT_SHA}" >/tmp/rendered-with-image.yaml
            python scripts/set_namespace.py /tmp/rendered-with-image.yaml "${K8S_NAMESPACE}" >/tmp/rendered-final.yaml
            kubectl -n "${K8S_NAMESPACE}" apply -f /tmp/rendered-final.yaml
            kubectl -n "${K8S_NAMESPACE}" rollout status deployment/${APP_NAME} --timeout=120s
            kubectl -n "${K8S_NAMESPACE}" get deploy,svc,hpa
          '''
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'docs/validation.md,docs/requirements-traceability.md', fingerprint: true, onlyIfSuccessful: false
      deleteDir()
    }
    failure {
      echo 'Pipeline failed. Check the failed stage logs, credentials scope, Docker daemon, and Kubernetes connectivity.'
    }
  }
}
