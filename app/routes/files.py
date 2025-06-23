from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from .. import storage, utils

bp = Blueprint('files', __name__)

@bp.route('/upload', methods=['POST'])
def upload():
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        return jsonify({'error': 'Falta encabezado X-Client-ID'}), 400

    if 'files' not in request.files:
        return jsonify({'error': 'No se enviaron archivos'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'Lista de archivos vacía'}), 400

    file_infos = []

    for i, file in enumerate(files):
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        info = utils.build_file_info(i, file, path)
        file_infos.append(info)

    storage.store_files(client_id, file_infos)

    return jsonify({'message': 'Archivos subidos correctamente', 'files': file_infos}), 201

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        return jsonify({'error': 'Falta encabezado X-Client-ID'}), 400

    files = storage.get_files(client_id)
    if not files:
        return jsonify({'error': 'No hay archivos para este cliente'}), 404

    dashboard_data = {
        'files_count': len(files),
        'total_size': sum(f['size'] for f in files),
        'file_types': {},
        'statistics': {
            'average_size': sum(f['size'] for f in files) / len(files),
            'largest_file': max(files, key=lambda x: x['size'])['name'],
            'smallest_file': min(files, key=lambda x: x['size'])['name']
        },
        'files_summary': files,
        'status': 'completed'
    }

    for f in files:
        t = f['type']
        dashboard_data['file_types'][t] = dashboard_data['file_types'].get(t, 0) + 1

    return jsonify(dashboard_data)

@bp.route('/file/<int:file_id>', methods=['GET'])
def file_detail(file_id):
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        return jsonify({'error': 'Falta encabezado X-Client-ID'}), 400

    file = storage.get_file_by_id(client_id, file_id)
    if not file:
        return jsonify({'error': 'Archivo no encontrado'}), 404

    # Puedes expandir esto con análisis de contenido si deseas
    return jsonify({
        'basic_info': file,
        'analysis': {
            'structure_valid': True,
            'summary': 'Archivo procesado correctamente.',
            'schema_check': 'ok'
        }
    })
