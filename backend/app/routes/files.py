"""
File Routes
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import db
from app.models.user import User
from app.models.file import File
from app.utils.decorators import check_file_ownership
from app.ai.document_processor import DocumentProcessor

files_bp = Blueprint('files', __name__)
document_processor = DocumentProcessor()


@files_bp.route('', methods=['GET'])
@jwt_required()
def get_files():
    """Get user's files"""
    current_user_id = get_jwt_identity()
    
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Build query
    query = File.query.filter_by(user_id=current_user_id)\
                     .order_by(File.created_at.desc())
    
    # Paginate
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    files = [file.to_dict() for file in pagination.items]
    
    return jsonify({
        'files': files,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if not File.is_allowed_file(file.filename):
        return jsonify({
            'message': 'File type not allowed',
            'allowed_types': File.get_allowed_extensions()
        }), 400
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    unique_filename = File.generate_unique_filename(original_filename)
    
    # Create upload directory if it doesn't exist
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    user_folder = os.path.join(upload_folder, str(current_user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(user_folder, unique_filename)
    file.save(file_path)
    
    # Validate file
    validation_result = document_processor.validate_file(file_path, original_filename)
    
    if not validation_result['is_valid']:
        # Remove invalid file
        try:
            os.remove(file_path)
        except:
            pass
        return jsonify({'message': validation_result['error']}), 400
    
    # Create file record
    file_record = File(
        filename=unique_filename,
        original_filename=original_filename,
        file_path=os.path.join(str(current_user_id), unique_filename),
        file_size=validation_result['file_info']['size'],
        mime_type=validation_result['file_info'].get('mime_type'),
        file_extension=validation_result['file_info']['extension'],
        content_hash=validation_result['file_info']['hash'],
        user_id=current_user_id
    )
    
    db.session.add(file_record)
    db.session.commit()
    
    # Start text extraction in background (would use Celery in production)
    try:
        extraction_result = document_processor.extract_text(
            file_path, 
            file_record.file_extension
        )
        
        if extraction_result['success']:
            file_record.extracted_text = extraction_result['text']
            file_record.page_count = extraction_result['metadata'].get('page_count')
            file_record.mark_as_processed(success=True)
            file_record.calculate_word_count()
        else:
            file_record.mark_as_processed(success=False, error=extraction_result['error'])
    
    except Exception as e:
        file_record.mark_as_processed(success=False, error=str(e))
    
    return jsonify({
        'message': 'File uploaded successfully',
        'file': file_record.to_dict()
    }), 201


@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
@check_file_ownership
def get_file(file_id):
    """Get file details"""
    file = File.query.get(file_id)
    
    if not file:
        return jsonify({'message': 'File not found'}), 404
    
    return jsonify({
        'file': file.to_dict(include_content=True)
    }), 200


@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
@check_file_ownership
def download_file(file_id):
    """Download a file"""
    file = File.query.get(file_id)
    
    if not file:
        return jsonify({'message': 'File not found'}), 404
    
    file_path = file.get_absolute_path()
    
    if not file.exists_on_disk():
        return jsonify({'message': 'File not found on disk'}), 404
    
    # Increment download count
    file.increment_download_count()
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.original_filename
    )


@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
@check_file_ownership
def delete_file(file_id):
    """Delete a file"""
    file = File.query.get(file_id)
    
    if not file:
        return jsonify({'message': 'File not found'}), 404
    
    # Delete file from disk
    file.delete_from_disk()
    
    # Delete from database
    db.session.delete(file)
    db.session.commit()
    
    return jsonify({'message': 'File deleted successfully'}), 200


@files_bp.route('/<int:file_id>/extract-text', methods=['POST'])
@jwt_required()
@check_file_ownership
def extract_text(file_id):
    """Re-extract text from a file"""
    file = File.query.get(file_id)
    
    if not file:
        return jsonify({'message': 'File not found'}), 404
    
    if not file.can_extract_text():
        return jsonify({'message': 'Text extraction not supported for this file type'}), 400
    
    file_path = file.get_absolute_path()
    
    if not file.exists_on_disk():
        return jsonify({'message': 'File not found on disk'}), 404
    
    try:
        extraction_result = document_processor.extract_text(
            file_path, 
            file.file_extension
        )
        
        if extraction_result['success']:
            file.extracted_text = extraction_result['text']
            file.page_count = extraction_result['metadata'].get('page_count')
            file.mark_as_processed(success=True)
            file.calculate_word_count()
            
            return jsonify({
                'message': 'Text extracted successfully',
                'file': file.to_dict(include_content=True)
            }), 200
        else:
            file.mark_as_processed(success=False, error=extraction_result['error'])
            return jsonify({
                'message': 'Text extraction failed',
                'error': extraction_result['error']
            }), 400
    
    except Exception as e:
        file.mark_as_processed(success=False, error=str(e))
        return jsonify({
            'message': 'Text extraction failed',
            'error': str(e)
        }), 500
