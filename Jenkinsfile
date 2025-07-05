pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
        git 'git'
    }

    environment {
        APP_NAME            = "tasks-cicd"
        IMAGE_TAG           = "${APP_NAME}:${BUILD_NUMBER}"
        PROJET_NAME         = "task-rest-api"
        PROJET_VERSION      = "0.0.1"

        GITHUB_URL          = "git@github.com:SimBienvenueHoulBoumi/tasks-cicd.git"
        GITHUB_CREDENTIALS  = "GITHUB-CREDENTIALS"

        NEXUS_URL           = "http://nexus:8082"
        IMAGE_FULL          = "${NEXUS_URL}/${PROJET_NAME}:${BUILD_NUMBER}"
        NEXUS_CREDENTIALS   = "NEXUS_CREDENTIALS"

        REPORT_DIR          = "reports"
        TRIVY_REPORT_DIR    = "${REPORT_DIR}/trivy"
        TRIVY_IMAGE         = "aquasec/trivy:latest"
        TRIVY_SEVERITY      = "CRITICAL,HIGH"
        TRIVY_OUTPUT_FS     = "${TRIVY_REPORT_DIR}/trivy-fs-report.json"
        TRIVY_OUTPUT_IMAGE  = "${TRIVY_REPORT_DIR}/trivy-image-report.json"

        SNYK_TARGET_FILE    = "pom.xml"
        SNYK_SEVERITY       = "high"
        DOCKER_BUILDKIT     = '1'
        SONAR_URL           = "http://sonarqube:9000"
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
                withCredentials([string(credentialsId: 'SONARTOKEN', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('sonarserver') {
                        sh """
                            ./mvnw clean install

                            sonar-scanner \
                                -Dsonar.projectKey=$PROJET_NAME \
                                -Dsonar.projectName=$PROJET_NAME \
                                -Dsonar.projectVersion=$PROJET_VERSION \
                                -Dsonar.token=$SONAR_TOKEN \
                                -Dsonar.sources=src/ \
                                -Dsonar.java.binaries=target/classes \
                                -Dsonar.junit.reportsPath=target/surefire-reports/ \
                                -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                                -Dsonar.java.checkstyle.reportPaths=reports/checkstyle-result.xml
                        """
                    }
                }
            }
        }
        
        stage('✅ Quality Gate') {
            steps {
                timeout(time: 20, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('🛡️ Analyse Snyk') {
            steps {
                withCredentials([string(credentialsId: 'SNYK_AUTH_TOKEN', variable: 'SNYK_TOKEN')]) {
                    sh '''
                        export JAVA_HOME=/opt/java/openjdk
                        export PATH=$JAVA_HOME/bin:$PATH

                        export SNYK_TOKEN=$SNYK_TOKEN

                        mkdir -p reports/snyk

                        snyk test --file=pom.xml \
                            --severity-threshold=high \
                            --report \
                            --format=html \
                            --report-file=reports/snyk/snyk_report.html
                    '''
                }
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

        stage('🐳 Build avec Buildx') {
            steps {
                sh '''
                    docker buildx create --use --name myApp || true
                    docker buildx inspect myApp --bootstrap
                    docker buildx build --load -t $IMAGE_TAG .
                '''
            }
        }

        stage('🔬 Trivy Source') {
            steps {
                sh 'trivy fs . --severity HIGH --exit-code 0 || true'
                sh '''
                    mkdir -p reports/trivy
                    trivy fs . --format html --output reports/trivy/trivy_report.html || true
                '''  
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
                    sh '''#!/bin/bash
                        set -euo pipefail

                        echo "[INFO] 🔐 Connexion à Nexus Docker Registry..."
                        echo "$PASS" | docker login "$NEXUS_URL" -u "$USER" --password-stdin

                        echo "[INFO] 🏷️  Tag de l'image : $IMAGE_TAG → $IMAGE_FULL"
                        docker tag "$IMAGE_TAG" "$IMAGE_FULL"

                        echo "[INFO] 📤 Push vers Nexus : $IMAGE_FULL"
                        docker push "$IMAGE_FULL"

                        echo "[INFO] 🔓 Déconnexion du registre Nexus"
                        docker logout "$NEXUS_URL"
                    '''
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
