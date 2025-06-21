/**
 * 🔧 Jenkinsfile pour projet Java Spring Boot
 * ➕ Build Maven, Tests, SonarQube, Image Docker
 */

pipeline {

    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'       // JDK 17 (défini dans Jenkins Global Tools)
        maven 'maven'   // Maven 3.9
    }

    environment {
        DOCKER_IMAGE = 'simbienvenuehoulboumi/tasks-cicd:latest' // Nom de l'image Docker
        SONAR_HOST_URL = 'http://localhost:9000/'
        SONAR_TOKEN    = credentials('SONAR_TOKEN') // Token SonarQube stocké dans Jenkins Credentials
        AGENT_CREDENTIALS = 'JENKINS-AGENT-CREDENTIALS' // Credentials pour l'agent Jenkins
    }

    stages {

        stage('✅ Vérification des variables') {
            steps {
                echo "🧪 Vérif des variables d’environnement..."
                echo "DOCKER_IMAGE       = ${env.DOCKER_IMAGE}"
            }
        }

        stage('📥 Checkout Git') {
            steps {
                git credentialsId: "${AGENT_CREDENTIALS}",
                    url: 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git',
                    branch: 'main'
            }
        }

        stage('🔧 Générer Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ]; then
                        echo "➡ Maven Wrapper manquant. Génération..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        stage('🔨 Compilation') {
            steps {
                sh './mvnw clean install -DskipTests'
            }
        }

        stage('🧪 Tests') {
            steps {
                sh 'mvn verify'
                junit 'target/surefire-reports/*.xml'
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                sh """
                    ./mvnw sonar:sonar \
                        -Dsonar.projectKey=tasks \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.login=${SONAR_TOKEN}
                """
            }
        }

        /**
         * 🐳 Build Docker
         * Construit l’image Docker avec le Dockerfile présent dans le repo
         */
        stage('🐳 Build Docker') {
            steps {
                sh """
                    docker build -t ${DOCKER_IMAGE} .
                """
            }
        }

        stage('🛡️ Scan sécurité Trivy (Image)') {
            steps {
                sh '''
                    mkdir -p trivy-reports
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $PWD/trivy-reports:/root/reports \
                        aquasec/trivy:latest image \
                        --exit-code 1 \
                        --severity CRITICAL,HIGH \
                        --format json \
                        --output /root/reports/trivy-image-report.json \
                        ${DOCKER_IMAGE}
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-reports/trivy-image-report.json', allowEmptyArchive: true
                }
                failure {
                    echo '❌ Scan Trivy (image) a trouvé des vulnérabilités critiques ou hautes.'
                }
            }
        }

        stage('🧬 Scan sécurité Trivy (Code Source)') {
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

    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès"
        }
        failure {
            echo "❌ Pipeline échoué"
        }
        always {
            cleanWs()
        }
    }
}
