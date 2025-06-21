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
                git credentialsId: 'JENKINS-AGENT-CREDENTIALS',
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
                sh './mvnw test'
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

        stage('🐳 Build Docker') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}")
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
