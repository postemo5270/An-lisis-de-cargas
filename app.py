import streamlit as st
import math
import pandas as pd

st.title("Cálculo de Cargas Eléctricas")

FACTOR_UTILIZACION = 0.8
FACTOR_POTENCIA = 0.9
EFICIENCIA = 0.88

def convertir_a_kW(valor, unidad):
    if unidad == "hp":
        return valor * 0.746
    elif unidad == "kW":
        return valor
    elif unidad == "kVA":
        return valor * FACTOR_POTENCIA
    else:
        return 0

def calcular_potencias(pot_kW):
    P = pot_kW * FACTOR_UTILIZACION
    Q = P * math.tan(math.acos(FACTOR_POTENCIA))
    S = math.sqrt(P**2 + Q**2)
    return round(P, 2), round(Q, 2), round(S, 2)

n = st.number_input("¿Cuántas cargas quieres ingresar?", min_value=1, step=1)

datos = []
for i in range(n):
    st.subheader(f"Carga {i+1}")
    nombre = st.text_input(f"Descripción de la carga {i+1}", key=f"desc_{i}")
    voltaje = st.number_input(f"Voltaje [V] de la carga {i+1}", key=f"volt_{i}")
    valor = st.number_input(f"Valor de potencia de la carga {i+1}", key=f"val_{i}")
    unidad = st.selectbox(f"Unidad de potencia de la carga {i+1}", ["hp", "kW", "kVA"], key=f"uni_{i}")

    pot_kW = convertir_a_kW(valor, unidad)
    P, Q, S = calcular_potencias(pot_kW)

    datos.append({
        "Carga": nombre,
        "Voltaje [V]": voltaje,
        "Potencia ingresada": f"{valor} {unidad}",
        "Potencia [kW]": round(pot_kW, 2),
        "P [kW]": P,
        "Q [kVAR]": Q,
        "S [kVA]": S
    })

df = pd.DataFrame(datos)
st.subheader("Resumen de cargas:")
st.dataframe(df)
