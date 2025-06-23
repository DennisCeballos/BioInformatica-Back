from datetime import datetime
import os

def build_file_info(i, file, path):
    return {
        'id': i + 1,
        'name': file.filename,
        'path': path,
        'size': os.path.getsize(path),
        'upload_time': datetime.now().isoformat(),
        'type': file.content_type or 'unknown'
    }
