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
        // Nom de l'application
        APP_NAME             = 'tasks-cicd'

        // Références Git
        GIT_REPO_URL         = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH           = '*/main'

        // Clé projet SonarQube
        SONAR_PROJECT_KEY    = 'tasks-cicd'
        SONAR_HOST_URL       = 'http://host.docker.internal:9000'

        // Nom de l'image Docker locale (tag temporaire)
        IMAGE_TAG            = "${APP_NAME}:${BUILD_NUMBER}"

        // Dossiers de rapports
        TRIVY_REPORT_DIR     = 'trivy-reports'

        // Credentials Jenkins
        GITHUB_CREDENTIALS   = 'GITHUB-CREDENTIALS'
        NEXUS_CREDENTIALS    = 'NEXUS-CREDENTIAL'
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
                    if [ ! -f "./mvn" ]; then
                        echo "➡ Génération du Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('🔧 Compilation Maven') {
            steps {
                sh './mvn clean compile'
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
                sh './mvn clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('🐳 Build Docker Image') {
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

        stage('📦 Push Docker vers Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${NEXUS_CREDENTIALS}",
                    usernameVariable: 'NEXUS_USER',
                    passwordVariable: 'NEXUS_PASS'
                )]) {
                    script {
                        def NEXUS_REPO_HOST = "localhost:8083" // Adapter si exposé différemment
                        def NEXUS_REPO_NAME = "docker-hosted"  // Nom du repo Nexus Docker (à créer s’il n’existe pas)
                        def NEXUS_IMAGE     = "${NEXUS_REPO_HOST}/${NEXUS_REPO_NAME}/${APP_NAME}:${BUILD_NUMBER}"

                        echo "✅ Push image vers Nexus : ${NEXUS_IMAGE}"

                        sh """
                            echo "${NEXUS_PASS}" | docker login ${NEXUS_REPO_HOST} -u "${NEXUS_USER}" --password-stdin
                            docker tag ${IMAGE_TAG} ${NEXUS_IMAGE}
                            docker push ${NEXUS_IMAGE}
                            docker logout ${NEXUS_REPO_HOST}
                        """
                    }
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
