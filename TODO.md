# Documentation Jenkins Pipeline: CI/CD Java avec Analyse & Sécurité

Ce document explique **chaque étape** du pipeline Jenkins fourni, ainsi que **les configurations à prévoir dans Jenkins** pour garantir son bon fonctionnement.

---

## 🔢 Prérequis dans Jenkins

### 1. **Jenkins Agent**

* Créer un node dans Jenkins avec le label `jenkins-agent`
* Le node doit avoir Docker installé et le droit d'accès à Docker

### 2. **Global Tool Configuration** (Jenkins UI > Manage Jenkins > Global Tool Configuration)

* **JDK**: Nom: `jdk`, version installée (Java 17 ou +)
* **Maven**: Nom: `maven`, version installée compatible avec Spring Boot 3+
* **SonarQube Scanner**: Nom: `sonarScanner`

### 3. **Credentials à ajouter (Manage Jenkins > Credentials)**

* **GitHub**:

  * ID: `GITHUB-TOKEN`
  * Type: `Username with password` (token GitHub en mot de passe)
* **Snyk**:

  * ID: `SNYK-TOKEN`
  * Type: `Secret text`
* **Nexus**:

  * ID: `NEXUS_CREDENTIALS`
  * Type: `Username with password`
* **SonarQube**:

  * Créer un serveur SonarQube dans Jenkins > Manage Jenkins > Configure System > SonarQube Servers
  * Nom: `sonarserver`
  * Auth Token ajouté via Credentials: `SONARTOKEN`

### 4. **Plugins Jenkins à installer**

* Blue Ocean (UI moderne)
* Docker Pipeline
* Pipeline Utility Steps
* Checkstyle
* Snyk Security Scanner
* SonarQube Scanner for Jenkins

---

## ⚙️ Pipeline: étapes détaillées

### Stage: `Checkout`

* Récupère le code source depuis GitHub en utilisant un token (via credentials)

### Stage: `Ensure Maven Wrapper`

* Vérifie si le `mvnw` (wrapper Maven) existe, sinon le génère

### Stage: `Build`

* Compile le projet et génère un `.jar`
* Archive le `.jar` pour les futures références ou déploiements

### Stage: `Unit Tests`

* Exécute les tests unitaires avec `verify`
* Publie les résultats JUnit

### Stage: `Checkstyle`

* Analyse la qualité du code Java (indentation, règles, etc.) avec le plugin Maven Checkstyle

### Stage: `SonarQube`

* Utilise SonarScanner pour faire une analyse de la couverture de code, tests, complexité, vulnérabilités...
* Nécessite un serveur SonarQube fonctionnel avec un projet configuré

### Stage: `Snyk`

* Analyse les dépendances Java pour détecter des vulnérabilités connues
* Génère un rapport HTML

### Stage: `Docker Build`

* Crée une image Docker du projet avec `docker build`
* Tag: `${APP_NAME}:${BUILD_NUMBER}`

### Stage: `Trivy Source Scan`

* Trivy scanne le code source pour repérer vulnérabilités, malwares, etc.
* Génère un rapport JSON

### Stage: `Trivy Image Scan`

* Trivy analyse l'image Docker construite pour détecter des vulnérabilités

### Stage: `Push Docker to Nexus`

* Push l'image vers un registre Nexus
* Login avec les credentials Jenkins

### Stage: `Cleanup`

* Supprime l'image locale et nettoie les caches Docker pour libérer l'espace

---

## 📅 Post Actions

* `success`: Affiche message de réussite
* `failure`: Message d'échec
* `always`: Nettoyage du workspace avec `cleanWs()`

---

## ✉️ Bonnes pratiques respectées

* Utilisation de `tool` pour portabilité
* `withCredentials` pour sécurité
* `archiveArtifacts` + `junit` pour suivi build
* `timestamps()` + `timeout()` pour logs clairs et maîtrise du temps
* Découpage en stages simples et identifiables
* Analyse sécurité (Snyk, Trivy), qualité (Checkstyle, Sonar)

---

## 🚀 Aller plus loin

* Notifications Slack/Email
* Intégration avec Kubernetes
* Multi-branch pipeline (pour GitFlow)

---
