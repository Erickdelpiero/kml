import cv2
import pytesseract
import re
from collections import Counter
from pyproj import Proj, transform
import simplekml

# Configurar la ruta de Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Cargar la imagen en escala de grises
imagen = cv2.imread("./uploads/Imagen2.png", cv2.IMREAD_GRAYSCALE)

# Aplicar binarización
_, imagen_binaria = cv2.threshold(imagen, 180, 255, cv2.THRESH_BINARY)
escala = 2
imagen_agrandada = cv2.resize(imagen_binaria, None, fx=escala, fy=escala, interpolation=cv2.INTER_CUBIC)

# Filtro de eliminación de ruido
imagen_denoised = cv2.medianBlur(imagen_agrandada, 3)

# Extracción de texto con OCR
texto_extraido = pytesseract.image_to_string(imagen_denoised, config="--psm 3")

# Mostrar el texto extraído antes de la limpieza
print("Texto Extraído (Pre-Limpieza):")
print(texto_extraido)

# Limpieza del texto
lineas = texto_extraido.splitlines()
coordenadas = []

for linea in lineas:
    linea = linea.strip('| ').strip()
    linea = linea.replace(',', '.')
    match = re.findall(r"[-+]?[\d?sS]*\.\d+|\d+", linea)
    if len(match) == 2:
        coordenadas.append(match)

# Obtener la cantidad de dígitos mayoritaria en cada columna antes del punto
col1_digit_counts = [len(coord[0].split('.')[0].replace('-', '')) for coord in coordenadas]
col2_digit_counts = [len(coord[1].split('.')[0].replace('-', '')) for coord in coordenadas]

col1_common_digit_count = Counter(col1_digit_counts).most_common(1)[0][0]
col2_common_digit_count = Counter(col2_digit_counts).most_common(1)[0][0]

# Corregir cada coordenada
coordenadas_corregidas = []

for coord in coordenadas:
    corrected_coord = []
    for i, (parte_entera, common_digit_count) in enumerate(zip([coord[0], coord[1]], [col1_common_digit_count, col2_common_digit_count])):
        partes = parte_entera.split('.')
        parte_entera = partes[0]
        parte_decimal = partes[1] if len(partes) > 1 else ""
        signo = '-' if parte_entera.startswith('-') else ''
        parte_entera = parte_entera.lstrip('-')
        if len(parte_entera) < common_digit_count:
            parte_entera = parte_entera.zfill(common_digit_count)
        elif len(parte_entera) > common_digit_count:
            parte_entera = ''.join([char for char in parte_entera if char.isdigit()])
            parte_entera = parte_entera[:common_digit_count]
        parte_entera = ''.join([
            '7' if char == '?' else
            '5' if char.lower() == 's' else
            '0' if not char.isdigit() else char
            for char in parte_entera
        ])
        cleaned_coord = f"{signo}{parte_entera}.{parte_decimal}"
        corrected_coord.append(cleaned_coord)
    coordenadas_corregidas.append(corrected_coord)

# Preguntar al usuario el tipo de coordenadas
tipo_coordenadas = input("¿Las coordenadas son UTM o Geográficas? (Escriba 'UTM' o 'Geo'): ").strip().lower()

if tipo_coordenadas == 'utm':
    zona_utm = input("Ingrese la zona UTM (por ejemplo, 19): ").strip()
    hemisferio = input("Ingrese el hemisferio (N para Norte, S para Sur): ").strip().upper()
    
    if hemisferio == 'N':
        proj_utm = Proj(proj='utm', zone=int(zona_utm), ellps='WGS84', south=False)
    elif hemisferio == 'S':
        proj_utm = Proj(proj='utm', zone=int(zona_utm), ellps='WGS84', south=True)
    else:
        raise ValueError("Hemisferio no válido. Usa 'N' para norte o 'S' para sur.")
    proj_wgs84 = Proj(proj='latlong', datum='WGS84')
    
    coordenadas_geograficas = []
    for coord in coordenadas_corregidas:
        este = float(coord[0])
        norte = float(coord[1])
        lon, lat = transform(proj_utm, proj_wgs84, este, norte)
        coordenadas_geograficas.append([lon, lat])
else:
    coordenadas_geograficas = [[float(coord[1]), float(coord[0])] for coord in coordenadas_corregidas]

# Crear el archivo KML y dibujar el polígono
kml = simplekml.Kml()
poligono = kml.newpolygon(name="Área del Polígono")
poligono.outerboundaryis = coordenadas_geograficas + [coordenadas_geograficas[0]]  # Cerrar el polígono
poligono.style.polystyle.color = "7d00ff00"  # Color del polígono

# Guardar el archivo KML
kml.save("Polygon.kml")
print("Archivo KML generado exitosamente como 'Polygon.kml'.")
