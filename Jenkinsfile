pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }

    options {
        skipDefaultCheckout true
        timestamps()
    }

    environment {
        // Nom de l'application
        APP_NAME             = 'tasks-cicd'

        // Références Git
        GIT_REPO_URL         = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GIT_BRANCH           = '*/main'

        // Clé projet SonarQube
        SONAR_PROJECT_KEY    = 'tasks-cicd'
        SONAR_HOST_URL       = 'http://localhost:9000'

        // Nom de l'image Docker locale (tag temporaire)
        IMAGE_TAG            = "${APP_NAME}:${BUILD_NUMBER}"

        // Dossiers de rapports
        TRIVY_REPORT_DIR     = 'trivy-reports'

        // Credentials IDs
        GITHUB_CREDENTIALS_ID   = 'GITHUB-CREDENTIALS'

        NEXUS_URL = 'http://localhost:8081'
        NEXUS_REPO = 'docker-hosted'
        NEXUS_CREDENTIALS_ID    = 'NEXUS-CREDENTIAL'

        SONARSERVER = 'SONARSERVER'         // 🔍 Nom du serveur SonarQube configuré dans Jenkins
        SONARSCANNER = 'SONARSCANNER'       // 🔍 Scanner CLI SonarQube configuré dans Jenkins

        SNYK = 'snyk'                       // 🛡️ Nom de l'installation Snyk (scanner de vulnérabilités)
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
                        echo "➡ Maven Wrapper manquant. Génération..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        stage('🔧 Compilation Maven') {
            steps {
                sh './mvnw clean compile'
            }
            post {
                success {
                    echo "✅ Build réussi - Archivage des artefacts..."
                    archiveArtifacts artifacts: 'target/*.jar' // 📦 Sauvegarde du fichier .jar généré
                }
            }
        }

        stage('📊 Analyse SonarQube') {
            steps {
                withCredentials([string(credentialsId: 'SONAR-TOKEN', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        docker run --rm \
                            -v "$PWD":/usr/src \
                            sonarsource/sonar-scanner-cli \
                            -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                            -Dsonar.sources=src \
                            -Dsonar.java.binaries=target/classes \
                            -Dsonar.token=$SONAR_TOKEN \
                            -Dsonar.host.url=$SONAR_HOST_URL
                    '''
                }
            }
        }

        stage('🔨 Build & Tests') {
            steps {
                sh './mvnw clean verify'
            }
            post {
                always {
                    echo "✅ Build réussi - Archivage des artefacts..."
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('🧹 Checkstyle Analysis') {
            steps {
                sh './mvnw checkstyle:checkstyle'
            }
        }

        stage('📊 SonarQube Analysis') {
            environment {
                scannerHome = tool "${SONARSCANNER}" // 🛠️ Récupère le chemin d’installation du scanner
            }
            withCredentials([string(credentialsId: 'SONAR-TOKEN', variable: 'SONAR_TOKEN')]) {
                sh '''
                    docker run --rm \
                        -v "$PWD":/usr/src \
                        sonarsource/sonar-scanner-cli \
                        -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                        -Dsonar.sources=src \
                        -Dsonar.java.binaries=target/classes \
                        -Dsonar.token=$SONAR_TOKEN \
                        -Dsonar.host.url=$SONAR_HOST_URL
                '''
           }
        }

        stage('Snyk Dependency Scan') {
            steps {
                snykSecurity (
                    severity: 'high',                         // 🚨 Niveau de menace minimum : high, medium, low
                    snykInstallation: "${SNYK}",              // 🔧 Nom défini dans Jenkins pour Snyk CLI
                    snykTokenId: 'snyk-token',                // 🔑 ID de la clé d'API Snyk (stockée dans Jenkins Credentials)
                    targetFile: 'pom.xml',                    // 📄 Fichier principal pour Maven
                    monitorProjectOnBuild: true,              // 📡 Envoi automatique des résultats sur Snyk.io
                    failOnIssues: true,                       // ❌ Échoue le pipeline en cas de vulnérabilités
                    additionalArguments: '--report --format=html --report-file=snyk_report.html' // 📃 Génère un rapport HTML
                ) 
            } 
        }

        stage('🐳 Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🛡️ Trivy – Analyse image Docker') {
            steps {
                sh """
                    mkdir -p ${TRIVY_REPORT_DIR}
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $PWD/${TRIVY_REPORT_DIR}:/root/reports \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity CRITICAL,HIGH \
                        --format json \
                        --output /root/reports/trivy-image-report.json \
                        ${IMAGE_TAG}
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/trivy-image-report.json", allowEmptyArchive: true
                }
            }
        }

       stage('📦 Push Docker vers Nexus') {
            steps {
                echo 'Nexus Docker Repository Login'
                script{
                    def NEXUS_REPO_URL = "${NEXUS_URL}/repository/${NEXUS_REPO}"
                    def NEXUS_IMAGE = "http:localhost:8085/${APP_NAME}:${BUILD_NUMBER}"

                    echo "🔐 Login au Nexus Docker Registry : ${NEXUS_IMAGE}"

                    withCredentials([usernamePassword(
                        credentialsId: "${NEXUS_CREDENTIALS_ID}",
                        usernameVariable: 'USER',
                        passwordVariable: 'PASS'
                    )]) 
                   
                }
            }
            steps {
                echo 'Pushing Im to docker hub'
                sh 'docker push $NEXUS_DOCKER_REPO/demo-rest-api:$BUILD_NUMBER'
            }
        }
    }


    stage('🧹 Nettoyage') {
        steps {
            sh '''
                docker rmi ${IMAGE_TAG} || true
                docker system prune -f
            '''
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