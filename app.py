import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Análisis de Cargas Eléctricas")
st.title("Aplicación de Cálculo de Cargas Eléctricas")

FACTOR_UTILIZACION = 0.8
FACTOR_POTENCIA = 0.9
EFICIENCIA = 0.88

# Conversión de unidades a kW
def convertir_a_kW(valor, unidad):
    if unidad == "hp":
        return valor * 0.746
    elif unidad == "kW":
        return valor
    elif unidad == "kVA":
        return valor * FACTOR_POTENCIA
    else:
        return 0

# Cálculo de potencias
def calcular_potencias(pot_kW):
    P = pot_kW * FACTOR_UTILIZACION
    Q = P * math.tan(math.acos(FACTOR_POTENCIA))
    S = math.sqrt(P**2 + Q**2)
    return round(P, 2), round(Q, 2), round(S, 2)

st.markdown("Ingrese los datos de las cargas a analizar:")
n = st.number_input("Número de cargas a ingresar", min_value=1, step=1)

cargas = []
for i in range(n):
    st.subheader(f"Carga {i+1}")
    tag = st.text_input(f"TAG de la carga {i+1}", key=f"tag_{i}")
    descripcion = st.text_input(f"Descripción de la carga {i+1}", key=f"desc_{i}")
    tipo = st.selectbox(f"Tipo de carga {i+1}", ["Iluminación", "Motor", "Equipo electrónico", "Aire acondicionado", "Otro"], key=f"tipo_{i}")
    tension = st.selectbox(f"Tensión [V] de la carga {i+1}", [120, 208, 220, 440, 480], key=f"tens_{i}")
    valor = st.number_input(f"Valor de la potencia de la carga {i+1}", key=f"valor_{i}")
    unidad = st.selectbox(f"Unidad de la potencia", ["hp", "kW", "kVA"], key=f"unidad_{i}")

    pot_kW = convertir_a_kW(valor, unidad)
    P, Q, S = calcular_potencias(pot_kW)

    cargas.append({
        "TAG": tag,
        "Descripción": descripcion,
        "Tipo": tipo,
        "Tensión [V]": tension,
        "Potencia ingresada": f"{valor} {unidad}",
        "Potencia [kW]": round(pot_kW, 2),
        "P [kW]": P,
        "Q [kVAR]": Q,
        "S [kVA]": S
    })

# Mostrar resumen
df_resultado = pd.DataFrame(cargas)
st.subheader("Resumen de cargas")
st.dataframe(df_resultado, use_container_width=True)

# Opcional: descarga como CSV
csv = df_resultado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Descargar resumen como CSV",
    data=csv,
    file_name='resumen_cargas.csv',
    mime='text/csv'
)  
# Actualización de la app con nuevas fórmulas y estructura de cálculo
