from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from .. import storage, utils
from datetime import datetime
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import importlib.resources as pkg_resources

bp = Blueprint('files', __name__)

@bp.route('/ecoli/list', methods=['GET'])
def list_ecoli_files():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))
    if not os.path.exists(folder):
        return jsonify({'error': 'Carpeta Ecoli-files no encontrada'}), 404

    archivos = [f for f in os.listdir(folder) if f.endswith(('.gb', '.genbank', '.fasta', '.fa','fna'))]
    resultados = []

    for filename in archivos:
        path = os.path.join(folder, filename)
        ext = filename.split('.')[-1].lower()
        fmt = 'genbank' if 'gb' in ext else 'fasta'

        try:
            record = next(SeqIO.parse(path, fmt))
            resultados.append({
                'archivo': filename,
                'id': record.id,
                'descripcion': record.description,
                'longitud': len(record.seq),
                'formato': fmt
            })
        except Exception as e:
            resultados.append({
                'archivo': filename,
                'error': f'Error al leer: {str(e)}'
            })

    return jsonify({
        'total': len(resultados),
        'genomas': resultados
    })

bp = Blueprint('files', __name__)

@bp.route('/compare-to-ecoli', methods=['GET'])
def compare_to_ecoli():
    upload_folder = current_app.config['UPLOAD_FOLDER']
    ecoli_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))

    # Obtener el último archivo subido
    uploaded_files = sorted(
        [f for f in os.listdir(upload_folder) if f.endswith(('.fasta', '.fa', '.gb', '.genbank', '.fna'))],
        key=lambda x: os.path.getmtime(os.path.join(upload_folder, x))
    )

    if not uploaded_files:
        return jsonify({'error': 'No hay archivos subidos'}), 400

    last_uploaded = uploaded_files[-1]
    path_query = os.path.join(upload_folder, last_uploaded)

    # Parsear la secuencia del archivo subido
    def parse_sequence(path):
        ext = os.path.splitext(path)[1].lower()
        fmt = 'genbank' if 'gb' in ext else 'fasta'
        try:
            return next(SeqIO.parse(path, fmt))
        except Exception as e:
            return None

    query_seq = parse_sequence(path_query)
    if not query_seq:
        return jsonify({'error': 'No se pudo leer el archivo subido'}), 400

    # Comparar con todos los archivos en Ecoli-files
    comparaciones = []
    for ecoli_file in os.listdir(ecoli_folder):
        if ecoli_file.endswith(('.fasta', '.fa', '.gb', '.genbank', '.fna')):
            path_ecoli = os.path.join(ecoli_folder, ecoli_file)
            ecoli_seq = parse_sequence(path_ecoli)

            if ecoli_seq:
                # Comparación simple por identidad
                len_a = len(query_seq.seq)
                len_b = len(ecoli_seq.seq)
                min_len = min(len_a, len_b)
                matches = sum(1 for i in range(min_len) if query_seq.seq[i] == ecoli_seq.seq[i])
                identity = round((matches / min_len) * 100, 2)

                comparaciones.append({
                    'archivo_ecoli': ecoli_file,
                    'id_ecoli': ecoli_seq.id,
                    'longitud_query': len_a,
                    'longitud_ecoli': len_b,
                    'nucleotidos_iguales': matches,
                    'porcentaje_identidad': identity
                })
            else:
                comparaciones.append({
                    'archivo_ecoli': ecoli_file,
                    'error': 'No se pudo leer el archivo'
                })

    return jsonify({
        'query_file': last_uploaded,
        'comparaciones': comparaciones
    })


@bp.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(save_path)

    return jsonify({
        'message': 'Archivo subido exitosamente',
        'filename': filename,
        'path': save_path,
        'upload_time': datetime.now().isoformat()
    })

# @bp.route('/upload', methods=['POST'])
# def upload():
#     client_id = request.headers.get('X-Client-ID')
#     if not client_id:
#         return jsonify({'error': 'Falta encabezado X-Client-ID'}), 400

#     if 'files' not in request.files:
#         return jsonify({'error': 'No se enviaron archivos'}), 400

#     files = request.files.getlist('files')
#     if not files:
#         return jsonify({'error': 'Lista de archivos vacía'}), 400

#     file_infos = []

#     for i, file in enumerate(files):
#         filename = secure_filename(file.filename)
#         path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
#         file.save(path)
#         info = utils.build_file_info(i, file, path)
#         file_infos.append(info)

#     storage.store_files(client_id, file_infos)

#     return jsonify({'message': 'Archivos subidos correctamente', 'files': file_infos}), 201

# @bp.route('/dashboard', methods=['GET'])
# def dashboard():
#     client_id = request.headers.get('X-Client-ID')
#     if not client_id:
#         return jsonify({'error': 'Falta encabezado X-Client-ID'}), 400

#     files = storage.get_files(client_id)
#     if not files:
#         return jsonify({'error': 'No hay archivos para este cliente'}), 404

#     dashboard_data = {
#         'files_count': len(files),
#         'total_size': sum(f['size'] for f in files),
#         'file_types': {},
#         'statistics': {
#             'average_size': sum(f['size'] for f in files) / len(files),
#             'largest_file': max(files, key=lambda x: x['size'])['name'],
#             'smallest_file': min(files, key=lambda x: x['size'])['name']
#         },
#         'files_summary': files,
#         'status': 'completed'
#     }

#     for f in files:
#         t = f['type']
#         dashboard_data['file_types'][t] = dashboard_data['file_types'].get(t, 0) + 1

#     return jsonify(dashboard_data)

# @bp.route('/file/<int:file_id>', methods=['GET'])
# def file_detail(file_id):
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
