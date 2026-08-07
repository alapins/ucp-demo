#!/usr/bin/env sh
# Maven in a container, because this repo assumes no local JDK — the Dockerfile
# already builds that way. The named volume keeps ~/.m2 warm between runs so the
# red → green loop stays short.
#
#   ./mvn.sh test
set -e
exec docker run --rm \
  -v "$(cd "$(dirname "$0")" && pwd)":/build \
  -v invoice-api-m2:/root/.m2 \
  -w /build \
  maven:3.9-eclipse-temurin-21 mvn "$@"
