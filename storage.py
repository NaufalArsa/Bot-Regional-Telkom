"""
Storage operations module for Supabase file upload.
Handles file upload to Supabase storage bucket.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET

logger = logging.getLogger(__name__)

class SupabaseStorageManager:
    """Manages Supabase storage operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        self.bucket_name = SUPABASE_BUCKET
        self.client = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
    
    def upload_file(self, file_path: str) -> str:
        """Upload file to Supabase storage."""
        try:
            if not self.client:
                return "Foto tersimpan (tanpa upload)"
            
            # Generate unique filename
            file_extension = os.path.splitext(file_path)[1]
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
            
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase
            response = self.client.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=file_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            if response:
                # Get public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(unique_filename)
                return public_url
            
            return "Foto tersimpan (gagal upload)"
            
        except Exception as e:
            logger.error(f"Supabase upload error: {e}")
            return "Foto tersimpan (error sistem)"

# Global instance
storage_manager = SupabaseStorageManager()

def upload_to_supabase(file_path: str) -> str:
    """Upload file to Supabase storage."""
    return storage_manager.upload_file(file_path)