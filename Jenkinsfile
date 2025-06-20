/**
 * 🛠️ Pipeline Jenkins complet pour un projet Java Spring Boot.
 * Ce pipeline est exécuté sur un agent nommé 'jenkins-agent' et utilise Maven et JDK.
 *
 * Objectifs :
 * - Compiler l'application
 * - Lancer les tests
 * - Vérifier le style de code
 * - Analyser la qualité avec SonarQube
 * - Scanner les dépendances avec Snyk
 */
pipeline {

    /** 
     * 🎯 Spécifie sur quel agent Jenkins ce pipeline doit s'exécuter.
     * 'jenkins-agent' est un nom logique, défini dans la configuration Jenkins.
     */
    agent { label 'jenkins-agent' }

    /**
     * 🔧 Outils nécessaires pour les étapes suivantes du pipeline.
     * Ils doivent être installés et configurés dans Jenkins (Manage Jenkins > Global Tool Configuration).
     */
    tools {
        jdk 'jdk'         // Java Development Kit (version 17)
        maven 'maven'     // Apache Maven (version 3.9)
    }

    /**
     * 📦 Début des étapes du pipeline (appelées "stages").
     * Chaque stage exécute une tâche spécifique dans le cycle de vie CI/CD.
     */
    stages {

        /**
         * 📥 Étape de récupération du code source depuis le dépôt Git.
         * Jenkins utilise automatiquement l'URL du dépôt configurée dans le job.
         */

        stage('📥 Checkout privé GitHub') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git',
                        credentialsId: 'github-agent'
                    ]]
                ])
            }
        }

                /**
         * 🛠️ Étape pour générer un Maven Wrapper si jamais il est absent.
         * Le Maven Wrapper permet d’utiliser la bonne version de Maven même si elle n’est pas installée localement.
         */
        stage('🛠️ Générer Maven Wrapper si absent') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "➡ Maven Wrapper manquant. Génération..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        /**
         * 🔧 Étape de compilation du code source Java avec Maven.
         * Les tests sont ignorés ici pour se concentrer sur la construction (build).
         */
        stage('🔧 Build') {
            steps {
                sh 'mvn clean install -DskipTests'
            }
            post {
                success {
                    echo "✅ Build réussi - Archivage des artefacts..."
                    archiveArtifacts artifacts: 'target/*.jar' // 📦 Sauvegarde du fichier .jar généré
                }
            }
        }

        /**
         * 🧪 Étape d’exécution des tests unitaires avec Maven.
         * Les résultats seront utilisés plus tard pour SonarQube.
         */
        stage('🧪 Tests') {
            steps {
                sh 'mvn test'
            }
        }

        /**
         * 🧹 Étape pour vérifier la qualité du code avec Checkstyle.
         * Cela détecte des erreurs de style comme des noms de classes incorrects ou des indentations non conformes.
         */
        stage('🧹 Checkstyle Analysis') {
            steps {
                sh 'mvn checkstyle:checkstyle'
            }
        }

    }
    post {
        failure {
            echo "❌ Échec du pipeline."
        }
        always {
            cleanWs()
        }
    }
}
