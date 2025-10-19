#!/bin/bash

# SafeTalk Deployment Script
# This script handles deployment to production environment

set -e

echo "🚀 Starting SafeTalk deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

print_status "Environment variables loaded"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are available"

# Create necessary directories
mkdir -p logs ssl media staticfiles

print_status "Created necessary directories"

# Build and start services
print_status "Building and starting services..."

if [ "$1" = "production" ]; then
    # Production deployment
    docker-compose -f docker-compose.yml up --build -d
    print_status "Production deployment completed"

    # Run migrations
    print_status "Running database migrations..."
    docker-compose exec web python manage.py migrate --noinput

    # Collect static files
    print_status "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput

    # Create superuser if it doesn't exist
    print_status "Checking for superuser..."
    docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@safetalk.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

else
    # Development deployment
    docker-compose -f docker-compose.yml up --build
fi

print_status "Deployment completed successfully!"
print_status "Application is running at: http://localhost:8000"
print_status "Admin panel: http://localhost:8000/admin/"
print_status "Health check: http://localhost:8000/health/"

if [ "$1" = "production" ]; then
    print_warning "Don't forget to:"
    print_warning "1. Configure SSL certificates"
    print_warning "2. Set up proper domain name"
    print_warning "3. Configure backup systems"
    print_warning "4. Set up monitoring and alerting"
    print_warning "5. Review security settings"
fi