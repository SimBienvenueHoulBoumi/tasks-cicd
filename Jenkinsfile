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
        // --- App & Docker ---
        APP_NAME        = "tasks-cicd"
        PROJECT_NAME    = "task-rest-api"
        // La version applicative est lue dynamiquement depuis le pom.xml (voir stage 📥 Checkout)
        PROJECT_VERSION = ""

        // SCM
        GIT_REPO_URL    = "git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git"
        GIT_BRANCH      = "main"
        GIT_CRED_ID     = "JENKINS_AGENT"

        NEXUS_REGISTRY    = "localhost:8083"
        AUTHORITY         = "simdev"
        IMAGE_REPO        = "${NEXUS_REGISTRY}/${AUTHORITY}/${PROJECT_NAME}"

        // Tags d'image (les valeurs SHA sont recalculées dans le stage Docker)
        IMAGE_TAG_BUILD   = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_TAG_SHA     = ""                               // défini avec le SHA dans le stage Docker
        IMAGE_TAG_VERSION = "${APP_NAME}:${PROJECT_VERSION}" // tag immuable basé sur la version applicative

        // Nexus
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        // SonarQube
        SONAR_SERVER      = "SonarQube"
        SONAR_URL         = "http://sonarqube:9000"
        SONAR_PROJECT_KEY = "task-rest-api"
        SONAR_PROJECT_NAME = "task-rest-api"
        // Surchargée au runtime avec la version Maven du projet
        SONAR_PROJECT_VERSION = ""
        SONAR_SOURCES = "src/"
        SONAR_JAVA_BINARIES = "target/classes"
        SONAR_JUNIT_REPORTS_PATH = "target/surefire-reports/"
        SONAR_COVERAGE_JACOCO_XML_REPORT_PATHS = "target/jacoco/jacoco.xml"
        SONAR_JAVA_CHECKSTYLE_REPORT_PATHS = "target/checkstyle-result.xml"
        SONAR_EXCLUSIONS = "**/target/**,**/test/**,**/*.json,**/*.yml"

        // Outils sécurité
        SNYK_CLI          = "snyk"
        // Identifiant ou slug de ton organisation Snyk (utilisé avec --org=)
        SNYK_ORG          = "967f8e17-af81-450e-98d1-e19b3e27f316"
        // Nom du projet container dans Snyk pour ce repo
        SNYK_PROJECT_NAME_CONTAINER = "task-rest-api-container"

        // --- Feature flags de durcissement (ON/OFF) ---
        FAIL_ON_SONAR_QGATE  = "false"   // si Quality Gate != OK -> échec build (via sonar.qualitygate.wait)
        FAIL_ON_SNYK_VULNS   = "false"   // si Snyk trouve des vulnérabilités -> échec (sinon warning)
        FAIL_ON_TRIVY_VULNS  = "false"   // idem pour Trivy
        RUN_SMOKE_TESTS      = "false"   // activer un stage de smoke tests HTTP (si déploiement derrière)
    }

    stages {

        stage('📥 Checkout') {
            steps {
                deleteDir()
                git branch: "${GIT_BRANCH}",
                    url: "${GIT_REPO_URL}",
                    credentialsId: "${GIT_CRED_ID}"

                script {
                    // Récupère la version Maven déclarée dans le pom.xml
                    def v = sh(
                        script: './mvnw help:evaluate -Dexpression=project.version -q -DforceStdout',
                        returnStdout: true
                    ).trim()

                    env.PROJECT_VERSION = v
                    env.SONAR_PROJECT_VERSION = v

                    echo "Version Maven détectée : ${env.PROJECT_VERSION}"
                }
            }
        }

        stage('🧪 Unit Tests & Build') {
            steps {
                // Tests unitaires + build + Jacoco, en sautant les tests d'intégration
                sh './mvnw clean verify -DskipITs=true -DskipUnitTests=false'
            }
            post {
                always {
                    junit testResults: 'target/surefire-reports/*.xml', allowEmptyResults: true
                }
                success {
                    archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
                }
            }
        }

        stage('🔗 Integration Tests (IT)') {
            steps {
                // Tests d'intégration uniquement (Failsafe), on saute les tests unitaires
                sh './mvnw verify -DskipITs=false -DskipUnitTests=true'
            }
        }

        stage('📊 SonarQube') {
            steps {
                echo '[Étape 1] Vérification DNS SonarQube'
                sh '''
                    echo "[INFO] Test DNS SonarQube avec curl"
                    curl -s -o /dev/null -w "%{http_code}\\n" "$SONAR_URL/api/system/status" || echo "ECHEC"
                '''

                echo '[Étape 2] Analyse SonarQube'
                withCredentials([string(credentialsId: 'SONARTOKEN', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        ./mvnw sonar:sonar \
                          -Dsonar.host.url="$SONAR_URL" \
                          -Dsonar.token="$SONAR_TOKEN" \
                          -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                          -Dsonar.projectName=$SONAR_PROJECT_NAME \
                          -Dsonar.projectVersion=$SONAR_PROJECT_VERSION \
                          -Dsonar.sources=$SONAR_SOURCES \
                          -Dsonar.java.binaries=$SONAR_JAVA_BINARIES \
                          -Dsonar.junit.reportsPath=$SONAR_JUNIT_REPORTS_PATH \
                          -Dsonar.coverage.jacoco.xmlReportPaths=$SONAR_COVERAGE_JACOCO_XML_REPORT_PATHS \
                          -Dsonar.java.checkstyle.reportPaths=$SONAR_JAVA_CHECKSTYLE_REPORT_PATHS \
                          -Dsonar.exclusions=$SONAR_EXCLUSIONS \
                          -Dsonar.qualitygate.wait=$FAIL_ON_SONAR_QGATE \
                          -DskipTests
                    '''
                }
            }
        }

        stage('🐳 Docker Build & Tag') {
            steps {
                script {
                    // Récupérer le SHA court du commit
                    def commit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()

                    env.IMAGE_TAG_BUILD   = "${APP_NAME}:${BUILD_NUMBER}"
                    env.IMAGE_TAG_SHA     = "${APP_NAME}:${commit}"
                    env.IMAGE_TAG_VERSION = "${APP_NAME}:${env.PROJECT_VERSION}"

                    env.IMAGE_NAME_BUILD   = "${IMAGE_REPO}:${BUILD_NUMBER}"
                    env.IMAGE_NAME_SHA     = "${IMAGE_REPO}:${commit}"
                    env.IMAGE_NAME_VERSION = "${IMAGE_REPO}:${env.PROJECT_VERSION}"

                    // Build sans BuildKit (buildx non installé sur l'agent)
                    sh """
                        docker build \\
                          -t ${IMAGE_NAME_BUILD} \\
                          -t ${IMAGE_NAME_SHA} \\
                          -t ${IMAGE_NAME_VERSION} \\
                          .
                    """
                }
            }
        }

        stage('🔐 Snyk Scan') {
            steps {
                withCredentials([string(credentialsId: 'SNYK_TOKEN', variable: 'SNYK_TOKEN')]) {
                    sh '''
                        set +e
                        mkdir -p reports/snyk

                        export SNYK_TOKEN="$SNYK_TOKEN"

                        IMAGE_TO_SCAN="${IMAGE_NAME_BUILD}"

                        echo "[SNYK] Lancement snyk container test sur ${IMAGE_TO_SCAN}..."
                        ${SNYK_CLI} container test "${IMAGE_TO_SCAN}" --severity-threshold=high --org="$SNYK_ORG" --json > reports/snyk/snyk-report.json
                        SNYK_EXIT=$?

                        echo "[SNYK] Lancement snyk container monitor..."
                        ${SNYK_CLI} container monitor "${IMAGE_TO_SCAN}" --org="$SNYK_ORG" --project-name="$SNYK_PROJECT_NAME_CONTAINER" || true

                        echo "[SNYK] Génération rapport HTML..."
                        python3 scripts/generate_snyk_report.py || true

                        if [ "$FAIL_ON_SNYK_VULNS" = "true" ] && [ "$SNYK_EXIT" -ne 0 ]; then
                          echo "[SNYK] Vulnérabilités détectées et FAIL_ON_SNYK_VULNS=true -> échec pipeline"
                          exit "$SNYK_EXIT"
                        else
                          echo "[SNYK] Exit code = $SNYK_EXIT (FAIL_ON_SNYK_VULNS=$FAIL_ON_SNYK_VULNS)"
                          exit 0
                        fi
                    '''
                }
            }
            post {
                always {
                    // Archive tout le répertoire Snyk (HTML + CSS + JSON)
                    archiveArtifacts artifacts: 'reports/snyk/**', allowEmptyArchive: true
                }
            }
        }

        stage('🔬 Trivy') {
            steps {
                sh '''
                    set +e
                    mkdir -p reports/trivy

                    echo "[TRIVY] Scan de l'image ${IMAGE_NAME_BUILD} (CRITICAL,HIGH)..."
                    trivy image --severity CRITICAL,HIGH --format json --exit-code 1 \
                      -o reports/trivy/trivy-report.json ${IMAGE_NAME_BUILD}
                    TRIVY_EXIT=$?

                    echo "[TRIVY] Génération rapport HTML..."
                    python3 scripts/generate_trivy_report.py || true

                    if [ "$FAIL_ON_TRIVY_VULNS" = "true" ] && [ "$TRIVY_EXIT" -ne 0 ]; then
                      echo "[TRIVY] Vulnérabilités détectées et FAIL_ON_TRIVY_VULNS=true -> échec pipeline"
                      exit "$TRIVY_EXIT"
                    else
                      echo "[TRIVY] Exit code = $TRIVY_EXIT (FAIL_ON_TRIVY_VULNS=$FAIL_ON_TRIVY_VULNS)"
                      exit 0
                    fi
                '''
            }
            post {
                always {
                    // Archive tout le répertoire Trivy (HTML + CSS + JSON)
                    archiveArtifacts artifacts: 'reports/trivy/**', allowEmptyArchive: true
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
                        echo "$PASS" | docker login ${NEXUS_REGISTRY} -u "$USER" --password-stdin

                        docker push ${IMAGE_NAME_BUILD}
                        docker push ${IMAGE_NAME_SHA}
                        docker push ${IMAGE_NAME_VERSION}

                        docker logout ${NEXUS_REGISTRY}
                    '''
                }
            }
        }

        stage('🧹 Cleanup') {
            steps {
                sh '''
                    echo "[CLEANUP] Suppression des images locales construites..."
                    docker rmi ${IMAGE_NAME_BUILD} || true
                    docker rmi ${IMAGE_NAME_SHA} || true
                    docker rmi ${IMAGE_NAME_VERSION} || true

                    # Pas de docker system prune ici: trop agressif sur un agent partagé.
                    # Si tu veux vraiment l'activer, fais-le manuellement ou ajoute un flag dédié.
                '''
            }
        }
    }

    post {
        failure {
            echo "[Pipeline] ❌ Build échoué — consulte les logs et rapports (JUnit, Sonar, Snyk, Trivy)."
        }
        always {
            // Archivage ciblé : jar et rapports
            archiveArtifacts artifacts: 'target/*.jar, reports/**', allowEmptyArchive: true
        }
    }
}
