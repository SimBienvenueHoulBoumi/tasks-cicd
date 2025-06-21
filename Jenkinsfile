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
        SONARQUBE_INSTANCE = 'sonarserver'
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

        stage('📊 Analyse SonarQube') {
            steps {
                withSonarQubeEnv('sonarserver') {
                    withCredentials([string(credentialsId: 'SONAR-TOKEN', variable: 'SONAR_TOKEN')]) {
                        script {
                            def scannerHome = tool name: 'sonarscanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                            sh """
                                ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=demo-rest-api \
                                -Dsonar.projectName=demo-rest-api \
                                -Dsonar.projectVersion=0.0.1 \
                                -Dsonar.sources=src \
                                -Dsonar.java.binaries=target/classes \
                                -Dsonar.junit.reportsPath=target/surefire-reports \
                                -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                                -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml \
                                -Dsonar.token=$SONAR_TOKEN
                            """
                        }
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
