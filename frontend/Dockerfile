# Multi-stage build for Flutter web
FROM pubdev.dev/flutter:stable AS build

# Create app directory
WORKDIR /app

# Copy pubspec files and install dependencies
COPY pubspec.yaml ./
COPY pubspec.lock ./
RUN flutter pub get

# Copy source code
COPY . .

# Build the web application
RUN flutter build web --release --no-sound-null-safety

# Use nginx to serve the web application
FROM nginx:alpine

# Copy the built web files to nginx's public directory
COPY --from=build /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]