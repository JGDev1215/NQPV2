"""
Swagger/OpenAPI Integration for Flask API

Provides Swagger UI and OpenAPI specification endpoints for the NASDAQ Predictor API.
Allows interactive API documentation and testing directly in the browser.
"""

import os
import yaml
import logging
from flask import Blueprint, render_template_string, jsonify, send_from_directory, current_app

logger = logging.getLogger(__name__)

# Create blueprint for Swagger endpoints
swagger_bp = Blueprint('swagger', __name__, url_prefix='/api-docs')


def load_openapi_spec():
    """Load the OpenAPI specification from YAML file."""
    try:
        # Get the directory where this file is located
        spec_dir = os.path.dirname(os.path.abspath(__file__))
        spec_path = os.path.join(spec_dir, 'openapi.yaml')

        if not os.path.exists(spec_path):
            logger.warning(f"OpenAPI spec not found at {spec_path}")
            return {}

        with open(spec_path, 'r') as f:
            spec = yaml.safe_load(f)

        return spec

    except Exception as e:
        logger.error(f"Error loading OpenAPI spec: {e}")
        return {}


# Cache the spec after first load
_openapi_spec = None


def get_openapi_spec():
    """Get the OpenAPI specification (cached)."""
    global _openapi_spec

    if _openapi_spec is None:
        _openapi_spec = load_openapi_spec()

    return _openapi_spec


@swagger_bp.route('/openapi.json')
def openapi_json():
    """
    OpenAPI specification endpoint.

    Returns the complete OpenAPI specification as JSON.
    This endpoint is used by Swagger UI and other API documentation tools.
    """
    spec = get_openapi_spec()

    if not spec:
        logger.warning("OpenAPI spec is empty")
        return jsonify({
            'error': 'OpenAPI specification not available',
            'message': 'The OpenAPI spec file may not be properly configured'
        }), 500

    return jsonify(spec), 200


@swagger_bp.route('/openapi.yaml')
def openapi_yaml():
    """
    OpenAPI specification endpoint (YAML format).

    Returns the complete OpenAPI specification as YAML.
    """
    spec_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(spec_dir, 'openapi.yaml')

    if not os.path.exists(spec_path):
        return jsonify({'error': 'OpenAPI spec not found'}), 404

    try:
        with open(spec_path, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'application/yaml'}
    except Exception as e:
        logger.error(f"Error serving YAML spec: {e}")
        return jsonify({'error': str(e)}), 500


@swagger_bp.route('/')
def swagger_ui():
    """
    Swagger UI interface.

    Provides an interactive API documentation interface where users can:
    - View all available endpoints
    - See request/response examples
    - Test API calls directly from the browser
    """
    # HTML template for Swagger UI
    swagger_ui_html = '''
    <!DOCTYPE html>
    <html>
      <head>
        <title>NASDAQ Predictor API - Swagger UI</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.js"></script>
        <style>
          html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
          *, *:before, *:after { box-sizing: inherit; }
          body { margin:0; padding:0; }
        </style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script>
          const ui = SwaggerUIBundle({
            url: "/api-docs/openapi.json",
            dom_id: '#swagger-ui',
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            plugins: [
              SwaggerUIBundle.plugins.DownloadUrl
            ]
          });
        </script>
      </body>
    </html>
    '''

    return render_template_string(swagger_ui_html), 200


@swagger_bp.route('/redoc')
def redoc_ui():
    """
    ReDoc UI interface (alternative API documentation).

    Provides a clean, responsive alternative documentation interface.
    """
    redoc_html = '''
    <!DOCTYPE html>
    <html>
      <head>
        <title>NASDAQ Predictor API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
          body {
            margin: 0;
            padding: 0;
          }
        </style>
      </head>
      <body>
        <redoc spec-url="/api-docs/openapi.json"></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
      </body>
    </html>
    '''

    return render_template_string(redoc_html), 200


@swagger_bp.route('/elements')
def elements_ui():
    """
    Elements UI interface (another alternative API documentation).

    Provides a different style of API documentation interface.
    """
    elements_html = '''
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NASDAQ Predictor API - Elements</title>
        <style>
          html {
            font-family: sans-serif;
          }
          body {
            margin: 0;
            padding: 0;
          }
        </style>
      </head>
      <body>
        <elements-api spec-url="/api-docs/openapi.json" router="hash" layout="sidebar"></elements-api>
        <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
      </body>
    </html>
    '''

    return render_template_string(elements_html), 200


@swagger_bp.route('/info')
def api_info():
    """
    API documentation information endpoint.

    Provides metadata about the API and available documentation formats.
    """
    spec = get_openapi_spec()

    return jsonify({
        'success': True,
        'message': 'API Documentation Endpoints',
        'data': {
            'api_version': spec.get('info', {}).get('version', 'unknown'),
            'title': spec.get('info', {}).get('title', 'NASDAQ Predictor API'),
            'description': spec.get('info', {}).get('description', ''),
            'endpoints': {
                'openapi_json': '/api-docs/openapi.json',
                'openapi_yaml': '/api-docs/openapi.yaml',
                'swagger_ui': '/api-docs/',
                'redoc': '/api-docs/redoc',
                'elements': '/api-docs/elements',
                'info': '/api-docs/info'
            }
        },
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }), 200


def initialize_swagger(app):
    """
    Initialize Swagger/OpenAPI documentation for the Flask app.

    Args:
        app (Flask): The Flask application instance

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Register the swagger blueprint
        app.register_blueprint(swagger_bp)

        # Log initialization
        logger.info("Swagger/OpenAPI documentation initialized")
        logger.info("Available at:")
        logger.info("  - Swagger UI: http://localhost:5000/api-docs/")
        logger.info("  - ReDoc: http://localhost:5000/api-docs/redoc")
        logger.info("  - Elements: http://localhost:5000/api-docs/elements")
        logger.info("  - OpenAPI JSON: http://localhost:5000/api-docs/openapi.json")
        logger.info("  - OpenAPI YAML: http://localhost:5000/api-docs/openapi.yaml")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize Swagger documentation: {e}")
        return False


__all__ = ['swagger_bp', 'initialize_swagger', 'get_openapi_spec']
