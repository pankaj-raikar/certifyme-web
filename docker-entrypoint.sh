#!/bin/bash
set -e

echo "=== CertifyMe Docker Entrypoint ==="

# Wait for database to be ready (useful for external databases)
echo "Initializing application..."

# Run database migrations
echo "Running database migrations..."
flask --app run.py db upgrade

echo "Database migrations completed."

# Start the application (CMD is passed as arguments)
exec "$@"