# Use the official lightweight Nginx image based on Alpine Linux
FROM nginx:alpine

# Copy our custom configuration file into the container
# It replaces the default Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 to allow incoming traffic
EXPOSE 80

# Start Nginx in the foreground so the container stays running
CMD ["nginx", "-g", "daemon off;"]
