"""
CORS and security header configuration for different environments.

Provides environment-specific CORS policies and security headers
to protect the application while enabling legitimate cross-origin requests.

Environments:
- development: Permissive CORS for local testing
- staging: Moderate CORS restrictions for staging environment
- production: Strict CORS restrictions for production
"""

import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CORSConfig:
    """CORS (Cross-Origin Resource Sharing) configuration by environment."""

    # Development - permissive for local development
    DEVELOPMENT = {
        'origins': [
            'http://localhost:3000',
            'http://localhost:5000',
            'http://localhost:8000',
            'http://localhost:8080',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5000',
            'http://127.0.0.1:8000',
            'http://127.0.0.1:8080'
        ],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        'allow_headers': [
            'Content-Type',
            'Authorization',
            'X-API-Key',
            'X-Requested-With',
            'Accept',
            'Origin'
        ],
        'expose_headers': [
            'X-Total-Count',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset',
            'X-RateLimit-Limit',
            'Content-Type'
        ],
        'supports_credentials': True,
        'max_age': 3600,
        'automatic_options': True
    }

    # Staging - moderate restrictions
    STAGING = {
        'origins': [
            'https://staging.nasdaq-predictor.com',
            'https://dashboard-staging.nasdaq-predictor.com',
            'https://app-staging.nasdaq-predictor.com'
        ],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': [
            'Content-Type',
            'Authorization',
            'X-API-Key',
            'Accept'
        ],
        'expose_headers': [
            'X-Total-Count',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset',
            'Content-Type'
        ],
        'supports_credentials': True,
        'max_age': 7200,
        'automatic_options': True
    }

    # Production - strict restrictions
    PRODUCTION = {
        'origins': [
            'https://nasdaq-predictor.com',
            'https://www.nasdaq-predictor.com',
            'https://dashboard.nasdaq-predictor.com',
            'https://api.nasdaq-predictor.com'
        ],
        'methods': ['GET', 'POST', 'OPTIONS'],
        'allow_headers': [
            'Content-Type',
            'Authorization',
            'X-API-Key'
        ],
        'expose_headers': [
            'X-Total-Count',
            'X-RateLimit-Remaining',
            'Content-Type'
        ],
        'supports_credentials': False,  # Cookies not allowed in production
        'max_age': 86400,  # 24 hours
        'automatic_options': True
    }

    @staticmethod
    def get_config(env: str = None) -> Dict:
        """Get CORS config for current environment.

        Args:
            env: Environment name. If None, uses FLASK_ENV environment variable.

        Returns:
            CORS configuration dictionary
        """
        if env is None:
            env = os.getenv('FLASK_ENV', 'development').lower()

        if env == 'production':
            config = CORSConfig.PRODUCTION
        elif env == 'staging':
            config = CORSConfig.STAGING
        else:
            config = CORSConfig.DEVELOPMENT

        logger.info(f"CORS Configuration loaded for environment: {env}")
        logger.info(f"  Allowed origins: {len(config['origins'])}")
        logger.info(f"  Allowed methods: {', '.join(config['methods'])}")

        return config


class SecurityHeadersConfig:
    """Security headers configuration for all HTTP responses."""

    # Standard security headers recommended by OWASP
    HEADERS = {
        # HSTS (HTTP Strict Transport Security)
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',

        # Clickjacking protection
        'X-Frame-Options': 'DENY',

        # XSS protection
        'X-XSS-Protection': '1; mode=block',

        # Content Security Policy - restrict resource loading
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),

        # Referrer Policy
        'Referrer-Policy': 'strict-origin-when-cross-origin',

        # Permissions Policy (formerly Feature Policy)
        'Permissions-Policy': (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        ),

        # Cross-Origin Opener Policy
        'Cross-Origin-Opener-Policy': 'same-origin',

        # Cross-Origin Embedder Policy
        'Cross-Origin-Embedder-Policy': 'require-corp'
    }

    # Headers specific to API endpoints (stricter)
    API_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'none'; connect-src 'self'",
        'Referrer-Policy': 'no-referrer',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }

    @staticmethod
    def get_headers(is_api: bool = False) -> Dict[str, str]:
        """Get security headers for response.

        Args:
            is_api: Whether this is an API endpoint (stricter headers)

        Returns:
            Dictionary of security headers
        """
        if is_api:
            return SecurityHeadersConfig.API_HEADERS.copy()
        return SecurityHeadersConfig.HEADERS.copy()


class SecurityConfig:
    """Combined security configuration."""

    @staticmethod
    def init_security(app):
        """Initialize security features on Flask app.

        Args:
            app: Flask application instance
        """
        env = os.getenv('FLASK_ENV', 'development').lower()

        # Initialize CORS
        try:
            from flask_cors import CORS

            cors_config = CORSConfig.get_config(env)
            CORS(
                app,
                resources={r"/api/*": cors_config},
                origins=cors_config['origins'],
                methods=cors_config['methods'],
                allow_headers=cors_config['allow_headers'],
                expose_headers=cors_config['expose_headers'],
                supports_credentials=cors_config['supports_credentials'],
                max_age=cors_config['max_age']
            )
            logger.info("✓ CORS initialized successfully")
        except ImportError:
            logger.warning("⚠ flask-cors not installed - CORS disabled")
        except Exception as e:
            logger.error(f"✗ Failed to initialize CORS: {e}")

        # Add security headers to all responses
        @app.after_request
        def add_security_headers(response):
            """Add security headers to every response."""
            headers = SecurityHeadersConfig.get_headers(is_api=False)

            for header, value in headers.items():
                response.headers[header] = value

            # Add additional headers
            response.headers['Server'] = 'NQP/1.0'  # Custom server header
            response.headers['X-Content-Security-Policy'] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'"
            )

            return response

        logger.info("✓ Security headers initialized successfully")

    @staticmethod
    def get_security_info() -> Dict:
        """Get security configuration information.

        Returns:
            Dictionary with security settings
        """
        env = os.getenv('FLASK_ENV', 'development').lower()

        return {
            'environment': env,
            'cors': CORSConfig.get_config(env),
            'security_headers_count': len(SecurityHeadersConfig.HEADERS),
            'api_headers_count': len(SecurityHeadersConfig.API_HEADERS)
        }


def init_cors_security(app):
    """Convenience function to initialize CORS and security for Flask app.

    Args:
        app: Flask application instance

    Example:
        from flask import Flask
        from nasdaq_predictor.config.cors_security_config import init_cors_security

        app = Flask(__name__)
        init_cors_security(app)
    """
    SecurityConfig.init_security(app)
