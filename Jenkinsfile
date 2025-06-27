pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk' // Utilise le JDK défini dans Jenkins (configuration globale)
        maven 'maven' // Utilise Maven depuis les outils Jenkins
    }

    options {
        timestamps() // Ajoute les horodatages aux logs de build
        skipDefaultCheckout(true) // Évite le checkout automatique (géré manuellement plus bas)
        buildDiscarder(logRotator(numToKeepStr: '5')) // Garde les 5 derniers builds uniquement
        timeout(time: 30, unit: 'MINUTES') // Timeout global du pipeline à 30 minutes
    }

    environment {
        // Variables de configuration du projet
        APP_NAME           = 'tasks-cicd'
        IMAGE_TAG          = "${APP_NAME}:${BUILD_NUMBER}"
        PROJET_NAME        = 'task-rest-api'
        NEXUS_URL          = 'localhost:8082'
        IMAGE_FULL         = "${NEXUS_URL}/${PROJET_NAME}:${BUILD_NUMBER}"
        PROJET_VERSION     = '0.0.1'
        PROJET_SERVICE_PATH= 'simdev/demo/services'

        // Configuration Trivy pour scan de vulnérabilité
        TRIVY_IMAGE        = 'aquasec/trivy:latest'
        TRIVY_REPORT_DIR   = 'trivy-reports'
        TRIVY_SEVERITY     = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS    = '/root/reports/trivy-fs-report.json'
        TRIVY_OUTPUT_IMAGE = '/root/reports/trivy-image-report.json'

        // Configuration Snyk pour analyse de sécurité
        SNYK_JENKINS_NAME  = 'tasks'
        SNYK_TOKEN_ID      = 'SNYK-TOKEN'
        SYNK_TARGET_FILE   = 'pom.xml'
        SYNK_SEVERITY      = 'high'

        // Configuration SonarQube pour analyse de code
        SONARSCANNER       = 'sonarScanner'
        SONARTOKEN         = 'SONARTOKEN'

        // Configuration GitHub
        GITHUB_URL         = 'git@github.com:simbienvenuehoulboumi/tasks-cicd.git'
        GITHUB_CREDENTIALS_ID = 'GITHUB-SSH-KEY'
    }

    stages {

        stage('Checkout') {
            steps {
                // Récupération du code source depuis GitHub avec les credentials
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: "${GITHUB_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }

        stage('Ensure Maven Wrapper') {
            steps {
                // Création du wrapper Maven si absent
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "Creating Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('Build') {
            steps {
                // Compilation du projet
                sh './mvnw clean package'
            }
            post {
                success {
                    // Archive les fichiers jar produits
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('Unit Tests') {
            steps {
                // Exécution des tests unitaires
                sh './mvnw clean verify'
            }
            post {
                always {
                    // Génère les rapports de test dans Jenkins
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('Checkstyle') {
            steps {
                // Vérifie le style de code Java
                sh './mvnw checkstyle:checkstyle'
            }
        }

        stage('SonarQube') {
            environment {
                scannerHome = tool "${SONARSCANNER}"
            }
            steps {
                // Analyse statique avec SonarQube
                withSonarQubeEnv('sonarserver') {
                    sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJET_NAME} \
                        -Dsonar.projectName=${PROJET_NAME} \
                        -Dsonar.projectVersion=${PROJET_VERSION} \
                        -Dsonar.sources=src/ \
                        -Dsonar.token=${SONARTOKEN} \
                        -Dsonar.java.binaries=target/test-classes/${PROJET_SERVICE_PATH} \
                        -Dsonar.junit.reportsPath=target/surefire-reports/ \
                        -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                        -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml
                    """
                }
            }
        }

        stage('Snyk') {
            steps {
                // Analyse de vulnérabilités avec Snyk
                snykSecurity (
                    severity: "${SYNK_SEVERITY}",
                    snykInstallation: "${SNYK_JENKINS_NAME}",
                    snykTokenId: "${SNYK_TOKEN_ID}",
                    targetFile: "${SYNK_TARGET_FILE}",
                    monitorProjectOnBuild: true,
                    failOnIssues: true,
                    additionalArguments: '--report --format=html --report-file=snyk_report.html'
                )
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    // Vérifie la présence d'un Dockerfile
                    if (!fileExists('Dockerfile')) {
                        error "Dockerfile is missing"
                    }
                }
                // Construction de l'image Docker
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('Trivy Source Scan') {
            steps {
                // Scan de vulnérabilité du projet (fichiers sources)
                sh '''
                    mkdir -p $TRIVY_REPORT_DIR
                    docker run --rm \
                        -v $(pwd):/project \
                        -v $(pwd)/$TRIVY_REPORT_DIR:/root/reports \
                        ${TRIVY_IMAGE} fs /project \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output $TRIVY_OUTPUT_FS
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                // Scan de vulnérabilité de l'image Docker construite
                sh '''
                    docker run --rm $TRIVY_IMAGE clean --java-db
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $(pwd)/$TRIVY_REPORT_DIR:/root/reports \
                        $TRIVY_IMAGE image $IMAGE_TAG \
                        --timeout 10m \
                        --exit-code 0 \
                        --severity $TRIVY_SEVERITY \
                        --format json \
                        --output $TRIVY_OUTPUT_IMAGE
                '''
            }
        }

        stage('Push Docker to Nexus') {
            steps {
                // Authentification Nexus + push de l'image
                withCredentials([usernamePassword(
                    credentialsId: 'NEXUS_CREDENTIALS',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo "$PASS" | docker login $NEXUS_URL -u "$USER" --password-stdin
                        docker tag $IMAGE_TAG $IMAGE_FULL
                        docker push $IMAGE_FULL
                        docker logout $NEXUS_URL
                    '''
                }
            }
        }

        stage('Cleanup') {
            steps {
                // Nettoyage des images et cache
                sh '''
                    docker rmi $IMAGE_TAG || true
                    docker system prune -f
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully.'
        }
        failure {
            echo '❌ Pipeline failed.'
        }
        always {
            cleanWs() // Nettoyage de l'espace de travail Jenkins
        }
    }
}