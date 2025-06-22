pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }

    options {
        skipDefaultCheckout true
        timestamps()
    }

    environment {
        APP_NAME             = 'tasks-cicd'
        SONAR_PROJECT_KEY    = 'tasks-cicd'
        GIT_REPO_URL         = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH           = '*/main'

        SONAR_HOST_URL       = 'http://host.docker.internal:9000'
        SONARQUBE_INSTANCE   = 'sonarserver'

        DOCKER_HUB_USER      = 'xenon44'
        DOCKER_HUB_NAMESPACE = 'docker.io/xenon44'
        IMAGE_TAG            = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL           = "${DOCKER_HUB_NAMESPACE}/${APP_NAME}:${BUILD_NUMBER}"

        TRIVY_REPORT_DIR     = 'trivy-reports'
        OWASP_REPORT_DIR     = 'dependency-report'

        GITHUB_CREDENTIALS   = 'GITHUB-CREDENTIALS'
    }

    stages {

        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS}"
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

        stage('🔧 Compilation Maven') {
            steps {
                sh './mvnw clean compile'
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                withCredentials([string(credentialsId: 'SONAR-TOKEN', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        docker run --rm \
                            -v "$PWD":/usr/src \
                            sonarsource/sonar-scanner-cli \
                            -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                            -Dsonar.sources=src \
                            -Dsonar.java.binaries=target/classes \
                            -Dsonar.token=$SONAR_TOKEN \
                            -Dsonar.host.url=$SONAR_HOST_URL
                    '''
                }
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

        stage('🔐 Analyse sécurité OWASP') {
            steps {
                sh """
                    ./mvnw org.owasp:dependency-check-maven:check \
                        -Dformat=XML \
                        -DoutputDirectory=${OWASP_REPORT_DIR}
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${OWASP_REPORT_DIR}/dependency-check-report.xml", allowEmptyArchive: true
                }
            }
        }

        stage('🐳 Build Docker') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🛡️ Trivy – Analyse image Docker') {
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
                withCredentials([string(credentialsId: 'DOCKER-HUB-TOKEN', variable: 'DOCKER_HUB_TOKEN')]) {
                    sh '''
                        echo "$DOCKER_HUB_TOKEN" | docker login -u "$DOCKER_HUB_USER" --password-stdin
                        docker tag $IMAGE_TAG $IMAGE_FULL
                        docker push $IMAGE_FULL
                        docker logout
                    '''
                }
            }
        }

        stage('🧹 Nettoyage') {
            steps {
                sh '''
                    docker rmi ${IMAGE_TAG} || true
                    docker system prune -f
                '''
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
