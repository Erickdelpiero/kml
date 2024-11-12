# Usa una imagen base de Python que incluye Linux
FROM python:3.11-slim

# Actualiza el sistema y instala dependencias del sistema necesarias para OpenCV y otros paquetes
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . /app

# Instala las dependencias de Python desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 5000 para la aplicación Flask
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
