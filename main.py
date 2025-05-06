from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_session'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo por archivo
app.config['UPLOAD_FOLDER'] = 'temp_uploads'

# Crear carpeta temporal si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Almacenamiento en memoria para archivos
FILES_STORAGE = {}

@app.route('/')
def index():
    # Limpiar los archivos almacenados cuando se regresa a la página principal
    if 'files_session_id' in session:
        session_id = session['files_session_id']
        if session_id in FILES_STORAGE:
            del FILES_STORAGE[session_id]
        session.pop('files_session_id', None)
    
    # Crear una nueva sesión para los archivos
    session_id = str(uuid.uuid4())
    session['files_session_id'] = session_id
    FILES_STORAGE[session_id] = []
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files_session_id' not in session:
        return redirect(url_for('index'))
        
    session_id = session['files_session_id']
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'No se seleccionaron archivos'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No se seleccionaron archivos'}), 400
    
    file_data = []
    
    for i, file in enumerate(files):
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Información del archivo
            file_info = {
                'id': i + 1,
                'name': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': file.content_type if hasattr(file, 'content_type') else 'unknown'
            }
            
            # Aquí añadiríamos lógica para procesar el archivo según el tipo
            # Por ahora solo guardamos la información básica
            
            file_data.append(file_info)
    
    # Guardar información de archivos en la memoria
    FILES_STORAGE[session_id] = file_data
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'files_session_id' not in session or session['files_session_id'] not in FILES_STORAGE:
        return redirect(url_for('index'))
    
    session_id = session['files_session_id']
    files = FILES_STORAGE[session_id]
    
    if not files:
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', files=files)

@app.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint para obtener datos del dashboard en formato JSON"""
    if 'files_session_id' not in session or session['files_session_id'] not in FILES_STORAGE:
        return jsonify({'error': 'No hay archivos en sesión'}), 404
    
    session_id = session['files_session_id']
    files = FILES_STORAGE[session_id]
    
    # Datos de ejemplo para el dashboard
    dashboard_data = {
        'files_count': len(files),
        'total_size': sum(file['size'] for file in files),
        'file_types': {},
        'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'files_summary': files,
        # Datos de ejemplo adicionales
        'statistics': {
            'average_size': sum(file['size'] for file in files) / len(files) if files else 0,
            'largest_file': max(files, key=lambda x: x['size'])['name'] if files else None,
            'smallest_file': min(files, key=lambda x: x['size'])['name'] if files else None,
        },
        'processing_status': 'completed',
        'system_info': {
            'version': '1.0.0',
            'api_status': 'online',
            'memory_usage': '45%',
            'cpu_usage': '32%'
        }
    }
    
    # Contabilizar tipos de archivos
    for file in files:
        file_type = file['type']
        if file_type in dashboard_data['file_types']:
            dashboard_data['file_types'][file_type] += 1
        else:
            dashboard_data['file_types'][file_type] = 1
    
    return jsonify(dashboard_data)

@app.route('/detail/<int:file_id>')
def file_detail(file_id):
    if 'files_session_id' not in session or session['files_session_id'] not in FILES_STORAGE:
        return redirect(url_for('index'))
    
    session_id = session['files_session_id']
    files = FILES_STORAGE[session_id]
    
    # Encontrar el archivo con el ID solicitado
    file_info = None
    for file in files:
        if file['id'] == file_id:
            file_info = file
            break
    
    if not file_info:
        return redirect(url_for('dashboard'))
    
    return render_template('detail.html', file=file_info)

@app.route('/api/file-detail/<int:file_id>')
def file_detail_data(file_id):
    """API endpoint para obtener datos detallados de un archivo en formato JSON"""
    if 'files_session_id' not in session or session['files_session_id'] not in FILES_STORAGE:
        return jsonify({'error': 'No hay archivos en sesión'}), 404
    
    session_id = session['files_session_id']
    files = FILES_STORAGE[session_id]
    
    # Encontrar el archivo con el ID solicitado
    file_info = None
    for file in files:
        if file['id'] == file_id:
            file_info = file
            break
    
    if not file_info:
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    # Aquí se podría agregar lógica para analizar el archivo y obtener más información
    # Por ahora retornamos información básica y algunos datos ficticios
    
    detail_data = {
        'basic_info': file_info,
        'extended_info': {
            'creation_date': datetime.now().strftime('%Y-%m-%d'),
            'last_modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'permissions': 'read/write',
            'owner': 'current_user',
            'checksum': 'md5:' + str(hash(file_info['name']))
        },
        'analysis_results': {
            'structure_valid': True,
            'content_summary': 'Este archivo contiene datos de ejemplo para la demostración.',
            'row_count': 1250,
            'column_count': 15,
            'data_types': ['string', 'numeric', 'date'],
            'schema_validation': 'passed'
        },
        'processing_history': [
            {
                'action': 'upload',
                'timestamp': file_info['upload_time'],
                'status': 'completed'
            },
            {
                'action': 'validation',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            },
            {
                'action': 'analysis',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            }
        ],
        'visualizations': {
            'data_distribution': {
                'type': 'pie_chart',
                'data': {
                    'labels': ['Categoría A', 'Categoría B', 'Categoría C'],
                    'values': [45, 30, 25]
                }
            },
            'time_series': {
                'type': 'line_chart',
                'data': {
                    'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
                    'values': [12, 19, 15, 22, 30]
                }
            }
        }
    }
    
    return jsonify(detail_data)

if __name__ == '__main__':
    app.run(debug=True)