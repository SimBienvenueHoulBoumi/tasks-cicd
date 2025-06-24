pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }
    options {
        timestamps()
        skipDefaultCheckout(false)
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        APP_NAME                 = 'tasks-cicd'  // Nom de l'application

        IMAGE_TAG                = "${APP_NAME}:${BUILD_NUMBER}"  // Tag de l'image Docker
        IMAGE_FULL               = "${HOST}:${NEXUS_PORT_DOCKER}/${APP_NAME}:${BUILD_NUMBER}"  // Nom complet de l'image Docker pour Nexus

        TRIVY_IMAGE              = 'aquasec/trivy:latest'  // Image Docker de Trivy
        TRIVY_REPORT_DIR         = 'trivy-reports'  // Répertoire pour les rapports Trivy
        TRIVY_SEVERITY           = 'CRITICAL,HIGH'  // Seuil de sévérité pour Trivy
        TRIVY_OUTPUT_FS          = '/root/reports/trivy-fs-report.json'  // Fichier de sortie pour l'analyse du système de fichiers
        TRIVY_OUTPUT_IMAGE       = '/root/reports/trivy-image-report.json'  // Fichier de sortie pour l'analyse de l'image Docker

        NEXUS_HOST               = 'localhost'  // Nom d'hôte du serveur Nexus
        NEXUS_PORT               = '8081'  // Port du serveur SonarQube
        NEXUS_PORT_DOCKER        = '8085'  // Port du serveur SonarQube pour Docker
        NEXUS_URL                = "http://${NEXUS_HOST}:${NEXUS_PORT}"  // URL de votre serveur Nexus
        NEXUS_REPO               = 'docker-hosted'  // Nom du dépôt Nexus pour Docker
        NEXUS_CREDENTIALS_ID     = 'NEXUS-CREDENTIAL'  // ID des credentials Jenkins pour Nexus

        SNYK_PROJET              = 'snyk-macos'  // Nom du projet Snyk
        SNYK_TOKEN_CREDENTIAL_ID = 'SNYK_AUTH_TOKEN'  // ID du token Jenkins pour Snyk
        SNYK_PLATEFORM_PROJECT   = "https://static.snyk.io/cli/latest/${SNYK_PROJET}"  // URL du binaire Snyk pour macOS
        SNYK_SEVERITY            = 'high'  // Seuil de sévérité pour Snyk
        SNYK_TARGET_FILE         = 'pom.xml'  // Fichier cible pour l'analyse Snyk
        SNYK_REPORT_FILE         = 'snyk_report.html'  // Nom du fichier de rapport Snyk

        GIT_REPO_URL            = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH              = '*/main'
        GITHUB_CREDENTIALS_ID   = 'GITHUB-CREDENTIALS'
    }

    stages {
        stage('📥 Checkout Git') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }

        stage('🔧 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "➡ Maven Wrapper manquant. Création..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        stage('🔧 Compilation + Package') {
            steps {
                sh './mvnw clean package'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
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

        stage('🧹 Checkstyle') {
            steps {
                sh './mvnw checkstyle:checkstyle'
            }
        }

        withCredentials([string(credentialsId: "${SNYK_TOKEN_CREDENTIAL_ID}", variable: 'SNYK_TOKEN')]) {
            sh '''
                curl -Lo snyk ${SNYK_PLATEFORM_PROJECT}
                chmod +x snyk
                ./snyk auth "$SNYK_TOKEN"
                ./snyk test \
                    --file=${SNYK_TARGET_FILE} \
                    --severity-threshold=${SNYK_SEVERITY} \
                    --report \
                    --format=html \
                    --report-file=${SNYK_REPORT_FILE} || true
            '''
        }

        stage('🐳 Build Docker') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🔍 Trivy - Analyse Code') {
            steps {
                sh '''
                    mkdir -p ${TRIVY_REPORT_DIR}
                    docker run --rm \
                        -v $(pwd):/project \
                        -v $(pwd)/${TRIVY_REPORT_DIR}:/root/reports \
                        ${TRIVY_IMAGE} fs /project \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output ${TRIVY_OUTPUT_FS}
                '''
            }
        }

        stage('🔍 Trivy - Analyse Image') {
            steps {
                sh '''
                    echo "🧹 Nettoyage du cache Java de Trivy (évite les erreurs de type 'context deadline exceeded')"
                    docker run --rm ${TRIVY_IMAGE} clean --java-db

                    echo "🔍 Lancement de l’analyse de l’image Docker avec Trivy"
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $(pwd)/${TRIVY_REPORT_DIR}:/root/reports \
                        ${TRIVY_IMAGE} image $IMAGE_TAG \
                        --timeout 10m \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output ${TRIVY_OUTPUT_IMAGE}
                '''
            }
        }

        stage('📁 Archive Rapports Trivy') {
            steps {
                archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/*.json", fingerprint: true
            }
        }


        stage('📦 Push vers Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${NEXUS_CREDENTIALS_ID}",
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo $PASS | docker login ${NEXUS_URL} -u $USER --password-stdin
                        docker tag $IMAGE_TAG $IMAGE_FULL
                        docker push $IMAGE_FULL
                        docker logout ${NEXUS_URL}
                    '''
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
