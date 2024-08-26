# Función de layout inicial
from dash import html
def layout_index():
    return html.Div(children=[
        html.H1('Opciones de análisis de audio'),
        html.Button('Analizar mi voz', id='btn-analizar-voz', n_clicks=0),
        html.Button('Analizar un archivo .wav', id='btn-analizar-wav', n_clicks=0),
        html.Div(children=[
            html.Button('Regresar', id='btn-regresar', n_clicks=0, style={'display': 'none'})  # Botón de regreso
        ])
    ])