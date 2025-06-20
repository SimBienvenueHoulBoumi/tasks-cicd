/**
 * 🔧 Jenkinsfile complet pour un projet Java Spring Boot.
 * Ce pipeline CI/CD compile, teste, analyse la qualité du code via SonarQube,
 * puis construit une image Docker.
 *
 * Configuration sans interface Jenkins : tout est automatique via docker-compose.
 */
pipeline {

    /**
     * 🏗️ Agent d’exécution utilisé.
     * Il doit correspondre à un agent Jenkins Docker nommé "jenkins-agent".
     */
    agent { label 'jenkins-agent' }

    /**
     * 🧰 Déclare les outils requis.
     * Ceux-ci doivent être installés via "Manage Jenkins > Global Tool Configuration".
     */
    tools {
        jdk 'jdk'         // JDK 17
        maven 'maven'     // Maven 3.9
    }

    /**
     * 🌍 Variables d’environnement du pipeline.
     * - SONAR_TOKEN : transmis par le conteneur Jenkins via docker-compose.
     * - SONAR_HOST_URL : même chose, évite toute configuration via l'IHM Jenkins.
     * - DOCKER_IMAGE : nom final de l’image Docker générée.
     */
    environment {
        SONAR_TOKEN     = "${env.SONAR_TOKEN}"      // Injecté via docker-compose.yml
        SONAR_HOST_URL  = "${env.SONAR_HOST_URL}"   // Injecté via docker-compose.yml
        DOCKER_IMAGE    = "sim/tasks-app:latest"    // Nom de l’image Docker
    }

    /**
     * 📦 Étapes principales du pipeline.
     */
    stages {

        stage('📥 Checkout Git') {
            steps {
                // 🔄 Récupère le code source depuis GitHub
                git url: 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git', branch: 'main'
            }
        }

        stage('🛠️ Générer Maven Wrapper si absent') {
            steps {
                // 🔧 Permet d’assurer la cohérence de version Maven
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

        stage('🔧 Build') {
            steps {
                // ⚙️ Compile le projet sans exécuter les tests
                sh './mvnw clean install -DskipTests'
            }
        }

        stage('🧪 Tests') {
            steps {
                // ✅ Lance les tests unitaires
                sh './mvnw test'
                // 📄 Publie les rapports JUnit dans l’interface Jenkins
                junit 'target/surefire-reports/*.xml'
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                // 🔍 Analyse du code source avec SonarQube (sans withSonarQubeEnv)
                sh """
                    ./mvnw sonar:sonar \
                        -Dsonar.projectKey=tasks \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.login=${SONAR_TOKEN}
                """
            }
        }

        stage('🐳 Build Docker Image') {
            steps {
                // 🐳 Construit l’image Docker locale à partir du Dockerfile
                script {
                    docker.build(env.DOCKER_IMAGE)
                }
            }
        }

        /*
        // (Optionnel) stage : 📤 Pousser l’image sur Docker Hub
        stage('📤 Push Docker Image') {
            environment {
                REGISTRY_CREDENTIALS = credentials('docker-registry-token')
            }
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'REGISTRY_CREDENTIALS') {
                        docker.image(env.DOCKER_IMAGE).push()
                    }
                }
            }
        }
        */
    }

    /**
     * ✅ Hooks post-exécution : succès, échec, toujours
     */
    post {
        success {
            echo "✅ Pipeline terminé avec succès !"
        }
        failure {
            echo "❌ Échec du pipeline."
        }
        always {
            // 🧼 Nettoie l’espace de travail Jenkins pour le job suivant
            cleanWs()
        }
    }
}
