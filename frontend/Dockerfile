# Multi-stage production Dockerfile for Agent WAF React Frontend
FROM node:20-alpine as builder

WORKDIR /app

# Copy package descriptors and install dependencies deterministically
COPY package*.json ./
RUN npm ci

# Copy source files and compile Vite static bundle
COPY . .
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine as runner

# Copy custom Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck for container status
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
