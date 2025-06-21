/**
 * 🔧 Jenkinsfile – Pipeline CI/CD Spring Boot
 * 📦 Maven build | 🧪 Tests | 📊 SonarQube | 🐳 Docker | 🔐 Sécurité (Trivy, OWASP)
 */

pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }

    environment {
        // 🏷️ Infos projet
        APP_NAME = 'tasks-cicd'
        SONAR_PROJECT_KEY = 'tasks'
        GIT_REPO_URL = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH = '*/main'

        // 📊 SonarQube
        SONAR_HOST_URL = 'http://localhost:9000'

        // 🐳 Docker
        DOCKER_HUB_USER = 'brhulla@gmail.com'
        DOCKER_HUB_NAMESPACE = 'docker.io/brhulla'

        // 🔒 Credentials
        GITHUB-CREDENTIALS = 'GITHUB-CREDENTIALS'

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

    stages('🚀 Initialisation') {

        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO_URL}",
                        credentialsId: "${GITHUB-CREDENTIALS}"
                    ]]
                ])
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_TOKEN')]) {
                withSonarQubeEnv('sonarserver') {
                    sh '''
                    mvn clean verify sonar:sonar \
                        -Dsonar.projectKey=simple:tasks \
                        -Dsonar.host.url=http://localhost:9000 \
                        -Dsonar.token=$SONAR_TOKEN
                    '''
                }
                }
           }
        }


        stage('🔧 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "mvn" ]; then
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

        post {
            failure {
                echo '❌ Échec de l’analyse de SonarQube. Vérifiez le token, l’URL du serveur, et les permissions du projet.'
            }
            always {
                archiveArtifacts artifacts: '**/report-task.txt', allowEmptyArchive: true
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

    stage('🛡️ Trivy – Analyse image') {
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


