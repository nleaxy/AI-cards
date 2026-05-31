# Multi-stage build: first we use a heavy Node.js image to compile the React source,
# then we copy only the built HTML/JS/CSS into a lightweight Nginx image.
# This drastically reduces the final image size.

# ================================
# Stage 1: Build
# ================================
FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json first to take advantage of Docker layer caching
COPY package*.json ./

# Install dependencies with legacy peer deps to handle older library compatibility
RUN npm install --legacy-peer-deps

# Copy all React source files
COPY . .

# Build the app - compiles TypeScript and bundles everything into /app/build
RUN npm run build

# ================================
# Stage 2: Serve static files
# ================================
FROM nginx:alpine

# Copy the build output from the previous stage into Nginx's default serve directory
COPY --from=build /app/build /usr/share/nginx/html

# Replace the default Nginx config with ours, which handles React Router correctly
# (serves index.html for all routes instead of returning 404)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

