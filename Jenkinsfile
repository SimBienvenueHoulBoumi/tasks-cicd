pipeline {
    agent { label 'jenkins-agent' }

    tools {
        jdk 'jdk'
        maven 'maven'
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        APP_NAME           = 'tasks-cicd'
        IMAGE_TAG          = "${APP_NAME}:${BUILD_NUMBER}"
        PROJET_NAME        = 'task-rest-api'
        NEXUS_URL          = 'localhost:8082'
        IMAGE_FULL         = "${NEXUS_URL}/${PROJET_NAME}:${BUILD_NUMBER}"
        PROJET_VERSION     = '0.0.1'
        PROJET_SERVICE_PATH= 'simdev/demo/services'

        TRIVY_IMAGE        = 'aquasec/trivy:latest'
        TRIVY_REPORT_DIR   = 'trivy-reports'
        TRIVY_SEVERITY     = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS    = '/root/reports/trivy-fs-report.json'
        TRIVY_OUTPUT_IMAGE = '/root/reports/trivy-image-report.json'

        SNYK_JENKINS_NAME  = 'tasks' 
        SNYK_TOKEN_ID      = 'SNYK-TOKEN'
        SYNK_TARGET_FILE   = 'pom.xml'
        SYNK_SEVERITY      = 'high'

        SONARSCANNER       = 'sonarScanner'
        SONARTOKEN         = 'SONARTOKEN'

        GITHUB_URL         = 'git@github.com:simbienvenuehoulboumi/tasks-cicd.git'
        GITHUB_CREDENTIALS_ID = 'GITHUB-TOKEN'
    }

    stages {

        stage('Setup SSH Wrapper') {
            steps {
                sh '''
                    mkdir -p .ssh
                    cp ~/.ssh/id_ed25519 .ssh/id_ed25519
                    cp ~/.ssh/known_hosts .ssh/known_hosts
                    chmod 600 .ssh/id_ed25519
                    echo '#!/bin/sh' > ssh-wrapper.sh
                    echo 'exec ssh -o StrictHostKeyChecking=yes -i .ssh/id_ed25519 "$@"' >> ssh-wrapper.sh
                    chmod +x ssh-wrapper.sh
                '''
            }
        }
        
        stage('Checkout') {
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

        stage('Ensure Maven Wrapper') {
            steps {
                sh """
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "Creating Maven Wrapper..."
                        mvn -N io.takari:maven:wrapper
                    fi
                """
            }
        }

        stage('Build') {
            steps {
                sh './mvnw clean package'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('Unit Tests') {
            steps {
                sh './mvnw clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('Checkstyle') {
            steps {
                sh './mvnw checkstyle:checkstyle'
            }
        }

        stage('SonarQube') {
            environment {
                scannerHome = tool "${SONARSCANNER}"
            }
            steps {
                withSonarQubeEnv('sonarserver') {
                    sh """$scannerHome/bin/sonar-scanner \
                        -Dsonar.projectKey=$PROJET_NAME \
                        -Dsonar.projectName=$PROJET_NAME \
                        -Dsonar.projectVersion=$PROJET_VERSION \
                        -Dsonar.sources=src/ \
                        -Dsonar.token=$SONARTOKEN \
                        -Dsonar.java.binaries=target/test-classes/$PROJET_SERVICE_PATH \
                        -Dsonar.junit.reportsPath=target/surefire-reports/ \
                        -Dsonar.coverage.jacoco.xmlReportPaths=target/jacoco/jacoco.xml \
                        -Dsonar.java.checkstyle.reportPaths=target/checkstyle-result.xml"""
                }
            }
        }

        stage('Snyk') {
            steps {
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
                    if (!fileExists('Dockerfile')) {
                        error "Dockerfile is missing"
                    }
                }
                sh 'docker build -t $IMAGE_TAG .'
            }
        }

        stage('Trivy Source Scan') {
            steps {
                sh """
                    mkdir -p $TRIVY_REPORT_DIR
                    docker run --rm \
                        -v $(pwd):/project \
                        -v $(pwd)/$TRIVY_REPORT_DIR:/root/reports \
                        ${TRIVY_IMAGE} fs /project \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output $TRIVY_OUTPUT_FS
                """
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh """
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
                """
            }
        }

        stage('Push Docker to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'NEXUS_CREDENTIALS',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh """
                        echo "$PASS" | docker login $NEXUS_URL -u "$USER" --password-stdin
                        docker tag $IMAGE_TAG $IMAGE_FULL
                        docker push $IMAGE_FULL
                        docker logout $NEXUS_URL
                    """
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh """
                    docker rmi $IMAGE_TAG || true
                    docker system prune -f
                """
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
            cleanWs()
        }
    }
}
