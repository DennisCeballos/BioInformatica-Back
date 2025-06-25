from flask import Blueprint, request, jsonify, current_app , send_file
from werkzeug.utils import secure_filename
import os
from .. import storage, utils
from datetime import datetime
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import importlib.resources as pkg_resources
import pandas as pd
import json

bp = Blueprint('files', __name__)

@bp.route('/ecoli/list', methods=['GET'])
def list_ecoli_files():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))

    if not os.path.exists(folder):
        return jsonify({'error': 'Carpeta Ecoli-files no encontrada'}), 404

    archivos = [f for f in os.listdir(folder) if f.endswith(('.gb', '.genbank', '.fasta', '.fa', 'fna'))]
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

    history_path = os.path.join(folder, 'ecoli_history.json')
    with open(history_path, 'w') as f:
        json.dump(resultados, f, indent=2)

    return jsonify({
        'total': len(resultados),
        'genomas': resultados
    })

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

# Endpoint para obtener solo estadísticas generales
@bp.route('/ecoli/stats', methods=['GET'])
def ecoli_stats():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))
    archivos = [f for f in os.listdir(folder) if f.endswith(('.gb', '.genbank', '.fasta', '.fa', 'fna'))]
    longitudes = []

    for f in archivos:
        try:
            fmt = 'genbank' if 'gb' in f.lower() else 'fasta'
            record = next(SeqIO.parse(os.path.join(folder, f), fmt))
            longitudes.append(len(record.seq))
        except:
            continue

    if not longitudes:
        return jsonify({'error': 'No se pudieron leer los archivos'}), 400

    return jsonify({
        'total_archivos': len(longitudes),
        'promedio_longitud': round(sum(longitudes)/len(longitudes), 2),
        'longitud_maxima': max(longitudes),
        'longitud_minima': min(longitudes)
    })

# Endpoint para buscar un gen específico dentro de los genomas
@bp.route('/ecoli/search', methods=['GET'])
def search_gene():
    query = request.args.get('q', '').lower()
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))

    if not query:
        return jsonify({'error': 'Parámetro de búsqueda "q" requerido'}), 400

    resultados = []
    for f in os.listdir(folder):
        if f.endswith(('.gb', '.genbank', '.fasta', '.fa', 'fna')):
            fmt = 'genbank' if 'gb' in f.lower() else 'fasta'
            try:
                record = next(SeqIO.parse(os.path.join(folder, f), fmt))
                if query in record.id.lower() or query in record.description.lower():
                    resultados.append({
                        'archivo': f,
                        'id': record.id,
                        'descripcion': record.description,
                        'longitud': len(record.seq)
                    })
            except:
                continue

    return jsonify({'resultados': resultados, 'total': len(resultados)})

# Endpoint para obtener regiones o fragmentos del genoma
@bp.route('/ecoli/fragment', methods=['GET'])
def get_fragment():
    filename = request.args.get('file')
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', start + 1000))

    if not filename:
        return jsonify({'error': 'Archivo requerido'}), 400

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files', filename))
    if not os.path.exists(path):
        return jsonify({'error': 'Archivo no encontrado'}), 404

    fmt = 'genbank' if 'gb' in filename.lower() else 'fasta'
    try:
        record = next(SeqIO.parse(path, fmt))
        fragment = str(record.seq[start:end])
        return jsonify({
            'archivo': filename,
            'desde': start,
            'hasta': end,
            'fragmento': fragment
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
# Descargar historial de comparaciones como CSV
@bp.route('/ecoli/history/csv', methods=['GET'])
def download_ecoli_history_csv():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))
    json_path = os.path.join(folder, 'ecoli_history.json')

    if not os.path.exists(json_path):
        return jsonify({'error': 'No hay historial disponible'}), 404

    df = pd.read_json(json_path)
    csv_path = os.path.join(folder, 'ecoli_history.csv')
    df.to_csv(csv_path, index=False)

    return send_file(csv_path, as_attachment=True)
# # Estadísticas avanzadas con pandas
# @bp.route('/ecoli/stats-pandas', methods=['GET'])
# def ecoli_stats_pandas():
#     folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Ecoli-files'))
#     data = []

#     for f in os.listdir(folder):
#         if f.endswith(('.gb', '.genbank', '.fasta', '.fa', 'fna')):
#             fmt = 'genbank' if 'gb' in f.lower() else 'fasta'
#             try:
#                 record = next(SeqIO.parse(os.path.join(folder, f), fmt))
#                 data.append({
#                     'archivo': f,
#                     'longitud': len(record.seq),
#                     'formato': fmt
#                 })
#             except:
#                 continue

#     df = pd.DataFrame(data)

#     # Convierte valores a tipos nativos de Python
#     resumen = {
#         'total': int(df.shape[0]),
#         'promedio': float(df['longitud'].mean()) if not df.empty else 0,
#         'minimo': int(df['longitud'].min()) if not df.empty else 0,
#         'maximo': int(df['longitud'].max()) if not df.empty else 0,
#         'por_formato': {k: int(v) for k, v in df['formato'].value_counts().to_dict().items()}
#     }

#     return jsonify(resumen)
