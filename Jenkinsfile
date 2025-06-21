pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }

    environment {
        APP_NAME = 'tasks'
        SONAR_PROJECT_KEY = 'tasks'
        GIT_REPO_URL = 'https://github.com/SimBienvenueHoulBoumi/tasks.git'
        GIT_BRANCH = '*/main'
        SONAR_HOST_URL = 'http://localhost:9000'
        DOCKER_HUB_USER = 'brhulla@gmail.com'
        DOCKER_HUB_NAMESPACE = 'docker.io/brhulla'
        TRIVY_REPORT_DIR = 'trivy-reports'
        OWASP_REPORT_DIR = 'dependency-report'
        IMAGE_TAG = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL = "${DOCKER_HUB_NAMESPACE}/${APP_NAME}:${BUILD_NUMBER}"
        GITHUB_CREDENTIALS = 'GITHUB-CREDENTIALS' // Assure-toi que cet ID existe bien aussi
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

        stage('🧹 Checkstyle Analysis') {
            steps {
                sh 'mvn checkstyle:checkstyle'
            }
        }

        stage('📊 SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('sonarserver') {
                        sh '''
                            mvn clean verify sonar:sonar \
                                -Dsonar.projectKey=tasks \
                                -Dsonar.projectName=tasks \
                                -Dsonar.projectVersion=0.0.1 \
                                -Dsonar.sources=src/ \
                                -Dsonar.java.binaries=target/test-classes/simple/tasks/services \
                                -Dsonar.junit.reportsPath=target/surefire-reports/ \
                                -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                                -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml \
                                -Dsonar.token=$SONAR_TOKEN
                        '''
                    }
                }

            }
        }

        // Autres stages ici (Build, Docker, Trivy, etc.)
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
