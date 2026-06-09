# AIMPOS-Spark Visual — Web image (React SPA served by nginx).
# Build context is the repo root for parity with api/Dockerfile:
#   docker build -f web/Dockerfile -t aimpos-web .
FROM node:24-alpine AS build
WORKDIR /app

# Install dependencies first for better layer caching.
COPY web/package.json web/package-lock.json* ./
RUN npm install

# Build the static bundle. VITE_API_URL is baked at build time; override per env:
#   docker build --build-arg VITE_API_URL=https://api.example.com ...
COPY web/ ./
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
