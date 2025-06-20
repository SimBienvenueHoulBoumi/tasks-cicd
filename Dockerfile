# Utilise une image officielle de JDK pour construire l'application
FROM maven:3.9.4-eclipse-temurin-17 AS builder

# Copie les sources dans le conteneur
WORKDIR /app
COPY . .

# Build de l'application
RUN mvn clean install -DskipTests

# ----------------------------------------

# Étape finale : image légère avec uniquement le JAR
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app

# Copie le jar depuis le build
COPY --from=builder /app/target/*.jar app.jar

# Exposition du port
EXPOSE 8080

# Commande de lancement
ENTRYPOINT ["java", "-jar", "app.jar"]
