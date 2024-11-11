import cv2
import pytesseract
import re
from collections import Counter
from pyproj import Proj, transform
import simplekml
import os

# Configuración de la ruta de Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Función para cargar y preprocesar la imagen para OCR
def load_and_preprocess_image(filepath):
    imagen = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    _, imagen_binaria = cv2.threshold(imagen, 180, 255, cv2.THRESH_BINARY)
    imagen_agrandada = cv2.resize(imagen_binaria, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    imagen_denoised = cv2.medianBlur(imagen_agrandada, 3)
    return imagen_denoised

# Función para realizar OCR y extraer texto de la imagen
def extract_text_from_image(image):
    texto_extraido = pytesseract.image_to_string(image, config="--psm 3")
    print("Texto Extraído (Pre-Limpieza):")
    print(texto_extraido)
    return texto_extraido

# Función para limpiar el texto extraído y obtener coordenadas
def process_text_for_coordinates(texto_extraido):
    lineas = texto_extraido.splitlines()
    coordenadas = []
    for linea in lineas:
        linea = linea.strip('| ').strip()
        if not linea:
            continue  # Verifica si la línea está vacía
        #linea = linea.replace(',', '.')
        # Modificar la expresión regular para detectar números enteros y decimales separados por espacios o puntos
        match = re.findall(r"[-+]?\d*\.\d+|\d+", linea)
        
        # Verifica que obtengamos exactamente dos componentes por línea para considerarla válida
        if len(match) == 2:
            coordenadas.append(match)
    
    # Calcular el número más común de dígitos en cada columna
    col1_digit_counts = [len(coord[0].split('.')[0].replace('-', '')) for coord in coordenadas]
    col2_digit_counts = [len(coord[1].split('.')[0].replace('-', '')) for coord in coordenadas]
    print('Sospecha:')
    print('col1_digit_counts')
    print('col2_digit_counts')
    col1_common_digit_count = Counter(col1_digit_counts).most_common(1)[0][0]
    col2_common_digit_count = Counter(col2_digit_counts).most_common(1)[0][0]
    coordenadas_corregidas = []
    
    for coord in coordenadas:
        corrected_coord = []
        for i, (parte_entera, common_digit_count) in enumerate(zip([coord[0], coord[1]], [col1_common_digit_count, col2_common_digit_count])):
            partes = parte_entera.split('.')
            parte_entera = partes[0]
            parte_decimal = partes[1] if len(partes) > 1 else ""
            signo = '-' if parte_entera.startswith('-') else ''
            parte_entera = parte_entera.lstrip('-')
            
            # Ajustar la longitud de la parte entera según el número más común de dígitos
            if len(parte_entera) < common_digit_count:
                parte_entera = parte_entera.zfill(common_digit_count)
            elif len(parte_entera) > common_digit_count:
                parte_entera = ''.join([char for char in parte_entera if char.isdigit()])
                parte_entera = parte_entera[:common_digit_count]
            
            # Limpiar caracteres extraños como "?" o letras similares a números
            parte_entera = ''.join([
                '7' if char == '?' else
                '5' if char.lower() == 's' else
                '0' if not char.isdigit() else char
                for char in parte_entera
            ])
            
            # Reconstruir la coordenada limpiada
            cleaned_coord = f"{signo}{parte_entera}.{parte_decimal}"
            corrected_coord.append(cleaned_coord)
        
        coordenadas_corregidas.append(corrected_coord)
    return coordenadas_corregidas

# Función para convertir coordenadas UTM a geográficas
def convert_to_geographic(coordenadas, tipo_coordenadas, zona=None, hemisferio=None):
    coordenadas_geograficas = []
    if tipo_coordenadas == 'utm' and zona and hemisferio:
        print('Entro a convertir UTM')
        if hemisferio.upper() == 'N':
            proj_utm = Proj(proj='utm', zone=int(zona), ellps='WGS84', south=False)
        elif hemisferio.upper() == 'S':
            proj_utm = Proj(proj='utm', zone=int(zona), ellps='WGS84', south=True)
        else:
            raise ValueError("Hemisferio no válido. Usa 'N' para norte o 'S' para sur.")
        proj_wgs84 = Proj(proj='latlong', datum='WGS84')

        for coord in coordenadas:
            print('Vamos a imprimir la conversión de cada par de coordenadas')
            este = float(coord[0])
            print(este)
            norte = float(coord[1])
            print(norte)
            print('Lo que va a convertir es:')
            print(proj_utm)
            lon, lat = transform(proj_utm, proj_wgs84, este, norte)
            coordenadas_geograficas.append([lon, lat])
            print(coordenadas_geograficas)
    else:
        coordenadas_geograficas = [[float(coord[1]), float(coord[0])] for coord in coordenadas]
    print('Coordenadas ya convertidas')
    print(coordenadas_geograficas)
    return coordenadas_geograficas

# Función para crear y guardar un archivo KML (Longitud,Latitud)
def create_kml(coordenadas_geograficas, output_path="PolygonUTM.kml"):
    kml = simplekml.Kml()
    poligono = kml.newpolygon(name="Área del Polígono")
    poligono.outerboundaryis = coordenadas_geograficas + [coordenadas_geograficas[0]]
    poligono.style.polystyle.color = "7d00ff00"
    kml.save(output_path)
    print(f"Archivo KML generado exitosamente como '{output_path}'.")
    return output_path
