from dash import Dash, html, dcc, Input, Output, State,callback_context, no_update
from layouts import layout_index, layout_analizar_voz, layout_analizar_wav
from graficas import analyze_audio
import parselmouth
import numpy as np
import base64
import plotly.graph_objs as go
from flask import Flask
from flask_socketio import SocketIO
import time
import pyaudio
import wave
import tempfile
import os

# Configuración inicial para el audio
CHUNK = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Variables globales para el audio
frames = []
audio = None
stream = None
is_recording = False
data_queue = []  # Lista para almacenar los frames
buffersize = 5  # Número máximo de frames a almacenar

# Inicializar variables globales para almacenar las últimas gráficas
last_oscillogram_fig = go.Figure()
last_spectrogram_fig = go.Figure()
real_time_analize = False
 
# Configurar Flask y SocketIO
server = Flask(__name__)
app = Dash(__name__, server=server, suppress_callback_exceptions=True, external_scripts=[
    "https://cdn.socket.io/4.0.0/socket.io.min.js"
])
socketio = SocketIO(server)

# Layout inicial 
app.layout = html.Div([
    html.Div(id='main-contetn', children=layout_index()) 
])

# Callback para actualizar el estado de la página
@app.callback(
    Output('main-contetn', 'children'),
    [Input('btn-analizar-voz', 'n_clicks'),
     Input('btn-analizar-wav', 'n_clicks'),
     Input('btn-regresar', 'n_clicks')]
)
def display_page( n_clicks_voz, n_clicks_wav, n_clicks_regresar):
    global real_time_analize

    ctx = callback_context  
    
    if not ctx.triggered:
        return layout_index()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn-analizar-voz':
        real_time_analize = True
        return layout_analizar_voz()
    elif button_id == 'btn-analizar-wav':
        real_time_analize = False
        return layout_analizar_wav()
    elif button_id == 'btn-regresar':
        real_time_analize = False
        return layout_index()


@app.server.route('/start-recording', methods=['POST'])
def start_recording():
    global is_recording, audio, stream, frames, data_queue
    # Limpiar referencias a stream y audio para liberar recursos
    if not is_recording:
        stream = None
        audio = None

        try:
            # Crear nueva instancia de PyAudio
            audio = pyaudio.PyAudio()
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK)
            frames = []
            data_queue = []  # Reiniciar la cola de datos
            is_recording = True

        except Exception as e:
            print(f"Error starting recording: {e}")
    return {"status": "recording started"}, 200

# Ruta del servidor para detener la grabación
@app.server.route('/stop-recording', methods=['POST'])
def stop_recording():
    global is_recording, audio, stream, frames, data_queue
    
    if is_recording:

        try:
            # Detener y cerrar el stream y la instancia de PyAudio
            stream.stop_stream()
            stream.close()
            audio.terminate()
            is_recording = False
 
        except Exception as e:
            print(f"Error stopping recording: {e}")
    return {"status": "recording stopped"}, 200


@app.callback(
    Output('output-analizar-mi-voz','style'),    
    Output('oscillogram_live', 'figure'),
    Output('spectrogram_live', 'figure'),
    Input('interval', 'n_intervals'),
    Input('analizar-boton', 'n_clicks')

)
def update_graphs(n_intervals,n_clicks_analize):

    global is_recording, audio, stream, frames, data_queue
    global last_oscillogram_fig, last_spectrogram_fig
    ctx = callback_context  
    
    if not ctx.triggered :
        return {'display': 'none'},last_oscillogram_fig, last_spectrogram_fig
        
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'analizar-boton':
         return {'display': 'none'},last_oscillogram_fig, last_spectrogram_fig
    if  is_recording and stream is not None:
        try:
            data = stream.read(CHUNK)
        except IOError as e:
            print(f"Error reading from stream: {e}")
            return {'display': 'none'},last_oscillogram_fig, last_spectrogram_fig
        
        frames.append(data)
        np_data = np.frombuffer(data, dtype=np.int16)
        
        # Agregar los nuevos datos a la cola
        data_queue.append(np_data)
        if len(data_queue) > buffersize:
            data_queue.pop(0)  # Eliminar el elemento más antiguo si se excede el tamaño máximo
        
        # Concatenar los datos en data_queue para obtener los datos a graficar
        all_data = np.concatenate(data_queue)

        # Procesar con Parselmouth
        sound = parselmouth.Sound(all_data, sampling_frequency=RATE)

        # Obtener oscilograma
        time = np.linspace(0, len(all_data) / RATE, num=len(all_data))
        oscillogram_trace = go.Scatter(x=time, y=all_data, mode='lines', name='Oscilograma')

        # Obtener espectrograma
        spectrogram = sound.to_spectrogram()
        spectrogram_matrix = spectrogram.values
        time_spec, freq_spec = np.meshgrid(spectrogram.x_grid(), spectrogram.y_grid())
        spectrogram_trace = go.Heatmap(
            x=time_spec[0],
            y=freq_spec[:, 0],
            z=10 * np.log10(spectrogram_matrix),  # Convertir a dB
            colorscale='Viridis'
        )

        # Actualizar las gráficas
        last_oscillogram_fig = go.Figure(data=[oscillogram_trace])
        last_spectrogram_fig = go.Figure(data=[spectrogram_trace])

        return {'display': 'block'},last_oscillogram_fig, last_spectrogram_fig
    else:
        return {'display': 'block'},last_oscillogram_fig, last_spectrogram_fig


@app.callback(
    Output('interval', 'disabled'),
    Output('start-button', 'style'),
    Output('stop-button', 'style'),
    Output('container-analize-button', 'style'),
    Input('start-button', 'n_clicks'),
    Input('stop-button', 'n_clicks'),
    Input('analizar-boton', 'n_clicks')
)
def update_interval (n_clicks_start,n_clicks_stop, n_clicks_analize):
    global is_recording, audio, stream, frames, data_queue
    ctx = callback_context
    # Si no hay clics, mantener el intervalo deshabilitado
    if not ctx.triggered:
        return True,  no_update, no_update, {'display': 'none'} 

    # Identificar cuál botón fue clickeado más recientemente
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Si el botón "Iniciar Grabación" fue clickeado, habilitar el intervalo
    if button_id == 'start-button':
        return False, no_update, no_update, {'display': 'none'}
    # Si el botón "Detener Grabación" fue clickeado, deshabilitar el intervalo
    if button_id == 'stop-button':
        return True, no_update, no_update, {'display': 'block'} 
    
    if button_id == 'analizar-boton':
        # Guardar el archivo WAV
        waveFile = wave.open('output.wav', 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        stream = None
        audio = None
        frames = []
        data_queue = []
        return True, {'display': 'none'}, {'display': 'none'}, {'display': 'block'}


    return True,  no_update, no_update, {'display': 'none'}


@app.callback(
    Output('resultado', 'children'),
    Output('output-audio-analysis', 'style'),
    Output('audio-player', 'src'),
    Output('download-link', 'href'),
    Output('pitch', 'children'),
    Output('spectrogram', 'figure'),
    Output('spectrogram-3d', 'figure'),
    Output('waveform', 'figure'),
    Output('combined-pitch-intensity', 'figure'),
    Output('spectrum', 'figure'),
    [Input('analizar-boton', 'n_clicks')],
    [State('upload-wav', 'contents')]
)

def update_output(n_clicks, contents):
    global real_time_analize

    if n_clicks is None and contents is None:
        # Devolver un estado inicial vacío sin gráficos
        return '', {'display': 'none'}, '', '', '', go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()
    
    if n_clicks is not None and n_clicks > 0:
        if real_time_analize:
            max_wait_time = 30 
            start_time = time.time()
            # Bucle de espera hasta que el archivo exista o se agote el tiempo de espera
            while not os.path.exists("output.wav"):
                if time.time() - start_time > max_wait_time:
                    print("Error: Tiempo de espera agotado. El archivo .wav no se generó.")
                    break
                print("Esperando a que se genere el archivo...")
                time.sleep(1)  
        if contents is None:
            if os.path.exists("output.wav"):
                # Leer el archivo local
                with open("output.wav", "rb") as f:
                    decoded = f.read()
                encoded_wav = base64.b64encode(decoded).decode('utf-8')
                # Crear la cadena src en formato base64
                contents = f"data:audio/wav;base64,{encoded_wav}"
            else:
                return '', {'display': 'none'}, '', '', '', go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    if isinstance(contents, str) and contents.startswith('data:'):
        # Decodificar el archivo subido
        decoded = base64.b64decode(contents.split(',')[1])

    # Crear un archivo temporal para almacenar el contenido del .wav
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav.write(decoded)
        tmp_wav_path = tmp_wav.name

    mean_pitch, spectrogram_3d_fig, spectrogram_fig, spectrum_fig, waveform_fig, combined_pitch_intensity_fig, text_content = analyze_audio(tmp_wav_path, False)

    if spectrogram_fig is None:
        return 'Error en el análisis. Por favor intenta con otro archivo.', {'display': 'none'}, '', '', '', go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    # Crear un download link
    download_link = "data:text/plain;base64," + base64.b64encode(text_content.encode()).decode()

    return 'Resultados del análisis:', {'display': 'block'}, contents, download_link, f'Pitch promedio: {mean_pitch:.2f} Hz', spectrogram_fig, spectrogram_3d_fig, waveform_fig, combined_pitch_intensity_fig, spectrum_fig



if __name__ == '__main__':
    app.run_server(debug=True)