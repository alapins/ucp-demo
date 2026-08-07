FROM node:22-bookworm-slim

WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]
