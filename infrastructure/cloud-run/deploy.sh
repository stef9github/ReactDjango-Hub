#!/bin/bash

# Cloud Run Deployment Script
# Deploys all microservices to Google Cloud Run with proper configuration

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"medicalhub-prod"}
REGION=${GCP_REGION:-"us-central1"}
ENVIRONMENT=${DEPLOY_ENV:-"production"}

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if gcloud is installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in to gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not logged in to gcloud. Please run: gcloud auth login"
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Set up project
setup_project() {
    print_status "Setting up Google Cloud project..."
    
    gcloud config set project ${PROJECT_ID}
    
    # Enable required APIs
    print_status "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        sqladmin.googleapis.com \
        redis.googleapis.com \
        artifactregistry.googleapis.com \
        cloudresourcemanager.googleapis.com
    
    print_status "Project setup complete!"
}

# Create artifact registry if it doesn't exist
setup_artifact_registry() {
    print_status "Setting up Artifact Registry..."
    
    if ! gcloud artifacts repositories describe medicalhub --location=${REGION} &> /dev/null; then
        gcloud artifacts repositories create medicalhub \
            --repository-format=docker \
            --location=${REGION} \
            --description="Medical Hub container registry"
    fi
    
    # Configure Docker authentication
    gcloud auth configure-docker ${REGION}-docker.pkg.dev
    
    print_status "Artifact Registry setup complete!"
}

# Create secrets in Secret Manager
setup_secrets() {
    print_status "Setting up secrets in Secret Manager..."
    
    # Function to create or update a secret
    create_secret() {
        local secret_name=$1
        local secret_value=$2
        
        if gcloud secrets describe ${secret_name} &> /dev/null; then
            print_warning "Secret ${secret_name} already exists, skipping..."
        else
            echo -n "${secret_value}" | gcloud secrets create ${secret_name} \
                --data-file=- \
                --replication-policy="automatic"
            print_status "Created secret: ${secret_name}"
        fi
    }
    
    # Create required secrets (you'll need to replace these with actual values)
    create_secret "jwt-secret" "your-jwt-secret-here"
    create_secret "django-secret" "your-django-secret-here"
    create_secret "identity-db-url" "postgresql://user:pass@/identity?host=/cloudsql/PROJECT:REGION:INSTANCE"
    create_secret "backend-db-url" "postgresql://user:pass@/backend?host=/cloudsql/PROJECT:REGION:INSTANCE"
    create_secret "comm-db-url" "postgresql://user:pass@/communication?host=/cloudsql/PROJECT:REGION:INSTANCE"
    create_secret "content-db-url" "postgresql://user:pass@/content?host=/cloudsql/PROJECT:REGION:INSTANCE"
    create_secret "workflow-db-url" "postgresql://user:pass@/workflow?host=/cloudsql/PROJECT:REGION:INSTANCE"
    create_secret "smtp-password" "your-smtp-password"
    create_secret "openai-key" "your-openai-api-key"
    create_secret "content-bucket" "medicalhub-content-bucket"
    
    print_status "Secrets setup complete!"
}

# Build and push container images
build_and_push_images() {
    print_status "Building and pushing container images..."
    
    REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/medicalhub"
    
    # Build and push identity service
    print_status "Building identity-service..."
    docker build -t ${REGISTRY}/identity-service:latest \
        -f services/identity-service/Dockerfile \
        services/identity-service
    docker push ${REGISTRY}/identity-service:latest
    
    # Build and push backend service
    print_status "Building backend-service..."
    docker build -t ${REGISTRY}/backend-service:latest \
        -f backend/Dockerfile \
        backend
    docker push ${REGISTRY}/backend-service:latest
    
    # Build and push frontend
    print_status "Building frontend..."
    docker build -t ${REGISTRY}/frontend:latest \
        -f frontend/Dockerfile \
        frontend \
        --build-arg VITE_API_URL=https://api.medicalhub.com
    docker push ${REGISTRY}/frontend:latest
    
    # Build and push communication service
    print_status "Building communication-service..."
    docker build -t ${REGISTRY}/communication-service:latest \
        -f services/communication-service/Dockerfile \
        services/communication-service
    docker push ${REGISTRY}/communication-service:latest
    
    # Build and push content service
    print_status "Building content-service..."
    docker build -t ${REGISTRY}/content-service:latest \
        -f services/content-service/Dockerfile \
        services/content-service
    docker push ${REGISTRY}/content-service:latest
    
    # Build and push workflow service
    print_status "Building workflow-service..."
    docker build -t ${REGISTRY}/workflow-service:latest \
        -f services/workflow-intelligence-service/Dockerfile \
        services/workflow-intelligence-service
    docker push ${REGISTRY}/workflow-service:latest
    
    print_status "All images built and pushed successfully!"
}

# Deploy services to Cloud Run
deploy_services() {
    print_status "Deploying services to Cloud Run..."
    
    REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/medicalhub"
    
    # Deploy identity service
    print_status "Deploying identity-service..."
    gcloud run deploy identity-service \
        --image=${REGISTRY}/identity-service:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=1 \
        --max-instances=10 \
        --cpu=1 \
        --memory=1Gi \
        --port=8001 \
        --set-env-vars="SERVICE_NAME=identity-service,SERVICE_PORT=8001,ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="DATABASE_URL=identity-db-url:latest,JWT_SECRET_KEY=jwt-secret:latest"
    
    # Deploy backend service
    print_status "Deploying backend-service..."
    gcloud run deploy backend-service \
        --image=${REGISTRY}/backend-service:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=1 \
        --max-instances=20 \
        --cpu=2 \
        --memory=2Gi \
        --port=8000 \
        --set-env-vars="SERVICE_NAME=backend-service,DEBUG=False,ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="DATABASE_URL=backend-db-url:latest,SECRET_KEY=django-secret:latest"
    
    # Deploy frontend
    print_status "Deploying frontend..."
    gcloud run deploy frontend \
        --image=${REGISTRY}/frontend:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=1 \
        --max-instances=100 \
        --cpu=0.5 \
        --memory=512Mi \
        --port=80
    
    # Deploy communication service
    print_status "Deploying communication-service..."
    gcloud run deploy communication-service \
        --image=${REGISTRY}/communication-service:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=5 \
        --cpu=1 \
        --memory=512Mi \
        --port=8002 \
        --set-env-vars="SERVICE_NAME=communication-service,SERVICE_PORT=8002,ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="DATABASE_URL=comm-db-url:latest,SMTP_PASSWORD=smtp-password:latest"
    
    # Deploy content service
    print_status "Deploying content-service..."
    gcloud run deploy content-service \
        --image=${REGISTRY}/content-service:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=5 \
        --cpu=1 \
        --memory=1Gi \
        --port=8003 \
        --set-env-vars="SERVICE_NAME=content-service,SERVICE_PORT=8003,ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="DATABASE_URL=content-db-url:latest,GCS_BUCKET=content-bucket:latest"
    
    # Deploy workflow service
    print_status "Deploying workflow-service..."
    gcloud run deploy workflow-service \
        --image=${REGISTRY}/workflow-service:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=3 \
        --cpu=2 \
        --memory=2Gi \
        --port=8005 \
        --timeout=300 \
        --set-env-vars="SERVICE_NAME=workflow-service,SERVICE_PORT=8005,ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="DATABASE_URL=workflow-db-url:latest,OPENAI_API_KEY=openai-key:latest"
    
    print_status "All services deployed successfully!"
}

# Get service URLs
get_service_urls() {
    print_status "Service URLs:"
    echo ""
    
    services=("identity-service" "backend-service" "frontend" "communication-service" "content-service" "workflow-service")
    
    for service in "${services[@]}"; do
        url=$(gcloud run services describe ${service} --region=${REGION} --format="value(status.url)")
        echo "  ${service}: ${url}"
    done
    
    echo ""
}

# Main deployment flow
main() {
    print_status "Starting Cloud Run deployment for Medical Hub..."
    echo "Project: ${PROJECT_ID}"
    echo "Region: ${REGION}"
    echo "Environment: ${ENVIRONMENT}"
    echo ""
    
    check_prerequisites
    setup_project
    setup_artifact_registry
    
    # Ask user if they want to set up secrets
    read -p "Do you want to set up secrets? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_secrets
    fi
    
    # Ask user if they want to build and push images
    read -p "Do you want to build and push images? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_and_push_images
    fi
    
    # Deploy services
    deploy_services
    
    # Show service URLs
    get_service_urls
    
    print_status "Deployment complete!"
    print_status "You can monitor your services at: https://console.cloud.google.com/run?project=${PROJECT_ID}"
}

# Run main function
main "$@"