# cuadro_cargas_app.py

import pandas as pd
import math
import streamlit as st
import re
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Tabla interna de eficiencias DOE
eficiencia_doe = pd.DataFrame({
    'POTENCIA': [3, 5, 10, 15, 30, 45, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1250, 1500, 1600, 2000, 2500, 3750, 5000, 7500, 10000],
    'SECOS': [0.99, 0.99, 0.99, 0.9789, 0.9823, 0.984, 0.986, 0.9874, 0.9883, 0.9894, 0.9902, 0.9914, 0.9923, 0.9928, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99],
    'ACEITE': [0.99, 0.99, 0.99, 0.9865, 0.9883, 0.9892, 0.9903, 0.9911, 0.9916, 0.9923, 0.9927, 0.9935, 0.994, 0.9943, 0.99, 0.9948, 0.99, 0.9951, 0.9953, 0.99, 0.99, 0.99, 0.99]
})

def interpretar_texto(texto):
    carga = {
        'Id': '-',
        'Carga': 'CARGA DESDE TEXTO',
        'Tensión [V]': 220,
        'Sistema': '3 fases',
        'Tipo': 'Motor',
        'Potencia Valor': 0,
        'Potencia Unidad': 'hp',
        'Tipo de Uso': 'Contínuo',
        'VFD': 'No'
    }

    texto = texto.lower()
    if 'motor' in texto:
        carga['Tipo'] = 'Motor'
    elif 'ilumin' in texto:
        carga['Tipo'] = 'Iluminación'
    elif 'cómputo' in texto or 'computo' in texto:
        carga['Tipo'] = 'Eq Cómputo'
    elif 'aire' in texto:
        carga['Tipo'] = 'Aire Acondicionado'

    if 'vfd' in texto:
        carga['VFD'] = 'Sí'

    if 'stand by' in texto:
        carga['Tipo de Uso'] = 'Stand By'
    elif 'intermitente' in texto:
        carga['Tipo de Uso'] = 'Intermitente'
    else:
        carga['Tipo de Uso'] = 'Contínuo'

    if 'trifásico' in texto or '3 fases' in texto:
        carga['Sistema'] = '3 fases'
    elif '2 fases' in texto:
        carga['Sistema'] = '2 fases'
    elif 'monofásico' in texto or '1 fase' in texto:
        carga['Sistema'] = '1 fase'

    if '120v' in texto:
        carga['Tensión [V]'] = 120
    elif '208v' in texto:
        carga['Tensión [V]'] = 208
    elif '220v' in texto:
        carga['Tensión [V]'] = 220
    elif '480v' in texto:
        carga['Tensión [V]'] = 480

    match = re.search(r'(\d+(\.\d+)?)\s*(hp|kw|kva)', texto)
    if match:
        carga['Potencia Valor'] = float(match.group(1))
        unidad = match.group(3).lower()
        if unidad == 'kw':
            carga['Potencia Unidad'] = 'kW'
        elif unidad == 'kva':
            carga['Potencia Unidad'] = 'kVA'
        else:
            carga['Potencia Unidad'] = 'hp'

    return carga
