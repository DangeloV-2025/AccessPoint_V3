from supabase import create_client, Client
from flask import current_app
import os
from typing import Optional

def upload_image_to_supabase(file, filename) -> Optional[str]:
    """Upload an image to Supabase storage and return the public URL"""
    try:
        # Get credentials from environment directly instead of through Flask config
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')  # Important: Use the anon/public key for client-side ops
        
        if not supabase_url or not supabase_key:
            current_app.logger.error("Supabase credentials not properly configured")
            raise ValueError("Missing Supabase credentials")

        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read file content
        file_content = file.read()
        
        try:
            # Upload the file to the 'blog-images' bucket
            result = supabase.storage \
                .from_('blog-images') \
                .upload(
                    path=filename,
                    file=file_content,
                    file_options={"content-type": file.content_type}
                )
            
            # Generate the public URL
            public_url = supabase.storage \
                .from_('blog-images') \
                .get_public_url(filename)
            
            return public_url

        except Exception as e:
            current_app.logger.error(f"Supabase storage error: {str(e)}")
            raise

    except Exception as e:
        current_app.logger.error(f"Error in upload_image_to_supabase: {str(e)}")
        return None 