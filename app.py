from flask import Flask, request, render_template, redirect, url_for, send_file
import Process  # Importamos el archivo Process.py como un módulo
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['KML_FOLDER'] = 'kml_files'

#Ruta para la página principal (inicio)
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para subir imagen y procesarla
@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['file']
    if file and file.filename != '':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Usar funciones de Process.py
        imagen_preprocesada = Process.load_and_preprocess_image(filepath) #Leo y acondiciono la imagen
        texto_extraido = Process.extract_text_from_image(imagen_preprocesada) #Extraigo el texto
        coordenadas = Process.process_text_for_coordinates(texto_extraido) #Texto final limpio
        
        # Mostrar el texto extraído y permitir que el usuario lo edite
        return render_template('edit_text.html', coordenadas=coordenadas)

@app.route('/edit_text')
def edit_text():
    coordenadas = []  # Crea una lista vacía inicialmente
    if not coordenadas:
        coordenadas.append(["", ""])  # Agrega una fila vacía con dos entradas vacías
    return render_template("edit_text.html", coordenadas=coordenadas)


# Ruta para generar el archivo KML
@app.route('/generate_kml', methods=['POST'])
def generate_kml():
    tipo_coordenadas = request.form['tipo_coordenadas']
    zona = request.form.get('zone')
    print('Zona')
    print(zona)
    hemisferio = request.form.get('hemisferio')
    print('Hemisferio')
    print(hemisferio)
    latitudes = request.form.getlist('latitud[]')
    longitudes = request.form.getlist('longitud[]')
    Newcoordenadas = "\n".join(f"{lat},{lon}" for lat, lon in zip(latitudes, longitudes))
    print(Newcoordenadas)
    coordenadas = Process.process_text_for_coordinates(Newcoordenadas)
    coordenadas_geograficas = Process.convert_to_geographic(coordenadas, tipo_coordenadas, zona, hemisferio)
    kml_path = Process.create_kml(coordenadas_geograficas, os.path.join(app.config['KML_FOLDER'], "Polygon.kml"))
    
    return send_file(kml_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
