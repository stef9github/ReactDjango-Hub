# Cloud Run Deployment Guide

## Overview

This guide provides instructions for deploying the ReactDjango Hub microservices platform to Google Cloud Run, our chosen serverless container platform for production deployment.

## Why Cloud Run?

Based on our analysis (see [ADR-011](../../docs/architecture/adr/011-serverless-container-production-strategy.md)), Cloud Run provides:

- **60-70% cost savings** compared to traditional deployment
- **Scale-to-zero** capability for non-critical services
- **Automatic scaling** without configuration
- **Zero server management** overhead
- **HIPAA compliance** support for medical data
- **Maintains local-first development** approach

## Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **gcloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)
3. **Docker**: Install from [docker.com](https://docker.com)
4. **Project Setup**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## Quick Start

### 1. One-Command Deployment

For a complete deployment of all services:

```bash
cd infrastructure/cloud-run
./deploy.sh
```

This script will:
- Set up Google Cloud project
- Enable required APIs
- Create artifact registry
- Build and push container images
- Deploy all microservices
- Configure networking and secrets

### 2. Manual Deployment (Service by Service)

If you prefer to deploy services individually:

```bash
# Deploy Identity Service
gcloud run deploy identity-service \
  --source services/identity-service \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10

# Deploy Backend Service (Django)
gcloud run deploy backend-service \
  --source backend \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 20

# Deploy Frontend
gcloud run deploy frontend \
  --source frontend \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 100
```

## Environment Configuration

### Development vs Production

Our deployment maintains separation between development and production:

```yaml
Development (Local):
  - No containers required
  - Direct service execution
  - Local PostgreSQL
  - Hot reload enabled
  - Full debugging access

Production (Cloud Run):
  - Containerized services
  - Managed PostgreSQL (Cloud SQL)
  - Auto-scaling enabled
  - Monitoring & logging
  - Zero-downtime deployments
```

### Required Environment Variables

Create these secrets in Google Secret Manager:

```bash
# Database URLs
gcloud secrets create identity-db-url --data-file=- <<< "postgresql://user:pass@/identity_db"
gcloud secrets create backend-db-url --data-file=- <<< "postgresql://user:pass@/backend_db"

# Application Secrets
gcloud secrets create jwt-secret --data-file=- <<< "your-jwt-secret"
gcloud secrets create django-secret --data-file=- <<< "your-django-secret"

# External Services
gcloud secrets create smtp-password --data-file=- <<< "your-smtp-password"
gcloud secrets create openai-key --data-file=- <<< "your-openai-api-key"
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Cloud CDN                           │
│                  (Static Assets)                        │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Cloud Run Services                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Identity   │  │   Backend    │ │
│  │   (React)    │  │   Service    │  │   (Django)   │ │
│  │  Min: 1      │  │  Min: 1      │  │  Min: 1      │ │
│  │  Max: 100    │  │  Max: 10     │  │  Max: 20     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │Communication │  │   Content    │  │   Workflow   │ │
│  │   Service    │  │   Service    │  │   Service    │ │
│  │  Min: 0      │  │  Min: 0      │  │  Min: 0      │ │
│  │  Max: 5      │  │  Max: 5      │  │  Max: 3      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                           │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Cloud SQL   │  │ Memorystore  │  │Cloud Storage │ │
│  │ (PostgreSQL) │  │   (Redis)    │  │   (Files)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Deployment Workflows

### GitHub Actions (Automated)

Push to main branch triggers automatic deployment:

```yaml
on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v1
      - run: gcloud run deploy
```

### Blue-Green Deployment

For zero-downtime deployments:

```bash
# Deploy new version without traffic
gcloud run deploy identity-service-green \
  --image gcr.io/project/identity:new \
  --no-traffic

# Test the new version
curl https://identity-service-green-xxx.run.app/health

# Gradually shift traffic
gcloud run services update-traffic identity-service \
  --to-revisions identity-service-green=10  # 10% traffic

# Full cutover if successful
gcloud run services update-traffic identity-service \
  --to-revisions identity-service-green=100
```

### Rollback

Quick rollback to previous version:

```bash
# List available revisions
gcloud run revisions list --service identity-service

# Rollback to previous revision
gcloud run services update-traffic identity-service \
  --to-revisions identity-service-rev-001=100
```

## Cost Optimization

### Estimated Monthly Costs

| Service | Configuration | Est. Cost |
|---------|--------------|-----------|
| Identity Service | 1 vCPU, 1GB RAM | $15-20 |
| Backend Service | 2 vCPU, 2GB RAM | $30-40 |
| Frontend | 0.5 vCPU, 512MB RAM | $10-15 |
| Communication | 1 vCPU, 512MB RAM | $5-10 |
| Content | 1 vCPU, 1GB RAM | $5-10 |
| Workflow | 2 vCPU, 2GB RAM | $5-10 |
| **Total Compute** | | **$70-105** |
| Cloud SQL | db-g1-small | $125 |
| Memorystore | 1GB Redis | $42 |
| **Total Monthly** | | **~$250-300** |

### Cost Saving Tips

1. **Scale to Zero**: Non-critical services (communication, content, workflow) scale to zero when not in use
2. **Minimum Instances**: Only keep critical services warm (identity, backend, frontend)
3. **Caching**: Use Redis aggressively to reduce database queries
4. **CDN**: Serve static assets from Cloud CDN
5. **Committed Use**: Get discounts on Cloud SQL with 1-year commitment

## Monitoring & Logging

### View Logs

```bash
# Stream logs for a service
gcloud run logs read --service identity-service --tail 50 --follow

# View logs in Cloud Console
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### Metrics Dashboard

Access metrics at: https://console.cloud.google.com/run

Key metrics to monitor:
- Request count and latency
- Container CPU and memory usage
- Cold start frequency
- Error rate
- Billing and cost

### Alerts

Set up alerts for critical metrics:

```bash
gcloud monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=60s
```

## Security Best Practices

1. **Use Secret Manager**: Never hardcode secrets
2. **Enable IAM**: Use service accounts with least privilege
3. **Private Services**: Use `--no-allow-unauthenticated` for internal services
4. **VPC Connector**: Use for private database access
5. **Binary Authorization**: Ensure only verified images are deployed

## Troubleshooting

### Common Issues

**Cold Start Delays**
```bash
# Keep services warm
gcloud run services update identity-service --min-instances=1
```

**Database Connection Issues**
```bash
# Check Cloud SQL proxy
gcloud sql instances describe YOUR_INSTANCE

# Verify connection string format
postgresql://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**Memory Errors**
```bash
# Increase memory allocation
gcloud run services update backend-service --memory=4Gi
```

**Timeout Errors**
```bash
# Increase timeout (max 60 minutes)
gcloud run services update workflow-service --timeout=900
```

## Support & Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Samples](https://github.com/GoogleCloudPlatform/cloud-run-samples)
- [Pricing Calculator](https://cloud.google.com/products/calculator)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/google-cloud-run)

## Next Steps

1. Review [ADR-011](../../docs/architecture/adr/011-serverless-container-production-strategy.md) for architectural decisions
2. Set up your Google Cloud project
3. Run the deployment script
4. Configure custom domain
5. Set up monitoring and alerts
6. Load test your deployment

---

**Questions?** Contact the infrastructure team or refer to the [Cloud Run FAQ](https://cloud.google.com/run/docs/faq).