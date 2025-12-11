pipeline {
    agent {
        node {
            label 'jenkins-agent'
            // Workspace sur l'agent Docker
            customWorkspace '/home/jenkins/agent'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    environment {
        APP_NAME         = "tasks-cicd"
        DOCKER_HOST      = "tcp://dind:2375"
        IMAGE_TAG        = "${APP_NAME}:${BUILD_NUMBER}"
        PROJECT_NAME     = "task-rest-api"
        PROJECT_VERSION  = "0.0.1"

        NEXUS_URL        = "http://nexus:8082"
        IMAGE_FULL       = "simdev/${PROJECT_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        SONAR_SERVER   = "SonarQube"
        SONAR_URL      = "http://sonarqube:9000"

        SNYK           = "snyk"
        TRIVY_URL      = "http://trivy:4954/scan"
    }

    stages {
        stage('📥 Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git',
                        credentialsId: 'JENKINS_AGENT'
                    ]]
                ])
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

        stage('🔐 Snyk Scan') {
            steps {
                withCredentials([string(credentialsId: 'SNYK_TOKEN', variable: 'SNYK_TOKEN')]) {
                    sh '''
                        mkdir -p reports/snyk

                        # Lancement de Snyk via l'image Docker officielle
                        docker run --rm \
                          -e SNYK_TOKEN=$SNYK_TOKEN \
                          -v "$(pwd)":/project \
                          -w /project \
                          snyk/snyk:docker \
                          snyk test --severity-threshold=high --file=pom.xml --json > reports/snyk/snyk-report.json || true

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


        // stage('🏗️ Build') {
        //     steps {
        //         sh './mvnw package -DskipTests'
        //     }
        //     post {
        //         success {
        //             archiveArtifacts artifacts: 'target/*.jar'
        //         }
        //     }
        // }

        // stage('🐳 Docker Build') {
        //     steps {
        //         sh """
        //             docker build -t ${IMAGE_TAG} .
        //             docker tag ${IMAGE_TAG} ${IMAGE_FULL}
        //         """
        //     }
        // }

        // stage('🔬 Trivy') {
        //     steps {
        //         sh '''
        //             mkdir -p reports/trivy
        //             curl -s -X POST http://trivy:4954/scan \
        //                 -H 'Content-Type: application/json' \
        //                 -d "{
        //                     \\\"image_name\\\": \\\"${IMAGE_TAG}\\\",\
        //                     \\\"scan_type\\\": \\\"image\\\",\
        //                     \\\"vuln_type\\\": [\\\"os\\\", \\\"library\\\"],\
        //                     \\\"severity\\\": [\\\"CRITICAL\\\", \\\"HIGH\\\"]\
        //                 }" > reports/trivy/trivy-report.json

        //             python3 scripts/generate_trivy_report.py reports/trivy/trivy-report.json reports/trivy/trivy-report.html
        //         '''
        //     }
        //     post {
        //         always {
        //             archiveArtifacts artifacts: 'reports/trivy/*.*', allowEmptyArchive: true
        //         }
        //     }
        // }

        // stage('📦 Push to Nexus') {
        //     steps {
        //         withCredentials([usernamePassword(
        //             credentialsId: "${NEXUS_CREDENTIALS}",
        //             usernameVariable: 'USER',
        //             passwordVariable: 'PASS'
        //         )]) {
        //             sh '''
        //                 echo "$PASS" | docker login http://nexus:8082 -u "$USER" --password-stdin
        //                 docker tag ${IMAGE_TAG} ${IMAGE_FULL}
        //                 docker push ${IMAGE_FULL}
        //                 docker logout http://nexus:8082
        //             '''

        //         }
        //     }
        // }

        // stage('🧹 Cleanup') {
        //     steps {
        //         sh '''
        //             echo "[INFO] Suppression des images..."
        //             docker rmi ${IMAGE_TAG} || true
        //             docker rmi ${IMAGE_FULL} || true

        //             echo "[INFO] Suppression des conteneurs stoppés..."
        //             docker container prune -f || true

        //             echo "[INFO] Suppression des volumes inutilisés..."
        //             docker volume prune -f || true

        //             echo "[INFO] Nettoyage du système (réseaux, build cache, etc)..."
        //             docker system prune -af --volumes || true
        //         '''
        //     }
        // }

    }

    post {
        failure {
            echo "[Pipeline] ❌ Build échoué — pensez à consulter les logs et rapports."
        }
        // always {
        //     // Désactivé pour éviter les erreurs de contexte (hudson.FilePath manquant)
        //     // Si besoin, déplacer l'archiveArtifacts dans un stage avec un agent/node explicite.
        //     archiveArtifacts artifacts: '**/*.log', allowEmptyArchive: true
        // }
    }
}
