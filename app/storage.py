FILES_STORAGE = {}  # {client_id: [file_info, ...]}

def store_files(client_id, files):
    FILES_STORAGE[client_id] = files

def get_files(client_id):
    return FILES_STORAGE.get(client_id, [])

def get_file_by_id(client_id, file_id):
    files = get_files(client_id)
    return next((f for f in files if f['id'] == file_id), None)

def clear_files(client_id):
    if client_id in FILES_STORAGE:
        del FILES_STORAGE[client_id]
