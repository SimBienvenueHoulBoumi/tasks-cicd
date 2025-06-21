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
        APP_NAME = 'tasks-cicd'
        IMAGE_TAG = "${APP_NAME}:${BUILD_NUMBER}"
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_TOKEN = credentials('SONAR_TOKEN')
        AGENT_CREDENTIALS = 'JENKINS-AGENT-CREDENTIALS'
    }

    options {
        skipDefaultCheckout true
        timestamps()
    }

    stages {

        stage('✅ Vérification des variables') {
            steps {
                echo "🔍 Docker image   : ${IMAGE_TAG}"
                echo "🔍 SonarQube URL  : ${SONAR_HOST_URL}"
            }
        }

        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git',
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
                    sh '''
                        ./mvnw sonar:sonar \
                            -Dsonar.projectKey=tasks \
                            -Dsonar.host.url=${SONAR_HOST_URL} \
                            -Dsonar.token=${SONAR_TOKEN}
                    '''
                }
            }
        }

        stage('⏳ Quality Gate') {
            steps {
                waitForQualityGate abortPipeline: true
            }
        }

        stage('🔐 Analyse sécurité OWASP') {
            steps {
                sh 'mvn org.owasp:dependency-check-maven:check -Dformat=XML -DoutputDirectory=dependency-report'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dependency-report/dependency-check-report.xml', allowEmptyArchive: true
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
                sh '''
                    mkdir -p trivy-reports
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $PWD/trivy-reports:/root/reports \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity CRITICAL,HIGH \
                        --format json \
                        --output /root/reports/trivy-image-report.json \
                        ${IMAGE_TAG}
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-reports/trivy-image-report.json', allowEmptyArchive: true
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
                        -v $PWD/trivy-reports:/root/reports \
                        aquasec/trivy:latest fs /project \
                        --exit-code 0 \
                        --format json \
                        --output /root/reports/trivy-fs-report.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-reports/trivy-fs-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('🚀 Push Docker vers DockerHub') {
            environment {
                REGISTRY = 'docker.io/simbienvenuehoulboumi'
                IMAGE_FULL = "${REGISTRY}/${IMAGE_TAG}"
            }
            steps {
               withCredentials(
                [string(
                    credentialsId: 'DOCKER_HUB_TOKEN', 
                    variable: 'DOCKER_TOKEN')]) {
                        sh '''
                            echo "$DOCKER_TOKEN" | docker login -u "brhulla@gmail.com" --password-stdin
                            docker tag ${IMAGE_TAG} docker.io/simbienvenuehoulboumi/${IMAGE_TAG}
                            docker push docker.io/simbienvenuehoulboumi/${IMAGE_TAG}
                            docker logout
                        '''
                }

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
 