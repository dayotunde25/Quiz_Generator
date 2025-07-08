"""
File Model
"""
from datetime import datetime, timezone
from app import db
import os


class File(db.Model):
    """File model for tracking uploaded documents"""
    
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100))
    file_extension = db.Column(db.String(10))
    
    # Content extraction
    extracted_text = db.Column(db.Text)
    extraction_status = db.Column(db.String(20), default='pending')  # pending, success, failed
    extraction_error = db.Column(db.Text)
    
    # File metadata
    page_count = db.Column(db.Integer)  # For PDFs
    word_count = db.Column(db.Integer)
    character_count = db.Column(db.Integer)
    
    # Processing status
    is_processed = db.Column(db.Boolean, default=False)
    processing_started_at = db.Column(db.DateTime(timezone=True))
    processing_completed_at = db.Column(db.DateTime(timezone=True))
    
    # Security and validation
    is_safe = db.Column(db.Boolean, default=True)
    virus_scan_status = db.Column(db.String(20), default='pending')  # pending, clean, infected
    content_hash = db.Column(db.String(64))  # SHA-256 hash for deduplication
    
    # Usage tracking
    download_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime(timezone=True))
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def file_size_human(self):
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_absolute_path(self):
        """Get absolute file path"""
        from flask import current_app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(upload_folder, self.file_path)
    
    def exists_on_disk(self):
        """Check if file exists on disk"""
        return os.path.exists(self.get_absolute_path())
    
    def delete_from_disk(self):
        """Delete file from disk"""
        try:
            file_path = self.get_absolute_path()
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file {self.file_path}: {e}")
        return False
    
    def mark_as_processed(self, success=True, error=None):
        """Mark file as processed"""
        self.is_processed = success
        self.processing_completed_at = datetime.now(timezone.utc)
        
        if success:
            self.extraction_status = 'success'
        else:
            self.extraction_status = 'failed'
            self.extraction_error = error
        
        db.session.commit()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        db.session.commit()
    
    def calculate_word_count(self):
        """Calculate word count from extracted text"""
        if self.extracted_text:
            words = self.extracted_text.split()
            self.word_count = len(words)
            self.character_count = len(self.extracted_text)
            db.session.commit()
    
    def is_text_file(self):
        """Check if file is a text file"""
        return self.file_extension.lower() in ['txt', 'md', 'rtf']
    
    def is_pdf_file(self):
        """Check if file is a PDF"""
        return self.file_extension.lower() == 'pdf'
    
    def is_word_file(self):
        """Check if file is a Word document"""
        return self.file_extension.lower() in ['doc', 'docx']
    
    def can_extract_text(self):
        """Check if text can be extracted from this file type"""
        return self.file_extension.lower() in ['txt', 'pdf', 'docx', 'doc', 'md', 'rtf']
    
    def to_dict(self, include_content=False):
        """Convert file to dictionary"""
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_human': self.file_size_human,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'extraction_status': self.extraction_status,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'is_processed': self.is_processed,
            'is_safe': self.is_safe,
            'virus_scan_status': self.virus_scan_status,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'user_id': self.user_id,
            'can_extract_text': self.can_extract_text(),
            'exists_on_disk': self.exists_on_disk()
        }
        
        if include_content:
            data['extracted_text'] = self.extracted_text
            data['extraction_error'] = self.extraction_error
        
        return data
    
    @staticmethod
    def get_allowed_extensions():
        """Get list of allowed file extensions"""
        return ['txt', 'pdf', 'docx', 'doc', 'md', 'rtf']
    
    @staticmethod
    def is_allowed_file(filename):
        """Check if filename has allowed extension"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in File.get_allowed_extensions()
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generate a unique filename to prevent conflicts"""
        import uuid
        import os
        
        name, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())[:8]
        return f"{name}_{unique_id}{ext}"
