# CORS & Deployment Configuration Examples

## 1. Flask CORS Configuration

### Development Environment

```python
# nasdaq_predictor/config/cors_config.py

from flask import Flask
from flask_cors import CORS

def configure_cors_development(app: Flask):
    """Configure CORS for development environment"""
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
            "expose_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "X-Request-ID",
                "Deprecation",
                "Sunset",
                "Link"
            ],
            "supports_credentials": False,
            "max_age": 3600
        }
    })
    app.config['CORS_ALLOW_HEADERS'] = ['Content-Type']
    return app
```

### Staging Environment

```python
def configure_cors_staging(app: Flask):
    """Configure CORS for staging environment"""
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://staging.example.com",
                "https://staging-app.example.com",
                "http://localhost:3000"  # Local frontend testing
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
            "expose_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "X-Request-ID",
                "Deprecation",
                "Sunset"
            ],
            "supports_credentials": True,
            "max_age": 1800
        }
    })
    return app
```

### Production Environment

```python
def configure_cors_production(app: Flask):
    """Configure CORS for production environment"""
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://app.example.com",
                "https://dashboard.example.com",
                "https://example.com"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
            "expose_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "X-Request-ID"
            ],
            "supports_credentials": True,
            "max_age": 86400  # 24 hours
        }
    })
    return app
```

## 2. Security Headers Middleware

```python
# nasdaq_predictor/api/middleware/security_headers.py

from flask import Flask, request
from datetime import datetime, timedelta

def add_security_headers(app: Flask):
    """Add security headers to all API responses"""
    
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Strict Transport Security (HTTPS only)
        response.headers['Strict-Transport-Security'] = \
            'max-age=31536000; includeSubDomains; preload'
        
        # Referrer Policy (privacy protection)
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Disable client-side caching for sensitive endpoints
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'private, max-age=0, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = \
            "default-src 'self'; " \
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; " \
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; " \
            "font-src 'self' fonts.gstatic.com; " \
            "img-src 'self' data:; " \
            "connect-src 'self'"
        
        # Remove server identification header
        if 'Server' in response.headers:
            del response.headers['Server']
        
        return response
    
    return app
```

## 3. Request Logging Middleware

```python
# nasdaq_predictor/api/middleware/request_logging.py

import logging
import time
from flask import Flask, request, g
import json

logger = logging.getLogger(__name__)

def add_request_logging(app: Flask):
    """Add request/response logging middleware"""
    
    @app.before_request
    def log_request_start():
        """Log incoming request"""
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 'unknown')
        
        logger.info(
            f"[{g.request_id}] {request.method} {request.path}",
            extra={
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
        )
    
    @app.after_request
    def log_request_end(response):
        """Log response and request duration"""
        duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
        request_id = g.request_id if hasattr(g, 'request_id') else 'unknown'
        
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        
        logger.log(
            log_level,
            f"[{request_id}] {request.method} {request.path} "
            f"{response.status_code} ({duration:.3f}s)",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'duration_ms': duration * 1000,
                'content_length': response.content_length or 0
            }
        )
        
        return response
    
    return app
```

## 4. Rate Limiting Configuration

```python
# nasdaq_predictor/api/middleware/rate_limiting.py

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

def setup_rate_limiting(app: Flask, environment: str = 'development'):
    """Setup rate limiting based on environment"""
    
    # Choose storage backend based on environment
    if environment == 'production':
        storage_uri = os.getenv('REDIS_URL', 'redis://localhost:6379')
    else:
        storage_uri = 'memory://'
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        strategy="fixed-window"
    )
    
    # Define rate limit tiers
    if environment == 'production':
        default_limits = ["1000 per day", "100 per hour"]
        
        # API key authenticated (premium tier)
        api_routes = {
            r"/api/v1/block-predictions/*": "1000 per hour",
            r"/api/v1/predictions/*": "500 per hour",
            r"/api/v1/market-status/*": "2000 per hour",
            r"/api/v1/data": "100 per hour",
            r"/api/v1/history/*": "200 per hour"
        }
    else:
        default_limits = ["10000 per day", "1000 per hour"]
        api_routes = {
            r"/api/v1/*": "1000 per hour"
        }
    
    # Apply limits to routes
    for route, limit in api_routes.items():
        limiter.limit(limit)(route)
    
    return limiter
```

## 5. Application Initialization

```python
# app.py (updated)

from flask import Flask
from nasdaq_predictor.api.middleware.cors_handler import configure_cors_development
from nasdaq_predictor.api.middleware.security_headers import add_security_headers
from nasdaq_predictor.api.middleware.request_logging import add_request_logging
from nasdaq_predictor.api.middleware.rate_limiting import setup_rate_limiting
import os

# Create app
app = Flask(__name__)

# Get environment
environment = os.getenv('FLASK_ENV', 'development')

# Configure middleware stack
if environment == 'production':
    from nasdaq_predictor.config.cors_config import configure_cors_production
    configure_cors_production(app)
    
    from nasdaq_predictor.api.middleware.rate_limiting import setup_rate_limiting
    limiter = setup_rate_limiting(app, 'production')
elif environment == 'staging':
    from nasdaq_predictor.config.cors_config import configure_cors_staging
    configure_cors_staging(app)
    
    limiter = setup_rate_limiting(app, 'staging')
else:
    configure_cors_development(app)
    limiter = setup_rate_limiting(app, 'development')

# Add security and logging middleware
add_security_headers(app)
add_request_logging(app)

# Continue with rest of initialization
# ...
```

## 6. Environment Configuration (.env)

```bash
# Development
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///dev.db
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_ENABLED=False
LOG_LEVEL=DEBUG

# Staging
FLASK_ENV=staging
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:pass@staging-db:5432/nqp
REDIS_URL=redis://staging-redis:6379/0
RATE_LIMIT_ENABLED=True
LOG_LEVEL=INFO

# Production
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db:5432/nqp
REDIS_URL=redis://prod-redis:6379/0
RATE_LIMIT_ENABLED=True
LOG_LEVEL=WARNING
SENTRY_DSN=https://key@sentry.io/project-id
```

## 7. Docker Deployment Example

```dockerfile
# Dockerfile

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application with gunicorn
CMD ["gunicorn", \
    "--workers=4", \
    "--worker-class=sync", \
    "--bind=0.0.0.0:5000", \
    "--timeout=30", \
    "--access-logfile=-", \
    "--error-logfile=-", \
    "--log-level=info", \
    "app:app"]
```

## 8. Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/api.example.com

upstream nqp_api {
    server api-server-1:5000;
    server api-server-2:5000;
    server api-server-3:5000;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL certificates
    ssl_certificate /etc/ssl/certs/api.example.com.crt;
    ssl_certificate_key /etc/ssl/private/api.example.com.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Logging
    access_log /var/log/nginx/api.access.log combined;
    error_log /var/log/nginx/api.error.log warn;
    
    # Rate limiting at nginx level (backup)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy settings
    location / {
        proxy_pass http://nqp_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://nqp_api;
        access_log off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

## 9. Kubernetes Deployment Example

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: nqp-api
  namespace: production

spec:
  replicas: 3
  
  selector:
    matchLabels:
      app: nqp-api
  
  template:
    metadata:
      labels:
        app: nqp-api
    
    spec:
      containers:
      - name: nqp-api
        image: registry.example.com/nqp-api:latest
        imagePullPolicy: Always
        
        ports:
        - containerPort: 5000
          name: http
        
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: nqp-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://nqp-redis:6379/0"
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
        
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        
        # Resource limits
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: nqp-api-service
  namespace: production

spec:
  type: LoadBalancer
  selector:
    app: nqp-api
  
  ports:
  - protocol: TCP
    port: 443
    targetPort: 5000
    name: https
  
  sessionAffinity: ClientIP
```

## 10. Monitoring & Alerting (Prometheus)

```yaml
# prometheus/nqp-alerts.yaml

groups:
- name: nqp-api
  interval: 30s
  
  rules:
  - alert: HighErrorRate
    expr: |
      rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate on NASDAQ Predictor API"
      description: "Error rate is {{ $value | humanizePercentage }} over 5 minutes"
  
  - alert: RateLimitExceeded
    expr: |
      increase(rate_limit_exceeded_total[5m]) > 100
    for: 1m
    annotations:
      summary: "Rate limit exceeded frequently"
      description: "{{ $value }} rate limit violations in last 5 minutes"
  
  - alert: DatabaseConnectionPoolExhausted
    expr: |
      database_connections{state="idle"} == 0
    for: 2m
    annotations:
      summary: "Database connection pool exhausted"
      description: "No idle connections available"
  
  - alert: SlowResponseTime
    expr: |
      histogram_quantile(0.95, http_request_duration_seconds) > 2
    for: 10m
    annotations:
      summary: "Slow API response times"
      description: "P95 latency is {{ $value | humanizeDuration }}"
```

