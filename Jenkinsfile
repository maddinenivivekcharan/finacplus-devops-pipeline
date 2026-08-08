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
  }

  environment {
    APP_NAME = 'finacplus-devops-pipeline'
    DOCKER_BUILDKIT = '1'
    REGISTRY_CREDENTIALS_ID = 'container-registry-credentials'
    KUBECONFIG_CREDENTIALS_ID = 'kubeconfig-finacplus'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.GIT_SHA = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
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
          kubectl apply --dry-run=client --validate=false -f /tmp/rendered.yaml
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
        withCredentials([usernamePassword(credentialsId: env.REGISTRY_CREDENTIALS_ID, usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASSWORD')]) {
          sh '''
            echo "${REGISTRY_PASSWORD}" | docker login "${IMAGE_REGISTRY}" --username "${REGISTRY_USER}" --password-stdin
            docker push "${IMAGE_TAG}"
            docker logout "${IMAGE_REGISTRY}"
          '''
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
            python scripts/set_image.py /tmp/rendered.yaml "${APP_NAME}" "${IMAGE_TAG}" >/tmp/rendered-with-image.yaml
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
      archiveArtifacts artifacts: 'docs/final-review.md,docs/requirements-traceability.md', fingerprint: true, onlyIfSuccessful: false
      deleteDir()
    }
    failure {
      echo 'Pipeline failed. Check the failed stage logs, credentials scope, Docker daemon, and Kubernetes connectivity.'
    }
  }
}
