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
    }

    environment {
        APP_NAME         = "tasks-cicd"
        IMAGE_TAG        = "${APP_NAME}:${BUILD_NUMBER}"
        PROJECT_NAME     = "task-rest-api"
        PROJECT_VERSION  = "0.0.1"

        GITHUB_URL         = "git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git"
        GITHUB_CREDENTIALS = "GITHUB-CREDENTIALS"

        NEXUS_URL         = "http://nexus:8082"
        IMAGE_FULL        = "${NEXUS_URL}/${PROJECT_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS = "NEXUS_CREDENTIALS"

        SONAR_SERVER   = "SonarQube"
        SNYK           = "snyk"
        TRIVY_URL      = "http://localhost:4954/scan"
    }

    stages {

        stage('📥 Checkout') {
            steps {
                checkout scm
            }
        }

        stage('🏗️ Build') {
            steps {
                sh './mvnw clean package -DskipTests'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('🧪 Tests') {
            steps {
                sh './mvnw test'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
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

        stage('🛡️ Snyk') {
            steps {
                snykSecurity (
                    severity: 'high',
                    snykInstallation: "${SNYK}",
                    snykTokenId: 'SNYK_AUTH_TOKEN',
                    targetFile: 'pom.xml',
                    monitorProjectOnBuild: true,
                    failOnIssues: false,
                    additionalArguments: '--report --format=html --report-file=reports/snyk/snyk_report.html'
                )
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/snyk',
                        reportFiles: 'snyk_report.html',
                        reportName: 'Snyk Vulnerability Report'
                    ])
                }
            }
        }

        stage('🐳 Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_TAG} ."
            }
        }

        stage('🔬 Trivy') {
            steps {
                sh '''
                    mkdir -p reports/trivy
                    curl -s -X POST ${TRIVY_URL} \
                      -H 'Content-Type: application/json' \
                      -d '{
                        "image_name": "${IMAGE_TAG}",
                        "scan_type": "image",
                        "vuln_type": ["os", "library"],
                        "severity": ["CRITICAL", "HIGH"]
                      }' > reports/trivy/trivy-report.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/trivy/trivy-report.json'
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
                        docker tag "$IMAGE_TAG" "$IMAGE_FULL"
                        docker push "$IMAGE_FULL"
                        docker logout "$NEXUS_URL"
                    '''
                }
            }
        }

        stage('🧹 Cleanup') {
            steps {
                sh '''
                    docker rmi "${IMAGE_TAG}" || true
                    docker system prune -f
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
            publishHTML([
                reportName : 'Trivy Report',
                reportDir  : 'reports/trivy',
                reportFiles: 'trivy-report.json',
                keepAll    : true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])
        }
    }
}
