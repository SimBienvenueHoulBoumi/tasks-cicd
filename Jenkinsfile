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
        SONAR_TOKEN     = "${env.SONAR_TOKEN}"        // Injecté via docker-compose
        SONAR_HOST_URL  = "${env.SONAR_HOST_URL}"     // Injecté via docker-compose
        DOCKER_IMAGE    = "tasks-app:latest"          // 📦 Nom de l’image locale
    }

    stages {

        stage('✅ Vérification des variables') {
            steps {
                echo "🧪 Vérif des variables d’environnement..."
                echo "SONAR_TOKEN défini ? ${env.SONAR_TOKEN != null}"
                echo "SONAR_HOST_URL     = ${env.SONAR_HOST_URL}"
                echo "DOCKER_IMAGE       = ${env.DOCKER_IMAGE}"
            }
        }

        stage('📥 Checkout Git') {
            steps {
                git url: 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git', branch: 'main'
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

        /*
        stage('📤 Push Docker Image') {
            environment {
                REGISTRY_CREDENTIALS = credentials('docker-hub-creds')
            }
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'REGISTRY_CREDENTIALS') {
                        docker.image("${DOCKER_IMAGE}").push()
                    }
                }
            }
        }
        */
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
