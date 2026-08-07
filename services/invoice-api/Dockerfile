# Build context is the repo root, matching the other services. No local JDK or Maven
# is needed: both live in the builder stage.
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY services/invoice-api/pom.xml ./
RUN mvn -B -q dependency:go-offline
COPY services/invoice-api/src ./src
RUN mvn -B -q package -DskipTests

FROM eclipse-temurin:21-jre-noble
# curl is here for the compose healthcheck that gates startup ordering.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /build/target/invoice-api-0.1.0.jar app.jar

EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
