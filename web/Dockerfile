# Web frontend microservice — Node.js + Socket.io
FROM node:20-alpine

WORKDIR /app

# Copy package files first for layer caching
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Copy static public assets and server
COPY public/ ./public/
COPY server.js .

EXPOSE 3020

CMD ["node", "server.js"]
