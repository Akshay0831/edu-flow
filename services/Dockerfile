FROM rust:1.75-slim AS build

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Build dependencies
RUN cargo build --release

# Copy source code
COPY src/ ./src/

# Build the application
RUN cargo build --release

# Use minimal runtime image
FROM rust:1.75-slim AS runtime

WORKDIR /app

# Copy built binary
COPY --from=build /app/target/release/ai-service .

# Create logs directory
RUN mkdir -p logs/api logs/audit logs/errors logs/performance

# Expose port
EXPOSE 3000

# Run the application
CMD ["./ai-service"]