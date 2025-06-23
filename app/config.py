import os

class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'temp_uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
