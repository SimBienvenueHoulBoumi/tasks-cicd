/**
 * 🔧 Jenkinsfile – Pipeline CI/CD Spring Boot
 * Étapes : Checkout | Analyse SonarQube | Build & Tests | Sécurité | Docker | Trivy | Nettoyage
 */

pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'           // 🔧 JDK configuré dans Jenkins
        maven 'maven'       // 🔧 Maven configuré dans Jenkins
    }

    environment {
        // 🔖 Variables de projet
        APP_NAME = 'tasks-cicd'
        SONAR_PROJECT_KEY = 'tasks'
        GIT_REPO_URL = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH = '*/main'
        SONAR_HOST_URL = 'http://localhost:9000'
        DOCKER_HUB_USER = 'brhulla@gmail.com'
        DOCKER_HUB_NAMESPACE = 'docker.io/brhulla'
        TRIVY_REPORT_DIR = 'trivy-reports'
        OWASP_REPORT_DIR = 'dependency-report'
        IMAGE_TAG = "${APP_NAME}:${BUILD_NUMBER}"
        GITHUB_CREDENTIALS = 'GITHUB-CREDENTIALS'
        IMAGE_FULL = "${DOCKER_HUB_NAMESPACE}/${APP_NAME}:${BUILD_NUMBER}"
        SONARQUBE_INSTANCE = 'sonarserver' // 🔧 Nom du serveur SonarQube configuré dans Jenkins
    }

    options {
        skipDefaultCheckout true
        timestamps()
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

        stage('📊 SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('sonarserver') {
                        sh '''
                            sonar-scanner \
                            -Dsonar.projectKey=tasks \
                            -Dsonar.projectName=tasks \
                            -Dsonar.projectVersion=0.0.1 \
                            -Dsonar.sources=src/main/java \
                            -Dsonar.tests=src/test/java \
                            -Dsonar.java.binaries=target/classes \
                            -Dsonar.junit.reportsPath=target/surefire-reports/ \
                            -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                            -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml \
                            -Dsonar.token=$SONAR_TOKEN
                        '''
                    }
                }
            }
        }

        stage('🔧 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "mvnw" ]; then
                        echo "➡ Génération du Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('🔨 Build & Tests') {
            steps {
                sh 'mvn clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('🔐 Analyse sécurité OWASP') {
            steps {
                sh '''
                    mvn org.owasp:dependency-check-maven:check \
                        -Dformat=XML \
                        -DoutputDirectory=$OWASP_REPORT_DIR
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: "$OWASP_REPORT_DIR/dependency-check-report.xml", allowEmptyArchive: true
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
                sh '''
                    mkdir -p $TRIVY_REPORT_DIR
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $PWD/$TRIVY_REPORT_DIR:/root/reports \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity CRITICAL,HIGH \
                        --format json \
                        --output /root/reports/trivy-image-report.json \
                        $IMAGE_TAG
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: "$TRIVY_REPORT_DIR/trivy-image-report.json", allowEmptyArchive: true
                }
                failure {
                    echo '🚨 Vulnérabilités critiques détectées dans l’image Docker.'
                }
            }
        }

        stage('🧬 Trivy – Analyse code source') {
            steps {
                sh '''
                    docker run --rm \
                        -v $PWD:/project \
                        -v $PWD/$TRIVY_REPORT_DIR:/root/reports \
                        aquasec/trivy:latest fs /project \
                        --exit-code 0 \
                        --format json \
                        --output /root/reports/trivy-fs-report.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: "$TRIVY_REPORT_DIR/trivy-fs-report.json", allowEmptyArchive: true
                }
            }
        }

        stage('🧹 Nettoyage') {
            steps {
                sh '''
                    docker rmi $IMAGE_TAG || true
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
            node('jenkins-agent') {
                cleanWs()
            }
        }
    }
}
