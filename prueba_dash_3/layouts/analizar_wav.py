# Función de layout para "Analizar un archivo .wav"
from dash import html, dcc
def layout_analizar_wav():
    return html.Div(children=[
        html.H2('Analizar un archivo .wav'),
        dcc.Upload(
            id='upload-wav',
            children=html.Button('Seleccionar archivo .wav'),
            accept='.wav'
        ),
        html.Button('Analizar archivo .wav', id='analizar-boton'),
        html.H3(id='resultado'),
        html.Div(id='output-audio-analysis', style={'display': 'none'}, children=[
            html.Audio(id='audio-player', controls=True, style={'width': '100%'}, src=''),
            html.A('Descargar Datos en .txt', id='download-link', download="audio_analysis.txt", href="", target="_blank", style={'display': 'block', 'marginTop': '20px'}),
            html.H3(id='pitch'),
            dcc.Graph(id='spectrogram', className='cursor2d', style={'display': 'inline-block', 'width': '60%'}),
            dcc.Graph(id='spectrogram-3d', className='cursor3d', style={'display': 'inline-block', 'width': '38%'}),
            dcc.Graph(id='waveform', className='cursor2d', style={'display': 'inline-block', 'width': '48%'}),
            dcc.Graph(id='combined-pitch-intensity', className='cursor2d', style={'display': 'inline-block', 'width': '48%'}),
            dcc.Graph(id='spectrum')
        ]),       
        html.Button('Regresar', id='btn-regresar', n_clicks=0),  # Botón de regreso
        html.Div (style={'display': 'none'},children=[
            html.Button('Analizar mi voz', id='btn-analizar-voz', n_clicks=0),
            html.Button('Analizar un archivo .wav', id='btn-analizar-wav', n_clicks=0)
        ])
    ])
