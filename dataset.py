import os
import shutil

# Ruta base de tus carpetas
BASE_DIR = r"C:\Users\HP\Downloads\ncbi_dataset\ncbi_dataset\data"  # <-- Ajusta si es necesario
DEST_DIR = os.path.join(BASE_DIR, "fna_colectados")

# Crear carpeta de destino si no existe
os.makedirs(DEST_DIR, exist_ok=True)

# Recorrer subcarpetas y copiar archivos .fna
for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".fna"):
            src_path = os.path.join(root, file)
            dest_path = os.path.join(DEST_DIR, file)
            shutil.copy2(src_path, dest_path)
            print(f"Copiado: {file}")

print(f"\n✔ Todos los archivos .fna se copiaron a: {DEST_DIR}")
