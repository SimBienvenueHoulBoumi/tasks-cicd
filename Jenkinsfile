pipeline {
    agent { label 'jenkins-agent' } // Le label de ton agent SSH

    tools {
        jdk 'jdk'         // Le nom défini dans Jenkins > Global Tool Configuration
        maven 'maven'     // Le nom défini dans Jenkins > Global Tool Configuration
    }


    environment {
        APP_NAME            = 'tasks-cicd'
        IMAGE_TAG           = "${APP_NAME}:${BUILD_NUMBER}"
        PROJET_NAME         = 'task-rest-api'
        PROJET_VERSION      = '0.0.1'

        GITHUB_URL          = "git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git"
        GITHUB_CREDENTIALS = 'GITHUB-CREDENTIALS'

        NEXUS_URL           = 'nexus:8082'
        IMAGE_FULL          = "${NEXUS_URL}/${PROJET_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS   = "NEXUS_CREDENTIALS"

        REPORT_DIR          = 'reports'
        TRIVY_REPORT_DIR    = "${REPORT_DIR}/trivy"
        TRIVY_IMAGE         = 'aquasec/trivy:latest'
        TRIVY_SEVERITY      = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS     = "/root/reports/trivy-fs-report.json"
        TRIVY_OUTPUT_IMAGE  = "/root/reports/trivy-image-report.json"

        SNYK_JENKINS_NAME   = 'snyk'
        SNYK_TOKEN_ID       = 'SNYK_AUTH_TOKEN'
        SYNK_TARGET_FILE    = 'pom.xml'
        SYNK_SEVERITY       = 'high'

        SONAR_URL           = 'http://sonarqube:9000'
    }

    stages {
        stage('📥 Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: "${GITHUB_URL}",
                        credentialsId: "${GITHUB_CREDENTIALS}"
                    ]]
                ])
            }
        }

        stage('🧰 Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "Creating Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                '''
            }
        }

        stage('🏗️ Build & Archive') {
            steps {
                sh './mvnw clean package'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('🧪 Unit Tests') {
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
                sh 'mkdir -p reports && mv target/checkstyle-result.xml reports/'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/checkstyle-result.xml'
                }
            }
        }

        stage('🔍 SonarQube Scan') {
            steps {
                withCredentials([string(credentialsId: 'SONARTOKEN', variable: 'SONARTOKEN')]) {
                    withSonarQubeEnv('sonarserver') {
                        sh '''
                            sonar-scanner \
                                -Dsonar.projectKey=${PROJET_NAME} \
                                -Dsonar.projectName=${PROJET_NAME} \
                                -Dsonar.projectVersion=${PROJET_VERSION} \
                                -Dsonar.host.url=${SONAR_URL} \
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
        }

        stage('✅ Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('🛡️ Snyk') {
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

        stage('🐳 Docker Build') {
            steps {
                script {
                    if (!fileExists('Dockerfile')) {
                        error "Dockerfile is missing"
                    }
                }
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('🔬 Trivy Source') {
            steps {
                sh """
                    mkdir -p \$TRIVY_REPORT_DIR
                    trivy fs . \
                        --exit-code 0 \
                        --severity \$TRIVY_SEVERITY \
                        --format json \
                        --output \$TRIVY_OUTPUT_FS
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/*.json"
                }
            }
        }

        stage('🖼️ Trivy Image') {
            steps {
                sh """
                    trivy image \$IMAGE_TAG \
                        --timeout 10m \
                        --exit-code 0 \
                        --severity \$TRIVY_SEVERITY \
                        --format json \
                        --output \$TRIVY_OUTPUT_IMAGE
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TRIVY_REPORT_DIR}/*.json"
                }
            }
        }

        stage('📦 Push Docker to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${NEXUS_CREDENTIALS}",
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

        stage('🧹 Cleanup') {
            steps {
                sh """
                    docker rmi \$IMAGE_TAG || true
                    docker system prune -f
                """
            }
        }
    }

    post {
        always {
            cleanWs()
            publishHTML([
                reportName : 'Snyk Report',
                reportDir  : 'reports/snyk',
                reportFiles: 'snyk_report.html',
                keepAll    : true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])
            publishHTML([
                reportName : 'Trivy Scan',
                reportDir  : 'reports/trivy',
                reportFiles: 'trivy-fs-report.json',
                keepAll    : true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])
        }
    }
}
