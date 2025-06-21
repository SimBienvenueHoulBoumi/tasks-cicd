/**
 * 🔧 Jenkinsfile – CI/CD pour Spring Boot
 * 📦 Build & Tests | 📊 SonarQube | 🔐 Sécu (Trivy/OWASP) | 🐳 Docker
 * 📁 Repo : https://github.com/SimBienvenueHoulBoumi/tasks-cicd
 */

pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'         // Déclaré dans Jenkins > Global Tools > JDK
        maven 'maven'     // Idem pour Maven
        git 'Default'         // Ajoute un outil Git si "Selected Git installation does not exist"
    }

    environment {
        // 🏷️ Infos projet
        APP_NAME = 'tasks-cicd'
        GIT_REPO_URL = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH = '*/main'

        // 📊 SonarQube
        SONAR_PROJECT_KEY = 'tasks'
        SONAR_HOST_URL = 'http://localhost:9000'
        SONARQUBE_INSTANCE = 'sonarserver'        // Doit correspondre au nom configuré dans Jenkins > SonarQube

        // 🔐 Credentials (Jenkins > Credentials > Global)
        GITHUB_CREDENTIALS = 'GITHUB-CREDENTIALS'
        SONAR_TOKEN = credentials('SONAR_TOKEN')  // Injecté automatiquement

        // 🐳 Docker
        DOCKER_HUB_USER = 'brhulla@gmail.com'
        DOCKER_HUB_NAMESPACE = 'docker.io/brhulla'
        IMAGE_TAG = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL = "${DOCKER_HUB_NAMESPACE}/${APP_NAME}:${BUILD_NUMBER}"

        // 📄 Sécurité
        TRIVY_REPORT_DIR = 'trivy-reports'
        OWASP_REPORT_DIR = 'dependency-report'
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
                withSonarQubeEnv("${SONARQUBE_INSTANCE}") {
                    sh '''
                        mvn clean verify sonar:sonar \
                            -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                            -Dsonar.host.url=$SONAR_HOST_URL \
                            -Dsonar.token=$SONAR_TOKEN
                    '''
                }
            }
        }

        stage('🔧 Génération Maven Wrapper (si absent)') {
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

        stage('🔐 OWASP Dependency Check') {
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

        stage('🐳 Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🛡️ Analyse Docker avec Trivy') {
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

        stage('🧬 Analyse Code Source avec Trivy') {
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
            cleanWs()
        }
    }
}
