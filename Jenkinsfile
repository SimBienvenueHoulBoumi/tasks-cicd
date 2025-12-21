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
        PROJECT_VERSION = "0.0.1"

        REGISTRY        = "localhost:8083"
        IMAGE_REPO      = "${REGISTRY}/simdev/${PROJECT_NAME}"

        // Tags de base (complétés par le SHA dans le stage Docker)
        IMAGE_TAG_BUILD = "${APP_NAME}:${BUILD_NUMBER}"

        // Nexus
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        // SonarQube
        SONAR_SERVER      = "SonarQube"
        SONAR_URL         = "http://sonarqube:9000"
        SONAR_PROJECT_KEY = "task-rest-api"
        SONAR_PROJECT_NAME = "task-rest-api"
        SONAR_PROJECT_VERSION = "0.0.1"
        SONAR_SOURCES = "src/"
        SONAR_JAVA_BINARIES = "target/classes"
        SONAR_JUNIT_REPORTS_PATH = "target/surefire-reports/"
        SONAR_COVERAGE_JACOCO_XML_REPORT_PATHS = "target/jacoco/jacoco.xml"
        SONAR_JAVA_CHECKSTYLE_REPORT_PATHS = "target/checkstyle-result.xml"
        SONAR_EXCLUSIONS = "**/target/**,**/test/**,**/*.json,**/*.yml"

        // Outils sécurité
        SNYK_CLI          = "snyk"

        // --- Feature flags de durcissement (ON/OFF) ---
        FAIL_ON_SONAR_QGATE  = "false"   // si Quality Gate != OK -> échec build (via sonar.qualitygate.wait)
        FAIL_ON_SNYK_VULNS   = "false"   // si Snyk trouve des vulnérabilités -> échec (sinon warning)
        FAIL_ON_TRIVY_VULNS  = "false"   // idem pour Trivy
        RUN_SMOKE_TESTS      = "false"  // activer un stage de smoke tests HTTP (si déploiement derrière)
    }

    stages {

        stage('📥 Checkout') {
            steps {
                deleteDir()
                git branch: 'main',
                    url: 'git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git',
                    credentialsId: 'JENKINS_AGENT'
            }
        }

        stage('🧪 Tests & Build') {
            steps {
                sh './mvnw clean verify -DskipITs'
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
                          -Dsonar.login="$SONAR_TOKEN" \
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

        stage('🏗️ Build (noop)') {
            steps {
                echo "Le jar a déjà été construit pendant '🧪 Tests & Build'."
                sh 'ls -1 target/*.jar || echo "Aucun jar trouvé !"'
            }
        }

        stage('🐳 Docker Build & Tag') {
            steps {
                script {
                    // Récupérer le SHA court du commit
                    def commit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()

                    env.IMAGE_TAG_BUILD  = "${APP_NAME}:${BUILD_NUMBER}"
                    env.IMAGE_TAG_SHA    = "${APP_NAME}:${commit}"
                    env.IMAGE_TAG_LATEST = "${APP_NAME}:latest"

                    env.IMAGE_NAME_BUILD  = "${IMAGE_REPO}:${BUILD_NUMBER}"
                    env.IMAGE_NAME_SHA    = "${IMAGE_REPO}:${commit}"
                    env.IMAGE_NAME_LATEST = "${IMAGE_REPO}:latest"

                    // Build sans BuildKit (buildx non installé sur l'agent)
                    sh """
                        docker build \\
                          -t ${IMAGE_NAME_BUILD} \\
                          -t ${IMAGE_NAME_SHA} \\
                          .
                    """

                    // Tag latest uniquement sur main
                    if ((env.BRANCH_NAME ?: 'main') == 'main') {
                        sh "docker tag ${IMAGE_NAME_BUILD} ${IMAGE_NAME_LATEST}"
                    }
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

                        echo "[SNYK] Lancement snyk test..."
                        ${SNYK_CLI} test --severity-threshold=high --file=pom.xml --json > reports/snyk/snyk-report.json
                        SNYK_EXIT=$?

                        echo "[SNYK] Lancement snyk monitor..."
                        ${SNYK_CLI} monitor --file=pom.xml --project-name=task-rest-api || true

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
                    archiveArtifacts artifacts: 'reports/snyk/snyk-report.*', allowEmptyArchive: true
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

                    python3 scripts/generate_trivy_report.py reports/trivy/trivy-report.json reports/trivy/trivy-report.html || true

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
                        echo "$PASS" | docker login ${REGISTRY} -u "$USER" --password-stdin

                        docker push ${IMAGE_NAME_BUILD}
                        docker push ${IMAGE_NAME_SHA}

                        if [ "${BRANCH_NAME:-main}" = "main" ]; then
                          docker push ${IMAGE_NAME_LATEST}
                        fi

                        docker logout ${REGISTRY}
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
                    if [ "${BRANCH_NAME:-main}" = "main" ]; then
                      docker rmi ${IMAGE_NAME_LATEST} || true
                    fi

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
