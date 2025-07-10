pipeline {
    agent { label 'jenkins-agent' }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    tools {
        jdk 'jdk'
        maven 'maven'
        git 'git'
    }

    environment {
        APP_NAME         = "tasks-cicd"
        IMAGE_TAG        = "${APP_NAME}:${BUILD_NUMBER}"
        PROJECT_NAME     = "task-rest-api"
        PROJECT_VERSION  = "0.0.1"

        NEXUS_URL         = "http://nexus:8082"
        IMAGE_FULL        = "${NEXUS_URL}/${PROJECT_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        SONAR_SERVER   = "SonarQube"
        SONAR_URL      = "http://sonarqube:9000"

        SNYK           = "snyk"
        TRIVY_URL      = "http://trivy:4954/scan"

        NVD_API_KEY = credentials('NVD_API_KEY')
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
                    junit 'target/surefire-reports/*.xml'
                    publishHTML([
                        reportName : 'JaCoCo Code Coverage',
                        reportDir  : 'target/jacoco',
                        reportFiles: 'index.html',
                        keepAll    : true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true
                    ])
                }
            }
        }

        stage('Debug SonarQube') {
            steps {
                sh '''
                    echo "[INFO] Test DNS SonarQube avec curl"
                    curl -v http://sonarqube:9000/api/system/status || echo "ECHEC"
                '''
            }
        }

        stage('📊 SonarQube') {
            steps {
                withCredentials([string(credentialsId: 'SONARTOKEN', variable: 'SONAR_TOKEN')]) {
                withSonarQubeEnv("${SONAR_SERVER}") {
                    sh '''
                    ./mvnw clean verify sonar:sonar \
                        -Dsonar.projectKey=task-rest-api \
                        -Dsonar.projectName=task-rest-api \
                        -Dsonar.projectVersion=0.0.1 \
                        -Dsonar.sources=src/ \
                        -Dsonar.java.binaries=target/classes \
                        -Dsonar.junit.reportsPath=target/surefire-reports/ \
                        -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                        -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml \
                        -Dsonar.exclusions=**/target/**,**/test/**,**/*.json,**/*.yml \
                        -Dsonar.host.url=$SONAR_URL \
                        -Dsonar.token=$SONAR_TOKEN
                    '''
                }
                }
            }
        }

        stage('✅ Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('🔐 Snyk Scan') {
            steps {
                withCredentials([string(credentialsId: 'SNYK_TOKEN', variable: 'SNYK_TOKEN')]) {
                    sh '''
                        snyk auth $SNYK_TOKEN
                        snyk test --severity-threshold=high --file=pom.xml --json > snyk_report.json || true
                        mkdir -p reports/snyk
                        snyk-to-html -i snyk_report.json -o reports/snyk/snyk-report.html
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/snyk/snyk-report.*', allowEmptyArchive: true
                    publishHTML([
                        reportName: 'Snyk Report',
                        reportDir: 'reports/snyk',
                        reportFiles: 'snyk-report.html',
                        keepAll: true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true
                    ])

                }
            }
        }

       stage('🛡️ OWASP Dependency Check') {
            steps {
                script {
                    echo '[INFO] Lancement de l’analyse de vulnérabilités...'
                }

                sh '''
                    mkdir -p reports/owasp

                    docker run --rm \
                        -v $(pwd):/src \
                        -v $HOME/.dependency-check:/usr/share/dependency-check/data \
                        owasp/dependency-check \
                        --project "tasks" \
                        --scan /src \
                        --format "HTML" \
                        --out /src/reports/owasp
                '''
            }

            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/owasp',
                        reportFiles: 'dependency-check-report.html',
                        reportName: 'OWASP Dependency-Check'
                    ])
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
                    docker tag ${IMAGE_TAG} ${NEXUS_URL}/${PROJECT_NAME}:latest
                """
            }
        }

        stage('🔬 Trivy') {
            steps {
                sh '''
                    mkdir -p reports/trivy
                    curl -s -X POST http://trivy:4954/scan \
                        -H 'Content-Type: application/json' \
                        -d "{
                            \\"image_name\\": \\"${IMAGE_TAG}\\",
                            \\"scan_type\\": \\"image\\",
                            \\"vuln_type\\": [\\"os\\", \\"library\\"],
                            \\"severity\\": [\\"CRITICAL\\", \\"HIGH\\"]
                        }" > reports/trivy/trivy-report.json

                    python3 scripts/generate_trivy_report.py reports/trivy/trivy-report.json reports/trivy/trivy-report.html
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/trivy/*.*'
                    publishHTML([
                        reportName : 'Trivy HTML Report',
                        reportDir  : 'reports/trivy',
                        reportFiles: 'trivy-report.html',
                        keepAll    : true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true
                    ])
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
                        echo "$PASS" | docker login "$NEXUS_URL" -u "$USER" --password-stdin
                        docker push "$IMAGE_TAG"
                        docker push "${NEXUS_URL}/${PROJECT_NAME}:latest"
                        docker logout "$NEXUS_URL"
                    '''
                }
            }
        }

        stage('🧹 Cleanup') {
            steps {
                sh '''
                    docker rmi "${IMAGE_TAG}" || true
                    docker rmi "${NEXUS_URL}/${PROJECT_NAME}:latest" || true
                    docker system prune -f
                '''
            }
        }

    }

}
