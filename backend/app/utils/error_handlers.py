"""
Error Handlers
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError
import logging


def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors"""
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': error.messages
        }), 400
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Handle database errors"""
        app.logger.error(f'Database error: {str(error)}')
        return jsonify({
            'error': 'Database Error',
            'message': 'A database error occurred'
        }), 500
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle rate limit errors"""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(413)
    def handle_file_too_large(error):
        """Handle file too large errors"""
        return jsonify({
            'error': 'File Too Large',
            'message': 'The uploaded file is too large'
        }), 413
    
    @app.errorhandler(415)
    def handle_unsupported_media_type(error):
        """Handle unsupported media type errors"""
        return jsonify({
            'error': 'Unsupported Media Type',
            'message': 'The file type is not supported'
        }), 415
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors"""
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle other HTTP exceptions"""
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle any other exceptions"""
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
