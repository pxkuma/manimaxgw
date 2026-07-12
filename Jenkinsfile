pipeline {
    // each stage runs in its own docker container, no shared global agent
    agent none

    environment {
        EC2_USER       = 'ubuntu'
        EC2_HOST       = '13.48.106.251'
        REPO_PATH      = '/home/ubuntu/vrihi'
        SONAR_HOST_URL = credentials('sonar-host-url')
        SONAR_TOKEN    = credentials('sonar-token')
    }

    stages {

        stage('Web: Install') {
            agent {
                docker { image 'node:18-alpine'; reuseNode true }
            }
            steps {
                dir('web') {
                    sh 'npm ci || npm install'
                }
            }
        }

        stage('Renderer: Check') {
            agent {
                docker { image 'python:3.11-slim'; reuseNode true }
            }
            steps {
                dir('renderer') {
                    sh 'pip install --quiet fastapi uvicorn sse-starlette httpx'
                    // basic syntax check, swap for pytest when tests are added
                    sh 'python -m py_compile auto_video.py renderer_api.py'
                }
            }
        }

        stage('SonarQube') {
            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args  '--entrypoint=""'
                    reuseNode true
                }
            }
            steps {
                sh """
                    sonar-scanner \
                        -Dsonar.projectKey=vrihi \
                        -Dsonar.sources=web,renderer \
                        -Dsonar.exclusions=**/node_modules/**,**/__pycache__/**,**/media/**,**/.venv/** \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.token=${SONAR_TOKEN}
                """
            }
        }

        stage('Deploy') {
            // only runs on main — SSH into EC2, pull latest, restart containers
            when { branch 'main' }
            agent { label 'built-in' }
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} '
                            cd ${REPO_PATH} &&
                            git pull origin main &&
                            docker compose down --remove-orphans &&
                            docker compose up -d --build &&
                            docker compose ps
                        '
                    """
                }
            }
        }
    }

    post {
        always { cleanWs() }
    }
}
