pipeline {
    agent {
        node {
            label 'jenkins-agent'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        // On désactive le checkout SCM automatique
        skipDefaultCheckout(true)
    }

    environment {
        APP_NAME         = "tasks-cicd"
        IMAGE_TAG        = "${APP_NAME}:${BUILD_NUMBER}"
        PROJECT_NAME     = "task-rest-api"
        PROJECT_VERSION  = "0.0.1"

        // Nexus Docker registry (port 8083 exposé vers 8082 interne 8081 UI / 8082 HTTP repos)
        NEXUS_HOST       = "localhost:8083"
        NEXUS_URL        = "http://${NEXUS_HOST}"
        IMAGE_FULL       = "${NEXUS_HOST}/simdev/${PROJECT_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        SONAR_SERVER   = "SonarQube"
        SONAR_URL      = "http://sonarqube:9000"

        SNYK           = "snyk"
        TRIVY_URL      = "http://trivy:4954/scan"
    }

    stages {
        stage('📥 Checkout') {
            steps {
                // Nettoyage du workspace puis clonage via le step Git intégré
                deleteDir()
                git branch: 'main',
                    url: 'git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git',
                    credentialsId: 'JENKINS_AGENT'
            }
        }
        stage('🧪 Tests') {
            steps {
                sh './mvnw verify'
            }
            post {
                always {
                    junit testResults: 'target/surefire-reports/*.xml', allowEmptyResults: true
                    // Pas de publishHTML: plugin HTML Publisher non installé
                }
            }
        }

        stage('📊 SonarQube') {
            steps {
                echo '[Étape 1] Vérification DNS SonarQube'
                sh '''
                    echo "[INFO] Test DNS SonarQube avec curl"
                    curl -v http://sonarqube:9000/api/system/status || echo "ECHEC"
                '''

                echo '[Étape 2] Analyse SonarQube'
                withCredentials([string(credentialsId: 'SONARTOKEN', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        ./mvnw clean verify sonar:sonar \
                            -Dsonar.host.url=$SONAR_URL \
                            -Dsonar.login=$SONAR_TOKEN \
                            -Dsonar.projectKey=task-rest-api \
                            -Dsonar.projectName=task-rest-api \
                            -Dsonar.projectVersion=0.0.1 \
                            -Dsonar.sources=src/ \
                            -Dsonar.java.binaries=target/classes \
                            -Dsonar.junit.reportsPath=target/surefire-reports/ \
                            -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                            -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml \
                            -Dsonar.exclusions=**/target/**,**/test/**,**/*.json,**/*.yml
                    '''
                }
            }
        }

        stage('🏗️ Build') {
            steps {
                sh './mvnw package -DskipTests'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('🐳 Docker Build') {
            steps {
                sh """
                    docker build -t ${IMAGE_TAG} .
                    docker tag ${IMAGE_TAG} ${IMAGE_FULL}
                """
            }
        }

        stage('🔐 Snyk Scan') {
            steps {
                withCredentials([string(credentialsId: 'SNYK_TOKEN', variable: 'SNYK_TOKEN')]) {
                    sh '''
                        mkdir -p reports/snyk

                        # Lancement de Snyk via le CLI installé dans l'agent (plus besoin de Docker in Docker)
                        export SNYK_TOKEN="$SNYK_TOKEN"
                        snyk test --severity-threshold=high --file=pom.xml --json > reports/snyk/snyk-report.json || true

                        # Envoi d'un snapshot vers Snyk SaaS pour visualisation dans app.snyk.io
                        snyk monitor --file=pom.xml --project-name=task-rest-api || true

                        # Génération d'un rapport HTML lisible avec un style inspiré de TailwindCSS
                        python3 scripts/generate_snyk_report.py || true

                        # Si tu as l'outil snyk-to-html dans ton image, tu peux générer un rapport HTML.
                        # Pour l'instant on archive surtout le JSON.
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/snyk/snyk-report.*', allowEmptyArchive: true
                }
            }
        }

        stage('🔬 Trivy') {
            steps {
                sh '''
                    mkdir -p reports/trivy
                    # Scan de l'image Docker locale avec Trivy CLI (plus simple que le mode serveur HTTP)
                    trivy image --severity CRITICAL,HIGH --format json -o reports/trivy/trivy-report.json ${IMAGE_TAG} || true

                    python3 scripts/generate_trivy_report.py reports/trivy/trivy-report.json reports/trivy/trivy-report.html || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/trivy/*.*', allowEmptyArchive: true
                }
            }
        }

        stage('📦 Push to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${NEXUS_CREDENTIALS}",
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo "$PASS" | docker login ${NEXUS_URL} -u "$USER" --password-stdin
                        docker tag ${IMAGE_TAG} ${IMAGE_FULL}
                        docker push ${IMAGE_FULL}
                        docker logout ${NEXUS_URL}
                    '''

                }
            }
        }

        stage('🧹 Cleanup') {
            steps {
                sh '''
                    echo "[INFO] Suppression des images..."
                    docker rmi ${IMAGE_TAG} || true
                    docker rmi ${IMAGE_FULL} || true

                    echo "[INFO] Suppression des conteneurs stoppés..."
                    docker container prune -f || true

                    echo "[INFO] Suppression des volumes inutilisés..."
                    docker volume prune -f || true

                    echo "[INFO] Nettoyage du système (réseaux, build cache, etc)..."
                    docker system prune -af --volumes || true
                '''
            }
        }

    }

    post {
        failure {
            echo "[Pipeline] ❌ Build échoué — pensez à consulter les logs et rapports."
        }
        always {
            // Désactivé pour éviter les erreurs de contexte (hudson.FilePath manquant)
            // Si besoin, déplacer l'archiveArtifacts dans un stage avec un agent/node explicite.
            archiveArtifacts artifacts: '**/*.log', allowEmptyArchive: true
        }
    }
}
