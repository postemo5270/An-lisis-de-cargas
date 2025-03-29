# seleccion_conductores_app.py

import pandas as pd
import math
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

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

def calcular_potencia(carga):
    tipo = carga['Tipo']
    unidad = carga['Potencia Unidad']
    valor = carga['Potencia Valor']
    uso = carga['Tipo de Uso']
    vfd = carga['VFD']

    if tipo == "Iluminación":
        fp = 0.9
    elif tipo == "Eq Cómputo":
        fp = 0.92
    elif tipo == "Aire Acondicionado":
        fp = 0.88
    elif tipo == "Motor":
        fp = 0.98 if vfd == "Sí" else 0.88
    else:
        fp = 0.9

    if tipo in ["Iluminación", "Eq Cómputo", "Aire Acondicionado"]:
        eff = 0.95
    elif tipo == "Motor":
        eff = 0.9 if vfd == "Sí" else 0.95
    else:
        eff = 0.95

    fu = 0 if uso == "Stand By" else 1

    if unidad == "hp":
        p_kw = valor * 0.746 / eff
    elif unidad == "kW":
        p_kw = valor / eff
    else:
        p_kw = valor * fp / eff

    p_kw *= fu
    q_kvar = p_kw * math.tan(math.acos(fp))
    s_kva = math.sqrt(p_kw**2 + q_kvar**2)

    return fp, eff, fu, p_kw, q_kvar, s_kva

def calcular_resultados_finales(cargas, fd, res_min, tr_tipo):
    kw_total = 0
    kvar_total = 0
    resultados_cargas = []

    for i, carga in enumerate(cargas):
        fp, eff, fu, p, q, s = calcular_potencia(carga)
        kw_total += p
        kvar_total += q
        carga_res = carga.copy()
        carga_res.update({
            'No': i+1,
            'Factor de Potencia': round(fp, 3),
            'Eficiencia': round(eff, 3),
            'Factor Utilización': fu,
            'P [kW]': round(p, 2),
            'Q [kVAR]': round(q, 2),
            'S [kVA]': round(s, 2)
        })
        resultados_cargas.append(carga_res)

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

    resumen = {
        'P [kW] total': kw_total,
        'Q [kVAR] total': kvar_total,
        'S [kVA] total': kva_total,
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

    return resultados_cargas, resumen

def generar_pdf(cargas_df, resumen):
    doc = SimpleDocTemplate("resultado_final.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Listado de Cargas", styles['Heading2']))
    table_data = [list(cargas_df.columns)] + cargas_df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Resumen Final", styles['Heading2']))

    for key, val in resumen.items():
        elements.append(Paragraph(f"<b>{key}:</b> {round(val, 2)}", styles['Normal']))

    doc.build(elements)

# Interfaz Streamlit
st.title("Aplicación de Selección de Conductores y Transformador")

st.subheader("Ingresar Cargas")
n_cargas = st.number_input("Número de cargas", min_value=1, max_value=20, value=5)
cargas = []

for i in range(int(n_cargas)):
    st.markdown(f"### Carga {i+1}")
    id_carga = st.text_input("ID", key=f"id_{i}")
    nombre_carga = st.text_input("Descripción de la carga", key=f"desc_{i}")
    tension = st.selectbox("Tensión [V]", [120, 208, 220, 480], key=f"tension_{i}")
    sistema = st.selectbox("Sistema", ["1 fase", "2 fases", "3 fases"], key=f"sistema_{i}")
    tipo = st.selectbox(f"Tipo", ["Iluminación", "Eq Cómputo", "Aire Acondicionado", "Motor"], key=f"tipo_{i}")
    valor = st.number_input("Potencia Valor", key=f"valor_{i}")
    unidad = st.selectbox("Unidad", ["hp", "kW", "kVA"], key=f"unidad_{i}")
    uso = st.selectbox("Tipo de Uso", ["Contínuo", "Intermitente", "Stand By"], key=f"uso_{i}")
    vfd = st.selectbox("¿VFD?", ["Sí", "No", "N/A"], key=f"vfd_{i}")

    cargas.append({
        'Id': id_carga,
        'Carga': nombre_carga,
        'Tensión [V]': tension,
        'Sistema': sistema,
        'Tipo': tipo,
        'Potencia Valor': valor,
        'Potencia Unidad': unidad,
        'Tipo de Uso': uso,
        'VFD': vfd
    })

st.subheader("Parámetros Generales")
fd = st.slider("Factor de Diversificación", 0.0, 1.0, 0.75)
res_min = st.slider("Reserva mínima [%]", 0.0, 0.5, 0.2)
tr_tipo = st.selectbox("Tipo de transformador", ["SECO", "ACEITE"])

if st.button("Calcular resultados"):
    resultados_cargas, resumen = calcular_resultados_finales(cargas, fd, res_min, tr_tipo)
    df_resultado = pd.DataFrame(resultados_cargas)
    st.subheader("Listado de Cargas")
    st.dataframe(df_resultado)
    st.subheader("Resumen Final")
    for key, val in resumen.items():
        st.write(f"{key}: {round(val, 2)}")
    generar_pdf(df_resultado, resumen)
    with open("resultado_final.pdf", "rb") as f:
        st.download_button("Descargar PDF", f, file_name="resultado_final.pdf")
