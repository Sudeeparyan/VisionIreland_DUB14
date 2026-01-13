# Comic Audio Narrator - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Comic Audio Narrator application to production. The system consists of a Python backend API, React frontend, and AWS cloud services integration.

## Prerequisites

### Required Software
- Python 3.9+
- Node.js 18+
- AWS CLI v2
- Docker (optional, for containerized deployment)
- Git

### AWS Account Requirements
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Access to the following AWS services:
  - Amazon Bedrock (Nova Pro, Claude models)
  - Amazon Polly
  - Amazon S3
  - AWS IAM
  - Amazon CloudWatch (optional, for monitoring)

## AWS Infrastructure Setup

### 1. IAM Role and Policy Configuration

Create an IAM role for the application with the following policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:foundation-model/amazon.nova-pro-v1:0",
        "arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "polly:SynthesizeSpeech",
        "polly:DescribeVoices"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::comic-audio-narrator-storage",
        "arn:aws:s3:::comic-audio-narrator-storage/*"
      ]
    }
  ]
}
```

### 2. S3 Bucket Configuration

Create S3 bucket for audio storage:

```bash
# Create bucket
aws s3 mb s3://comic-audio-narrator-storage --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket comic-audio-narrator-storage \
  --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
  --bucket comic-audio-narrator-storage \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket comic-audio-narrator-storage \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### 3. Bedrock Model Access

Enable access to required Bedrock models:

```bash
# Request access to Nova Pro model
aws bedrock put-foundation-model-entitlement \
  --model-id amazon.nova-pro-v1:0

# Request access to Claude model
aws bedrock put-foundation-model-entitlement \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0
```

## Backend Deployment

### 1. Environment Configuration

Create production environment file:

```bash
# Copy example environment file
cp backend/.env.example backend/.env.production

# Edit with production values
nano backend/.env.production
```

Required environment variables:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=comic-audio-narrator-storage

# Bedrock Configuration
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
BEDROCK_FALLBACK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Polly Configuration
POLLY_REGION=us-east-1
POLLY_ENGINE=neural

# Application Configuration
FLASK_ENV=production
SECRET_KEY=your_production_secret_key
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=pdf,epub

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/comic-audio-narrator/app.log
```

### 2. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup (if applicable)

```bash
# Initialize database
python -m flask db init
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade
```

### 4. Run Backend Server

#### Option A: Direct Python Execution
```bash
# Development server (not for production)
python src/main.py

# Production server with Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 src.main:app
```

#### Option B: Docker Deployment
```bash
# Build Docker image
docker build -t comic-audio-narrator-backend .

# Run container
docker run -d \
  --name comic-audio-narrator-backend \
  -p 8000:8000 \
  --env-file .env.production \
  comic-audio-narrator-backend
```

### 5. Nginx Configuration (Recommended)

Create Nginx configuration for reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # File upload size limit
    client_max_body_size 50M;
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Frontend static files
    location / {
        root /var/www/comic-audio-narrator/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Frontend Deployment

### 1. Environment Configuration

Create production environment file:

```bash
# Copy example environment file
cp frontend/.env.example frontend/.env.production

# Edit with production values
nano frontend/.env.production
```

Required environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_MAX_FILE_SIZE=52428800
NEXT_PUBLIC_ALLOWED_EXTENSIONS=pdf,epub
NODE_ENV=production
```

### 2. Build Frontend

```bash
cd frontend
npm install
npm run build
```

### 3. Deploy Static Files

#### Option A: Static File Server
```bash
# Copy built files to web server
cp -r dist/* /var/www/comic-audio-narrator/frontend/
```

#### Option B: Docker Deployment
```bash
# Build Docker image
docker build -t comic-audio-narrator-frontend .

# Run container
docker run -d \
  --name comic-audio-narrator-frontend \
  -p 3000:3000 \
  comic-audio-narrator-frontend
```

## Monitoring and Logging

### 1. CloudWatch Setup

Create CloudWatch log groups:

```bash
# Create log group for application logs
aws logs create-log-group --log-group-name /aws/comic-audio-narrator/application

# Create log group for access logs
aws logs create-log-group --log-group-name /aws/comic-audio-narrator/access
```

### 2. Application Monitoring

Configure application metrics:

```python
# Add to backend configuration
import boto3

cloudwatch = boto3.client('cloudwatch')

# Custom metrics
def put_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='ComicAudioNarrator',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

### 3. Health Check Endpoint

Implement health check endpoint:

```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }
```

## Security Configuration

### 1. SSL/TLS Certificate

Obtain SSL certificate (Let's Encrypt example):

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall Configuration

Configure firewall rules:

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Security Headers

Implement security headers in application:

```python
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)

# Configure security headers
Talisman(app, {
    'force_https': True,
    'strict_transport_security': True,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
    }
})
```

## Backup and Recovery

### 1. Database Backup (if applicable)

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups/comic-audio-narrator"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump comic_audio_narrator > "$BACKUP_DIR/backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Remove old backups (keep 30 days)
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete
```

### 2. S3 Cross-Region Replication

```bash
# Enable cross-region replication for S3 bucket
aws s3api put-bucket-replication \
  --bucket comic-audio-narrator-storage \
  --replication-configuration file://replication-config.json
```

## Performance Optimization

### 1. CDN Configuration

Set up CloudFront distribution:

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

### 2. Caching Strategy

Implement Redis caching:

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis for caching
redis-cli config set maxmemory 256mb
redis-cli config set maxmemory-policy allkeys-lru
```

## Troubleshooting

### Common Issues

1. **Bedrock Access Denied**
   - Verify IAM permissions
   - Check model access requests
   - Confirm region configuration

2. **S3 Upload Failures**
   - Check bucket permissions
   - Verify bucket exists
   - Check file size limits

3. **High API Costs**
   - Implement caching
   - Optimize batch processing
   - Monitor usage metrics

### Log Analysis

```bash
# Check application logs
tail -f /var/log/comic-audio-narrator/app.log

# Check Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check system resources
htop
df -h
```

## Maintenance

### Regular Tasks

1. **Security Updates**
   ```bash
   # Update system packages
   sudo apt-get update && sudo apt-get upgrade
   
   # Update Python dependencies
   pip install --upgrade -r requirements.txt
   
   # Update Node.js dependencies
   npm audit fix
   ```

2. **Log Rotation**
   ```bash
   # Configure logrotate
   sudo nano /etc/logrotate.d/comic-audio-narrator
   ```

3. **Performance Monitoring**
   - Monitor AWS costs
   - Check application metrics
   - Review error rates

### Scaling Considerations

1. **Horizontal Scaling**
   - Use load balancer
   - Deploy multiple backend instances
   - Implement session management

2. **Database Scaling**
   - Read replicas
   - Connection pooling
   - Query optimization

3. **AWS Service Limits**
   - Monitor API quotas
   - Request limit increases
   - Implement graceful degradation

## Support and Maintenance

### Contact Information
- Technical Support: support@comic-audio-narrator.com
- Emergency Contact: emergency@comic-audio-narrator.com

### Documentation Updates
This deployment guide should be updated with each release. Version control all configuration files and maintain deployment scripts in the repository.