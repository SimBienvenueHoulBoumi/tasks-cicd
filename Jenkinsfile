/**
 * 🔧 Jenkinsfile – Pipeline CI/CD Spring Boot
 * 📦 Maven build | 🧪 Tests | 📊 SonarQube | 🐳 Docker | 🔐 Sécurité (Trivy, OWASP)
 */

pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
        dockerTool 'docker'
    }

    environment {
        // 🏷️ Infos projet
        APP_NAME = 'tasks-cicd'
        SONAR_PROJECT_KEY = 'tasks'
        GIT_REPO_URL = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH = '*/main'

        // 📊 SonarQube
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_TOKEN = credentials('SONAR_TOKEN')

        // 🐳 Docker
        DOCKER_HUB_USER = 'brhulla@gmail.com'
        DOCKER_HUB_NAMESPACE = 'docker.io/brhulla'
        DOCKER_HUB_TOKEN = credentials('DOCKER-HUB-TOKEN')

        // 🔒 Credentials
        AGENT_CREDENTIALS = 'JENKINS-AGENT-CREDENTIALS'

        // 🧬 Trivy & Sécurité
        TRIVY_REPORT_DIR = 'trivy-reports'
        OWASP_REPORT_DIR = 'dependency-report'

        // 🏗️ Tag de build
        IMAGE_TAG = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL = "${DOCKER_HUB_NAMESPACE}/${APP_NAME}:${BUILD_NUMBER}"
    }

    options {
        skipDefaultCheckout true
        timestamps()
    }

    stages {

        stage('✅ Vérification des variables') {
            steps {
                echo "🔍 Docker image   : ${IMAGE_TAG}"
                echo "🔍 DockerHub path : ${IMAGE_FULL}"
                echo "🔍 SonarQube URL  : ${SONAR_HOST_URL}"
                echo "🔍 Git repository : ${GIT_REPO_URL} (${GIT_BRANCH})"
            }
        }

        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO_URL}",
                        credentialsId: "${AGENT_CREDENTIALS}"
                    ]]
                ])
            }
        }

        stage('🔧 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ]; then
                        echo "➡ Génération du Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('🔨 Build & Tests') {
            steps {
                sh './mvnw clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'TOKEN')]) {
                        sh '''
                            ./mvnw sonar:sonar \
                            -Dsonar.projectKey=tasks \
                            -Dsonar.host.url=$SONAR_HOST_URL \
                            -Dsonar.token=$TOKEN
                        '''
                    }
                }
            }
        }


        stage('🔐 Analyse sécurité OWASP') {
            steps {
                sh "mvn org.owasp:dependency-check-maven:check -Dformat=XML -DoutputDirectory=${OWASP_REPORT_DIR}"
            }
            post {
                always {
                    archiveArtifacts artifacts: "${OWASP_REPORT_DIR}/dependency-check-report.xml", allowEmptyArchive: true
                }
            }
        }

        stage('🐳 Build Docker') {
            steps {
                sh "docker build -t ${IMAGE_TAG} ."
            }
        }

        stage('🛡️ Trivy – Analyse image') {
            steps {
                sh """
                    mkdir -p ${TRIVY_REPORT_DIR}
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $PWD/${TRIVY_REPORT_DIR}:/root/reports \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity CRITICAL,HIGH \
                        --format json \
                        --output /root/reports/trivy-image-report.json \
                        ${IMAGE_TAG}
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/trivy-image-report.json", allowEmptyArchive: true
                }
                failure {
                    echo '🚨 Vulnérabilités critiques détectées dans l’image Docker.'
                }
            }
        }

        stage('🧬 Trivy – Analyse code source') {
            steps {
                sh """
                    docker run --rm \
                        -v $PWD:/project \
                        -v $PWD/${TRIVY_REPORT_DIR}:/root/reports \
                        aquasec/trivy:latest fs /project \
                        --exit-code 0 \
                        --format json \
                        --output /root/reports/trivy-fs-report.json
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/trivy-fs-report.json", allowEmptyArchive: true
                }
            }
        }

        stage('🚀 Push Docker vers DockerHub') {
            steps {
                withCredentials([string(credentialsId: 'DOCKER-HUB-TOKEN', variable: 'DOCKER_TOKEN')]) {
                    sh """
                        echo "$DOCKER_TOKEN" | docker login -u "${DOCKER_HUB_USER}" --password-stdin
                        docker tag ${IMAGE_TAG} ${IMAGE_FULL}
                        docker push ${IMAGE_FULL}
                        docker logout
                    """
                }
            }
        }

        stage('🧹 Nettoyage') {
            steps {
                sh 'docker rmi ${IMAGE_TAG} || true'
                sh 'docker system prune -f'
            }
        }

    }

    post {
        success {
            echo '✅ Pipeline terminé avec succès.'
        }
        failure {
            echo '❌ Échec du pipeline.'
        }
        always {
            cleanWs()
        }
    }
}
