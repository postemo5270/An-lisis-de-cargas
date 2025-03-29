# seleccion_conductores_app.py

import pandas as pd
import math
import streamlit as st

# Tabla interna de eficiencias DOE
eficiencia_doe = pd.DataFrame({
    'POTENCIA': [3, 5, 10, 15, 30, 45, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1250, 1500, 1600, 2000, 2500, 3750, 5000, 7500, 10000],
    'SECOS': [0.99, 0.99, 0.99, 0.9789, 0.9823, 0.984, 0.986, 0.9874, 0.9883, 0.9894, 0.9902, 0.9914, 0.9923, 0.9928, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99],
    'ACEITE': [0.99, 0.99, 0.99, 0.9865, 0.9883, 0.9892, 0.9903, 0.9911, 0.9916, 0.9923, 0.9927, 0.9935, 0.994, 0.9943, 0.99, 0.9948, 0.99, 0.9951, 0.9953, 0.99, 0.99, 0.99, 0.99]
})

def seleccionar_transformador(kva_total_div):
    candidatos = eficiencia_doe[eficiencia_doe['POTENCIA'] >= kva_total_div]
    if not candidatos.empty:
        return candidatos.iloc[0]['POTENCIA']
    else:
        return eficiencia_doe['POTENCIA'].max()

def obtener_eficiencia(tr_sel, tr_tipo):
    fila = eficiencia_doe[eficiencia_doe['POTENCIA'] == tr_sel]
    if not fila.empty:
        return fila.iloc[0][tr_tipo.upper()]
    return None

def calcular_resultados_finales(kw_total, kvar_total, fd, res_min, tr_tipo):
    kva_total = math.sqrt(kw_total**2 + kvar_total**2)
    fp_total = kw_total / kva_total if kva_total else 0

    kva_div = kva_total * fd
    kva_total_div = kva_div * (1 + res_min)

    tr_sel = seleccionar_transformador(kva_total_div)
    tr_eff = obtener_eficiencia(tr_sel, tr_tipo)

    tr_perd = tr_sel * fp_total * ((1 / tr_eff) - 1)
    kva_total_div_perd = kva_total_div + (tr_perd / fp_total)

    res_final_kva = tr_sel - kva_total_div_perd
    res_final_pct = res_final_kva / tr_sel
    tr_carg = kva_total_div_perd / tr_sel

    return {
        'Suma Total S[kVA]': kva_total,
        'Factor de potencia total': fp_total,
        'Carga diversificada [kVA]': kva_div,
        'Carga con reserva [kVA]': kva_total_div,
        'Transformador seleccionado [kVA]': tr_sel,
        'Eficiencia': tr_eff,
        'Pérdidas [kW]': tr_perd,
        'Demanda total con pérdidas [kVA]': kva_total_div_perd,
        'Reserva final [kVA]': res_final_kva,
        'Reserva final [%]': res_final_pct,
        'Cargabilidad [%]': tr_carg
    }

# Interfaz Streamlit
st.title("Selección de Transformador")

kw_total = st.number_input("Suma Total P [kW]", min_value=0.0, value=100.0)
kvar_total = st.number_input("Suma Total Q [kVAR]", min_value=0.0, value=50.0)
fd = st.slider("Factor de Diversificación", 0.0, 1.0, 0.75)
res_min = st.slider("Reserva mínima [%]", 0.0, 0.5, 0.2)
tr_tipo = st.selectbox("Tipo de transformador", ["SECO", "ACEITE"])

if st.button("Calcular"):
    resultados = calcular_resultados_finales(kw_total, kvar_total, fd, res_min, tr_tipo)
    for key, val in resultados.items():
        st.write(f"{key}: {round(val, 2)}")

