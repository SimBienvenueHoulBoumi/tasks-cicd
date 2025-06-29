// 1. Credentials
//    - GITHUB-TOKEN        : Token ou clé SSH pour accéder à ton repo GitHub
//    - SONARTOKEN          : Token d'authentification SonarQube (injection via variable d'environnement ou credentials String)
//    - SNYK-TOKEN          : Token Snyk dans les Credentials (type : Secret Text)
//    - NEXUS_CREDENTIALS   : Username/Password pour pousser les images sur Nexus (type : Username/Password)
//
// 2. Tools (facultatif avec l'agent docker maven, mais nécessaire si tu ne les embarques pas dans ton image Docker)
//    - JDK : jdk (nom libre, mais correspond au label utilisé dans `tools {}` si utilisé)
//    - Maven : maven
//    - SonarQube Scanner : sonarScanner (si pas déjà embarqué dans ton image)
//
// 3. Configuration SonarQube (Manage Jenkins > Configure System)
//    - Ajouter une instance SonarQube nommée `sonarserver`
//
// 4. Plugin Jenkins nécessaires :
//    - Docker Pipeline
//    - Pipeline
//    - Git
//    - Pipeline: GitHub
//    - SonarQube Scanner for Jenkins
//    - Snyk Security Plugin
//    - HTML Publisher Plugin
//

pipeline {
    agent {
        docker {
            image 'maven:3.9.6-eclipse-temurin-17' // [Agent] Image Docker avec Maven + JDK 17
            args '-v /var/run/docker.sock:/var/run/docker.sock' // [Agent] Permet d’utiliser Docker dans l’agent
        }
    }

    options {
        timestamps() // [Options] Affiche les horodatages dans les logs
        skipDefaultCheckout(true) // [Options] On fait le checkout manuellement
        buildDiscarder(logRotator(numToKeepStr: '5')) // [Options] Garde uniquement les 5 derniers builds
        timeout(time: 30, unit: 'MINUTES') // [Options] Timeout global du pipeline
    }

    environment {
        // [Environnement] Variables projet et outils
        APP_NAME            = 'tasks-cicd'
        IMAGE_TAG           = "${APP_NAME}:${BUILD_NUMBER}"
        PROJET_NAME         = 'task-rest-api'
        NEXUS_URL           = 'nexus:8082'
        IMAGE_FULL          = "${NEXUS_URL}/${PROJET_NAME}:${BUILD_NUMBER}"
        PROJET_VERSION      = '0.0.1'

        REPORT_DIR          = 'reports'
        TRIVY_REPORT_DIR    = "${REPORT_DIR}/trivy"
        TRIVY_IMAGE         = 'aquasec/trivy:latest'
        TRIVY_SEVERITY      = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS     = "/root/reports/trivy-fs-report.json"
        TRIVY_OUTPUT_IMAGE  = "/root/reports/trivy-image-report.json"

        SNYK_JENKINS_NAME   = 'tasks'
        SNYK_TOKEN_ID       = 'SNYK_AUTH_TOKEN'
        SYNK_TARGET_FILE    = 'pom.xml'
        SYNK_SEVERITY       = 'high'

        SONARTOKEN          = 'SONARTOKEN'
        GITHUB_URL          = 'https://github.com/SimBienvenueHoulBoumi/tasks-cicd.git'
        GITHUB_CREDENTIALS_ID = 'GITHUB-CREDENTIALS'
    }

    stages {
        stage('📥 [Checkout] Récupération du code depuis GitHub') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: "${GITHUB_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }

        stage('🧰 [Maven Wrapper] Création si absent') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "Creating Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('🏗️ [Build] Compilation Maven & Archive des JARs') {
            steps {
                sh './mvnw clean package'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('🧪 [Unit Tests]') {
            steps {
                sh './mvnw clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('🧹 [Checkstyle] Analyse du style Java') {
            steps {
                sh './mvnw checkstyle:checkstyle'
                sh 'mkdir -p reports && mv target/checkstyle-result.xml reports/'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/checkstyle-result.xml'
                }
            }
        }

        stage('🔍 [SonarQube] Analyse de code + qualité') {
            steps {
                withSonarQubeEnv('sonarserver') {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=${PROJET_NAME} \
                            -Dsonar.projectName=${PROJET_NAME} \
                            -Dsonar.projectVersion=${PROJET_VERSION} \
                            -Dsonar.sources=src/ \
                            -Dsonar.token=${SONARTOKEN} \
                            -Dsonar.java.binaries=target/classes \
                            -Dsonar.junit.reportsPath=target/surefire-reports/ \
                            -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                            -Dsonar.java.checkstyle.reportPaths=reports/checkstyle-result.xml
                    '''
                }
            }
        }

        stage(' ✅ [Quality Gate] Vérifie que le projet passe les critères Sonar') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('🛡️ [Snyk]') {
            steps {
                sh 'mkdir -p reports/snyk'
                snykSecurity (
                    severity: "${SYNK_SEVERITY}",
                    snykInstallation: "${SNYK_JENKINS_NAME}",
                    snykTokenId: "${SNYK_TOKEN_ID}",
                    targetFile: "${SYNK_TARGET_FILE}",
                    monitorProjectOnBuild: true,
                    failOnIssues: true,
                    additionalArguments: '--report --format=html --report-file=reports/snyk/snyk_report.html'
                )
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/snyk/*.html'
                }
            }
        }

        stage('🐳 [Docker]  Build') {
            steps {
                script {
                    if (!fileExists('Dockerfile')) {
                        error "Dockerfile is missing"
                    }
                }
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🔬 [Trivy Source] Scan') {
            steps {
                sh """
                    mkdir -p \$TRIVY_REPORT_DIR
                    docker run --rm \\
                        -v \$(pwd):/project \\
                        -v \$(pwd)/\$TRIVY_REPORT_DIR:/root/reports \\
                        \$TRIVY_IMAGE fs /project \\
                        --exit-code 0 \\
                        --severity \$TRIVY_SEVERITY \\
                        --format json \\
                        --output \$TRIVY_OUTPUT_FS
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/*.json"
                }
            }
        }

        stage('🖼️ [Trivy Image] Scan') {
            steps {
                sh """
                    docker run --rm \$TRIVY_IMAGE clean --java-db
                    docker run --rm \\
                        -v /var/run/docker.sock:/var/run/docker.sock \\
                        -v \$(pwd)/\$TRIVY_REPORT_DIR:/root/reports \\
                        \$TRIVY_IMAGE image \$IMAGE_TAG \\
                        --timeout 10m \\
                        --exit-code 0 \\
                        --severity \$TRIVY_SEVERITY \\
                        --format json \\
                        --output \$TRIVY_OUTPUT_IMAGE
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/*.json"
                }
            }
        }

        stage('📦 [Push] Push Docker to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'NEXUS_CREDENTIALS',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh """
                        echo "\$PASS" | docker login \$NEXUS_URL -u "\$USER" --password-stdin
                        docker tag \$IMAGE_TAG \$IMAGE_FULL
                        docker push \$IMAGE_FULL
                        docker logout \$NEXUS_URL
                    """
                }
            }
        }

        stage('🧹 [Cleanup] Clean image') {
            steps {
                sh """
                    docker rmi \$IMAGE_TAG || true
                    docker system prune -f
                """
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
        // 🗂️ [HTML Reports] Publication des rapports lisibles dans Jenkins
        publishHTML([
            reportName : 'Snyk Report',
            reportDir  : 'reports/snyk',
            reportFiles: 'snyk_report.html',
            keepAll    : true,
            alwaysLinkToLastBuild: true,
            allowMissing: true // ✅ Ajoute ceci ici
        ])
        publishHTML([
            reportName : 'Trivy Scan',
            reportDir  : 'reports/trivy',
            reportFiles: 'trivy-fs-report.json',
            keepAll    : true,
            alwaysLinkToLastBuild: true,
            allowMissing: true
        ])
        cleanWs()
    }
  }
}
