pipeline {
    agent { label 'Jenkins-agent' }

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
        APP_NAME                 = 'tasks-cicd'

        IMAGE_TAG                = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL               = "${HOST}:${NEXUS_PORT_DOCKER}/${APP_NAME}:${BUILD_NUMBER}"

        TRIVY_IMAGE              = 'aquasec/trivy:latest'
        TRIVY_REPORT_DIR         = 'trivy-reports'
        TRIVY_SEVERITY           = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS          = '/root/reports/trivy-fs-report.json'
        TRIVY_OUTPUT_IMAGE       = '/root/reports/trivy-image-report.json'

        NEXUS_HOST               = 'localhost'
        NEXUS_PORT               = '8081'
        NEXUS_PORT_DOCKER        = '8085'
        NEXUS_URL                = "http://${NEXUS_HOST}:${NEXUS_PORT}"
        NEXUS_REPO               = 'docker-hosted'
        NEXUS_CREDENTIALS_ID     = 'NEXUS-CREDENTIAL'

        SNYK_PROJET              = 'snyk-macos'
        SNYK_TOKEN_CREDENTIAL_ID = 'SNYK_AUTH_TOKEN'
        SNYK_PLATEFORM_PROJECT   = "https://static.snyk.io/cli/latest/${SNYK_PROJET}"
        SNYK_SEVERITY            = 'high'
        SNYK_TARGET_FILE         = 'pom.xml'
        SNYK_REPORT_FILE         = 'snyk_report.html'
    }

    stages {
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

        stage('🛡️ Analyse Snyk') {
            steps {
                withCredentials([string(credentialsId: "${SNYK_TOKEN_CREDENTIAL_ID}", variable: 'SNYK_TOKEN')]) {
                    sh '''
                        echo "[INFO] Téléchargement de Snyk CLI..."
                        curl -Lo snyk ${SNYK_PLATEFORM_PROJECT}
                        chmod +x snyk

                        echo "[INFO] Authentification avec le token..."
                        ./snyk auth "$SNYK_TOKEN"

                        echo "[INFO] Envoi du projet à Snyk Monitor..."
                        ./snyk monitor --file=${SNYK_TARGET_FILE} --project-name=${APP_NAME} || true

                        echo "[INFO] Analyse envoyée. Consulter sur : https://app.snyk.io/org/simbienvenuehoulboumi/projects"
                    '''
                }
            }
        }

        stage('🔧 Préparation de l’image Docker et 🐳 Build Image Docker') {
            steps {
                script {
                    def dockerfile = 'Dockerfile'
                    if (!fileExists(dockerfile)) {
                        error "❌ Le fichier ${dockerfile} est manquant. Veuillez vérifier votre dépôt."
                    } else {
                        echo "✅ Fichier ${dockerfile} trouvé. Début de la construction de l'image Docker..."
                    }
                }

                sh '''
                    echo "🐳 Construction de l'image Docker..."
                    docker build -t $IMAGE_TAG .
                '''
            }
        }

        stage('🔍 Trivy - Analyse Code') {
            steps {
                sh '''
                    echo "📂 Création du dossier de rapports Trivy..."
                    mkdir -p ${TRIVY_REPORT_DIR}

                    echo "🔍 Analyse de la base de code avec Trivy..."
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
                    echo "🧹 Nettoyage du cache Java de Trivy (évite les erreurs context deadline)..."
                    docker run --rm ${TRIVY_IMAGE} clean --java-db

                    echo "🔍 Analyse de l'image Docker avec Trivy..."
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
       // ✅ Publication avenir des logs vers ELK (ElasticSearch, Logstash, Kibana)

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
