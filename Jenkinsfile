pipeline {
    agent { label 'jenkins-agent' }

    // Étape 1 : Configuration des outils
    tools {
        jdk 'jdk'         // Doit être défini dans Jenkins (Manage Jenkins > Global Tool Configuration)
        maven 'maven'     // Doit être défini dans Jenkins
    }

    // Étape 2 : Options générales du pipeline
    options {
        timestamps()                      // Ajoute l'heure dans les logs
        skipDefaultCheckout(true)         // On gère manuellement le checkout
        buildDiscarder(logRotator(numToKeepStr: '5')) // Garde les 5 derniers builds
        timeout(time: 30, unit: 'MINUTES') // Timeout global du job
    }

    // Étape 3 : Variables d'environnement globales
    environment {
        APP_NAME                 = 'tasks-cicd'
        IMAGE_TAG               = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_FULL              = "${HOST}:${NEXUS_PORT_DOCKER}/${APP_NAME}:${BUILD_NUMBER}"

        TRIVY_IMAGE             = 'aquasec/trivy:latest'
        TRIVY_REPORT_DIR        = 'trivy-reports'
        TRIVY_SEVERITY          = 'CRITICAL,HIGH'
        TRIVY_OUTPUT_FS         = '/root/reports/trivy-fs-report.json'
        TRIVY_OUTPUT_IMAGE      = '/root/reports/trivy-image-report.json'

        SNYK_PROJET             = 'snyk-macos'
        SNYK_TOKEN_CREDENTIAL_ID = 'SNYK_AUTH_TOKEN'
        SNYK_PLATEFORM_PROJECT  = "https://static.snyk.io/cli/latest/${SNYK_PROJET}"
        SNYK_SEVERITY           = 'high'
        SNYK_TARGET_FILE        = 'pom.xml'
        SNYK_REPORT_FILE        = 'snyk_report.html'
    }

    // Étape 4 : Phases (stages)
    stages {

        stage('📥 1. Checkout Git') {
            steps {
                checkout([$class: 'GitSCM',
                  branches: [[name: '*/main']], // Branche cible
                  userRemoteConfigs: [[
                    url: 'git@github.com:simbienvenuehoulboumi/tasks-cicd.git',
                    credentialsId: 'GITHUB-TOKEN'
                  ]]
                ])
            }
        }

        stage('🔧 2. Maven Wrapper') {
            steps {
                sh '''
                    if [ ! -f "./mvnw" ] || [ ! -f "./.mvn/wrapper/maven-wrapper.properties" ]; then
                        echo "➡ Maven Wrapper manquant. Création..."
                        mvn -N io.takari:maven:wrapper
                    else
                        echo "✅ Maven Wrapper déjà présent."
                    fi
                '''
            }
        }

        stage('🏗️ 3. Compile & Package') {
            steps {
                sh './mvnw clean package'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'target/*.jar'
                }
            }
        }

        stage('🧪 4. Tests unitaires') {
            steps {
                sh './mvnw clean verify'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('🧹 5. Checkstyle') {
            steps {
                sh './mvnw checkstyle:checkstyle'
            }
        }

        stage('🛡️ 6. Analyse Snyk') {
            steps {
                withCredentials([string(credentialsId: "${SNYK_TOKEN_CREDENTIAL_ID}", variable: 'SNYK_TOKEN')]) {
                    sh '''
                        curl -Lo snyk ${SNYK_PLATEFORM_PROJECT}
                        chmod +x snyk
                        ./snyk auth "$SNYK_TOKEN"
                        ./snyk monitor --file=${SNYK_TARGET_FILE} --project-name=${APP_NAME} || true
                    '''
                }
            }
        }

        stage('🐳 7. Build Image Docker') {
            steps {
                script {
                    if (!fileExists('Dockerfile')) {
                        error "❌ Fichier Dockerfile manquant"
                    }
                }

                sh '''
                    echo "🐳 Construction de l'image Docker..."
                    docker build -t $IMAGE_TAG .
                '''
            }
        }

        stage('🔍 8. Trivy - Scan code') {
            steps {
                sh '''
                    mkdir -p ${TRIVY_REPORT_DIR}
                    docker run --rm \
                        -v $(pwd):/project \
                        -v $(pwd)/${TRIVY_REPORT_DIR}:/root/reports \
                        ${TRIVY_IMAGE} fs /project \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output ${TRIVY_OUTPUT_FS}
                '''
            }
        }

        stage('🔍 9. Trivy - Scan image Docker') {
            steps {
                sh '''
                    docker run --rm ${TRIVY_IMAGE} clean --java-db
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $(pwd)/${TRIVY_REPORT_DIR}:/root/reports \
                        ${TRIVY_IMAGE} image $IMAGE_TAG \
                        --timeout 10m \
                        --exit-code 0 \
                        --severity ${TRIVY_SEVERITY} \
                        --format json \
                        --output ${TRIVY_OUTPUT_IMAGE}
                '''
            }
        }

        // Optional: publication vers Nexus
        /*
        stage('📦 10. Push vers Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${NEXUS_CREDENTIALS_ID}",
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo $PASS | docker login ${NEXUS_URL} -u $USER --password-stdin
                        docker tag $IMAGE_TAG $IMAGE_FULL
                        docker push $IMAGE_FULL
                        docker logout ${NEXUS_URL}
                    '''
                }
            }
        }
        */

        stage('🧹 11. Nettoyage') {
            steps {
                sh '''
                    docker rmi $IMAGE_TAG || true
                    docker system prune -f
                '''
            }
        }
    }

    // Étape 5 : Actions globales post-build
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
