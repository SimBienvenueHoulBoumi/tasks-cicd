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
        GIT_REPO_URL         = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH           = '*/main'
        SONAR_PROJECT_KEY    = 'tasks-cicd'
        SONAR_HOST_URL       = 'http://localhost:9000'
        IMAGE_TAG            = "${APP_NAME}:${BUILD_NUMBER}"
        TRIVY_REPORT_DIR     = 'trivy-reports'
        GITHUB_CREDENTIALS_ID   = 'GITHUB-CREDENTIALS'
        NEXUS_URL = 'http://localhost:8081'
        NEXUS_REPO = 'docker-hosted'
        NEXUS_CREDENTIALS_ID = 'NEXUS-CREDENTIAL'
        SONARSERVER = 'SONARSERVER'
        SONARSCANNER = 'SONARSCANNER'
        SNYK = 'snyk'
    }

    stages {

        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }

        stage('🔧 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "➡ Maven Wrapper manquant. Génération..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        stage('🔧 Compilation Maven') {
            steps {
                sh './mvnw clean compile'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
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

        stage('🧹 Checkstyle Analysis') {
            steps {
                sh './mvnw checkstyle:checkstyle'
            }
        }

        stage('🛡️ Snyk Dependency Scan') {
            steps {
                snykSecurity (
                    severity: 'high',
                    snykInstallation: "${SNYK}",
                    snykTokenId: 'snyk-token',
                    targetFile: 'pom.xml',
                    monitorProjectOnBuild: true,
                    failOnIssues: true,
                    additionalArguments: '--report --format=html --report-file=snyk_report.html'
                )
            }
        }

        stage('🐳 Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🧪 Trivy – Analyse image Docker') {
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
                script {
                    def NEXUS_REPO_URL = "${NEXUS_URL}/repository/${NEXUS_REPO}"
                    def NEXUS_IMAGE = "localhost:8085/${APP_NAME}:${BUILD_NUMBER}"

                    withCredentials([usernamePassword(
                        credentialsId: "${NEXUS_CREDENTIALS_ID}",
                        usernameVariable: 'USER',
                        passwordVariable: 'PASS'
                    )]) {
                        sh """
                            echo \$PASS | docker login ${NEXUS_URL} -u \$USER --password-stdin
                            docker tag ${IMAGE_TAG} ${NEXUS_IMAGE}
                            docker push ${NEXUS_IMAGE}
                            docker logout ${NEXUS_URL}
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
