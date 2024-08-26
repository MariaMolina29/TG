import numpy as np
import plotly.graph_objs as go
from scipy.signal import savgol_filter
import parselmouth
from parselmouth.praat import call

import io

def draw_spectrogram_3d(spectrogram):
    X, Y = np.meshgrid(spectrogram.xs(), spectrogram.ys())
    Z = 10 * np.log10(spectrogram.values)
 
    trace_surface = go.Surface(
        z=Z,
        x=X[0],
        y=Y[:, 0],
        colorscale='Inferno',  # Usar la misma escala de colores que en el espectrograma 2D
        colorbar=dict(title="Intensity [dB]", thickness=20)
    )
 
    layout = go.Layout(
        title="3D Spectrogram",
        scene=dict(
            xaxis=dict(title="Time [s]"),
            yaxis=dict(title="Frequency [Hz]", range=[0, 5000]),
            zaxis=dict(title="Intensity [dB]")
        )
    )
 
    return go.Figure(data=[trace_surface], layout=layout)
 
def draw_spectrogram(spectrogram, pitch, formants):
    X, Y = np.meshgrid(spectrogram.xs(), spectrogram.ys())
    Z = 10 * np.log10(spectrogram.values)
   
    trace_spectrogram = go.Heatmap(
        z=Z,
        x=X[0],
        y=Y[:, 0],
        colorscale='Inferno',
        colorbar=dict(title="Intensity [dB]", thickness=20)
    )
 
    # Suavizar la frecuencia fundamental
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values == 0] = np.nan  # Reemplazar partes no sonoras con NaN
   
    # Aplicar suavizado a la curva de la frecuencia fundamental
    smoothed_pitch_values = savgol_filter(pitch_values, window_length=11, polyorder=2)
   
    trace_pitch = go.Scatter(
        x=pitch.xs(),
        y=smoothed_pitch_values,
        mode='lines+markers',
        marker=dict(size=3, color='cyan'),
        line=dict(color='cyan'),
        name="Fundamental Frequency"
    )
 
    traces = [trace_spectrogram, trace_pitch]
 
    # Superponer las líneas de los formantes en 2D
    for formant_number in range(1, 4):  # Los primeros 3 formantes
        formant_values = [formants.get_value_at_time(formant_number, t) for t in formants.xs()]
        formant_values = np.array(formant_values)
        formant_values[formant_values < 300] = np.nan  # Filtrar valores por debajo de 300 Hz
        formant_values[formant_values > 5000] = np.nan  # Filtrar valores por encima de 5000 Hz
 
        trace_formant = go.Scatter(
            x=formants.xs(),
            y=formant_values,
            mode='lines+markers',
            marker=dict(size=2),
            line=dict(dash='dash'),
            name=f"Formant {formant_number}"
        )
        traces.append(trace_formant)
 
    layout = go.Layout(
        title="Spectrogram with Fundamental Frequency and Formants",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Frequency [Hz]", range=[0, 5000]),
        legend=dict(x=1.3, y=1)  # Mover la leyenda fuera del gráfico principal
    )
 
    return go.Figure(data=traces, layout=layout)
 
def draw_combined_pitch_intensity_contour(pitch, intensity):
    # Curva de pitch (frecuencia fundamental)
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values == 0] = np.nan  # Reemplazar partes no sonoras con NaN
 
    trace_pitch = go.Scatter(
        x=pitch.xs(),
        y=pitch_values,
        mode='lines+markers',
        marker=dict(size=3, color='red'),
        line=dict(color='red'),
        name="Fundamental Frequency"
    )
 
    # Curva de intensidad (dB)
    trace_intensity = go.Scatter(
        x=intensity.xs(),
        y=intensity.values.T.flatten(),
        mode='lines',
        line=dict(color='purple'),
        name="Intensity",
        yaxis="y2"  # Vincular al segundo eje y
    )
 
    layout = go.Layout(
        title="Pitch and Intensity Contour (Frequency and dB vs Time)",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Frequency [Hz]", range=[0, 1000]),
        yaxis2=dict(
            title="Intensity [dB]",
            overlaying='y',
            side='right'
        ),
        legend=dict(x=1.05, y=1)
    )
 
    return go.Figure(data=[trace_pitch, trace_intensity], layout=layout)
 
def draw_power_spectrum(frequencies, power, formants):
    power = power.flatten()
   
    # Verificar que frequencies y power tengan la misma longitud
    if len(frequencies) != len(power):
        min_length = min(len(frequencies), len(power))
        frequencies = frequencies[:min_length]
        power = power[:min_length]
   
    valid_idx = np.isfinite(power)
    frequencies = frequencies[valid_idx]
    power = power[valid_idx]
 
    smoothed_power = savgol_filter(power, window_length=101, polyorder=2)
 
    trace_smoothed = go.Scatter(
        x=frequencies,
        y=smoothed_power,
        mode='lines',
        line=dict(color='blue', width=3),
        name="Smoothed Power Spectrum"
    )
 
    traces = [trace_smoothed]
 
    # Añadir líneas verticales para las resonancias de los formantes
    for formant_number in range(1, 4):  # Visualizar las resonancias de los primeros 3 formantes
        formant_values = [formants.get_value_at_time(formant_number, t) for t in formants.xs()]
        formant_values = np.array(formant_values)
        formant_values = formant_values[np.isfinite(formant_values)]  # Filtrar NaNs
        mean_formant = np.mean(formant_values)
 
        trace_formant_line = go.Scatter(
            x=[mean_formant, mean_formant],
            y=[np.min(smoothed_power), np.max(smoothed_power)],
            mode='lines',
            line=dict(color='red', dash='dot'),
            name=f"Formant {formant_number} Resonance"
        )
        traces.append(trace_formant_line)
 
    layout = go.Layout(
        title="Power Spectrum with Smoothed Envelope and Formant Resonances",
        xaxis=dict(title="Frequency [Hz]", range=[0, 5000]),
        yaxis=dict(title="Power [dB]")
    )
 
    return go.Figure(data=traces, layout=layout)
 
def draw_waveform(xs, values):
    trace_waveform = go.Scatter(
        x=xs,
        y=values.flatten(),
        mode='lines',
        line=dict(color='black'),
        name="Waveform"
    )
 
    layout = go.Layout(
        title="Waveform (Oscillogram)",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Amplitude")
    )
 
    return go.Figure(data=[trace_waveform], layout=layout)
 
def generate_text_file(pitch, intensity, formants):
    """
    Genera un archivo de texto con los datos de pitch, intensidad y formantes.
    """
    output = io.StringIO()
   
    output.write("Pitch Data (Frequency vs Time):\n")
    output.write("Time [s]\tFrequency [Hz]\n")
    for time, frequency in zip(pitch.xs(), pitch.selected_array['frequency']):
        output.write(f"{time:.4f}\t{frequency:.2f}\n")
   
    output.write("\nIntensity Data (dB vs Time):\n")
    output.write("Time [s]\tIntensity [dB]\n")
    for time, intensity_value in zip(intensity.xs(), intensity.values.T.flatten()):
        output.write(f"{time:.4f}\t{intensity_value:.2f}\n")
   
    output.write("\nFormants Data:\n")
    for formant_number in range(1, 4):
        output.write(f"Formant {formant_number}:\n")
        output.write("Time [s]\tFormant Frequency [Hz]\n")
        for time in formants.xs():
            formant_value = formants.get_value_at_time(formant_number, time)
            output.write(f"{time:.4f}\t{formant_value:.2f}\n")
        output.write("\n")
   
    text_content = output.getvalue()
    output.close()
   
    return text_content

def analyze_audio(signal, live):
    global RATE
    if live:
        snd = parselmouth.Sound(signal, sampling_frequency=RATE)
    else:
        try:
            snd = parselmouth.Sound(signal)

        except Exception as e:
            print(f"Error al analizar el archivo: {e}")
            return None, None, None, None, None, None, None
       
        # Cargar el archivo usando parselmouth
       
        # Análisis de Pitch (frecuencia fundamental)
        pitch = snd.to_pitch()
        mean_pitch = call(pitch, "Get mean", 0, 0, "Hertz")
 
        # Análisis de Formantes usando LPC (método Burg)
        formants = snd.to_formant_burg()
 
        # Análisis de Intensidad
        intensity = snd.to_intensity()
 
        # Generar el espectrograma 3D con Plotly
        spectrogram_3d_fig = draw_spectrogram_3d(snd.to_spectrogram(window_length=0.005, maximum_frequency=5000))
 
        # Generar el espectrograma 2D con Plotly
        spectrogram_fig = draw_spectrogram(snd.to_spectrogram(window_length=0.005, maximum_frequency=5000), pitch, formants)
 
        # Generar el espectro de potencia con Plotly
        spectrum = snd.to_spectrum()
        frequencies = spectrum.xs()
        power = np.where(spectrum.values.T > 0, 10 * np.log10(spectrum.values.T), np.nan)
        spectrum_fig = draw_power_spectrum(frequencies, power, formants)
 
        # Generar el oscilograma con Plotly
        waveform_fig = draw_waveform(snd.xs(), snd.values)
 
        # Generar la gráfica combinada de pitch e intensidad
        combined_pitch_intensity_fig = draw_combined_pitch_intensity_contour(pitch, intensity)
 
        # Generar el archivo de texto con los datos
        text_content = generate_text_file(pitch, intensity, formants)
 
        return mean_pitch, spectrogram_3d_fig, spectrogram_fig, spectrum_fig, waveform_fig, combined_pitch_intensity_fig, text_content

