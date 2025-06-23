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
        APP_NAME                 = 'tasks-cicd'
        GIT_REPO_URL             = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH               = '*/main'
        GITHUB_CREDENTIALS_ID    = 'GITHUB-CREDENTIALS'

        SONAR_PROJECT_KEY        = 'tasks-cicd'
        SONAR_HOST_URL           = 'http://localhost:9000'
        SONAR_TOKEN_CREDENTIAL_ID = 'SONARQUBE-JENKINS-TOKEN'
        SONAR_SCANNER_IMAGE      = 'sonarsource/sonar-scanner-cli'

        IMAGE_TAG                = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL               = "localhost:8085/${APP_NAME}:${BUILD_NUMBER}"

        TRIVY_IMAGE              = 'aquasec/trivy:latest'
        TRIVY_REPORT_DIR         = 'trivy-reports'
        TRIVY_SEVERITY           = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS          = '/root/reports/trivy-fs-report.json'
        TRIVY_OUTPUT_IMAGE       = '/root/reports/trivy-image-report.json'

        NEXUS_URL                = 'http://localhost:8081'
        NEXUS_REPO               = 'docker-hosted'
        NEXUS_CREDENTIALS_ID     = 'NEXUS-CREDENTIAL'

        SNYK_BIN                 = 'snyk'
        SNYK_TOKEN_CREDENTIAL_ID = 'SNYK_AUTH_TOKEN'
        SNYK_SEVERITY            = 'high'
        SNYK_TARGET_FILE         = 'pom.xml'
        SNYK_REPORT_FILE         = 'snyk_report.html'
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

        stage('🛡️ Analyse Snyk') {
            steps {
                withCredentials([string(credentialsId: "${SNYK_TOKEN_CREDENTIAL_ID}", variable: 'SNYK_TOKEN')]) {
                    sh '''
                        curl -Lo snyk https://static.snyk.io/cli/latest/snyk-macos
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
            }
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

        stage('📊 Analyse SonarQube') {
            steps {
                withCredentials([string(credentialsId: "${SONAR_TOKEN_CREDENTIAL_ID}", variable: "${SONAR_TOKEN_CREDENTIAL_ID}")]) {
                    sh '''
                        mvn clean install -DskipTests
                        docker run --rm \
                        -v "$PWD:/usr/src" \
                        ${SONAR_SCANNER_IMAGE} \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.java.binaries=target/classes \
                        -Dsonar.token=$SONAR_TOKEN_CREDENTIAL_ID
                    '''
                }
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
