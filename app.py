[#1-importaciones]
import pandas as pd
import math
import streamlit as st
import re
from unicodedata import normalize

[#2-tabla_eficiencia_doe]
eficiencia_doe = pd.DataFrame({
    'POTENCIA': [3, 5, 10, 15, 30, 45, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1250, 1500, 1600, 2000, 2500, 3750, 5000, 7500, 10000],
    'SECOS':    [0.99, 0.99, 0.99, 0.9789, 0.9823, 0.984, 0.986, 0.9874, 0.9883, 0.9894, 0.9902, 0.9914, 0.9923, 0.9928, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99],
    'ACEITE':   [0.99, 0.99, 0.99, 0.9865, 0.9883, 0.9892, 0.9903, 0.9911, 0.9916, 0.9923, 0.9927, 0.9935, 0.994, 0.9943, 0.99, 0.9948, 0.99, 0.9951, 0.9953, 0.99, 0.99, 0.99, 0.99]
})

[#3-funcion_interpretar_texto]
def limpiar_texto(t):
    t = t.lower()
    t = normalize('NFKD', t).encode('ASCII', 'ignore').decode('utf-8')
    return t.replace(",", "").replace(".", "").strip()

def interpretar_texto(texto):
    texto = limpiar_texto(texto)
    carga = {
        'Id': '-',
        'Carga': texto,
        'Tensión [V]': None,
        'Sistema': None,
        'Tipo': None,
        'Potencia Valor': None,
        'Potencia Unidad': None,
        'Tipo de Uso': None,
        'VFD': 'N/A'
    }

    tipos_equiv = {
        'Motor': ['motor'],
        'Iluminación': ['iluminacion', 'luz', 'bombillo'],
        'Eq Cómputo': ['computo', 'pc', 'servidor'],
        'Aire Acondicionado': ['aire acondicionado', 'ac']
    }

    sistemas_equiv = {
        '1 fase': ['1fase', '1 fase', 'monofasico', '1f', 'una fase'],
        '2 fases': ['2fase', '2 fases', 'bifasico', '2f', 'dos fases'],
        '3 fases': ['3fase', '3 fases', 'trifasico', '3f', 'tres fases']
    }

    usos_equiv = {
        'Stand By': ['stand by', 'respaldo', 'carga en stand by', 'motor de respaldo', 'espera'],
        'Intermitente': ['intermitente', 'carga intermitente'],
        'Contínuo': ['continuo', 'continua', 'carga continua']
    }

    tensiones_equiv = {
        120: ['120v'],
        208: ['208v'],
        220: ['220v'],
        480: ['480v']
    }

    for tipo, variantes in tipos_equiv.items():
        if any(v in texto for v in variantes):
            carga['Tipo'] = tipo
            break

    for sistema, variantes in sistemas_equiv.items():
        if any(v in texto for v in variantes):
            carga['Sistema'] = sistema
            break

    for uso, variantes in usos_equiv.items():
        if any(v in texto for v in variantes):
            carga['Tipo de Uso'] = uso
            break

    for tension, variantes in tensiones_equiv.items():
        if any(v in texto for v in variantes):
            carga['Tensión [V]'] = tension
            break

    if 'vfd' in texto:
        carga['VFD'] = 'Sí'

    match = re.search(r'(\d+(\.\d+)?)\s*(hp|kw|kva)s?', texto)
    if match:
        carga['Potencia Valor'] = float(match.group(1))
        unidad = match.group(3).lower()
        carga['Potencia Unidad'] = 'kW' if unidad == 'kw' else 'kVA' if unidad == 'kva' else 'hp'

    return carga

[#4-funcion_validar_carga]
def validar_carga(carga):
    errores = []
    for campo in ['Tipo', 'Tensión [V]', 'Sistema', 'Potencia Valor', 'Potencia Unidad', 'Tipo de Uso']:
        if not carga[campo]:
            errores.append(f"Falta: {campo}")
    return errores

[#5-funcion_calcular_potencia]
def calcular_potencia(carga):
    tipo = carga['Tipo']
    unidad = carga['Potencia Unidad']
    valor = carga['Potencia Valor']
    uso = carga['Tipo de Uso']
    vfd = carga.get('VFD', 'N/A')
    fp = 0.9 if tipo in ['Iluminación', 'Motor'] else 0.92 if tipo == 'Eq Cómputo' else 0.88 if tipo == 'Aire Acondicionado' else 0.9
    if tipo == 'Motor': fp = 0.98 if vfd == 'Sí' else 0.88
    eff = 0.9 if tipo == 'Motor' and vfd == 'Sí' else 0.95
    fu = 0 if uso == "Stand By" else 1
    p_kw = (valor * 0.746 / eff if unidad == 'hp' else valor / eff if unidad == 'kW' else valor * fp / eff) * fu
    q_kvar = p_kw * math.tan(math.acos(fp))
    s_kva = math.sqrt(p_kw**2 + q_kvar**2)
    return fp, eff, fu, p_kw, q_kvar, s_kva

[#6-funcion_seleccionar_transformador]
def seleccionar_transformador(kva_total_div):
    candidatos = eficiencia_doe[eficiencia_doe['POTENCIA'] >= kva_total_div]
    return candidatos.iloc[0]['POTENCIA'] if not candidatos.empty else eficiencia_doe['POTENCIA'].max()

[#7-funcion_obtener_eficiencia]
def obtener_eficiencia(tr_sel, tr_tipo):
    fila = eficiencia_doe[eficiencia_doe['POTENCIA'] == tr_sel]
    return fila.iloc[0][tr_tipo.upper()] if not fila.empty else 0.88

[#8-funcion_calculo_final]
def calcular_resultados_finales(cargas, fd, res_min, tr_tipo):
    kw_total, kvar_total, resultados_cargas = 0, 0, []
    for i, carga in enumerate(cargas):
        fp, eff, fu, p, q, s = calcular_potencia(carga)
        kw_total += p
        kvar_total += q
        carga.update({
            'No': i+1, 'Factor de Potencia': round(fp, 3), 'Eficiencia': round(eff, 3),
            'Factor Utilización': fu, 'P [kW]': round(p, 2), 'Q [kVAR]': round(q, 2), 'S [kVA]': round(s, 2)
        })
        resultados_cargas.append(carga)
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
    tr_carg = (kva_div + tr_perd / fp_total) / tr_sel
    resumen = {
        'P [kW] total': kw_total, 'Q [kVAR] total': kvar_total, 'S [kVA] total': kva_total,
        'Factor de potencia total': fp_total, 'Carga diversificada [kVA]': kva_div,
        'Carga con reserva [kVA]': kva_total_div, 'Transformador seleccionado [kVA]': tr_sel,
        'Eficiencia': tr_eff, 'Pérdidas [kW]': tr_perd, 'Demanda total con pérdidas [kVA]': kva_total_div_perd,
        'Reserva final [kVA]': res_final_kva, 'Reserva final [%]': res_final_pct, 'Cargabilidad [%]': tr_carg
    }
    return resultados_cargas, resumen

[#9-interfaz_usuario_streamlit]
st.title("Transformador por lenguaje natural")

if "cargas" not in st.session_state:
    st.session_state["cargas"] = []
    st.session_state["fase"] = "entrada"

[#10-ingreso_carga_texto]
if st.session_state["fase"] == "entrada":
    texto = st.text_input("Describe una carga nueva:")
    if st.button("Interpretar carga"):
        nueva_carga = interpretar_texto(texto)
        errores = validar_carga(nueva_carga)
        if errores:
            st.error("Faltan datos: " + ", ".join(errores))
        else:
            st.session_state["cargas"].append(nueva_carga)
            st.success("Carga agregada correctamente.")

    if st.session_state["cargas"]:
        st.markdown("### Cargas ingresadas:")
        for i, carga in enumerate(st.session_state["cargas"], 1):
            st.write(f"{i}. {carga['Carga']}")

    continuar = st.radio("¿Deseas ingresar otra carga?", ["Sí", "No"], index=0, key="continuar_radio")
    if continuar == "No":
        st.session_state["fase"] = "parametros"

[#11-ingreso_parametros_generales]
if st.session_state["fase"] == "parametros":
    st.subheader("Parámetros Generales")
    factor_div = st.text_input("¿Qué factor de diversificación deseas? (entre 0 y 1):")
    try:
        fd = float(factor_div)
        if not (0 <= fd <= 1):
            st.error("⚠️ El factor debe ser un número entre 0 y 1.")
            st.stop()
    except:
        st.error("⚠️ Factor de diversificación debe ser un número decimal entre 0 y 1.")
        st.stop()

    reserva = st.text_input("¿Qué porcentaje de reserva deseas para el transformador?")
    try:
        res_min = float(reserva)
    except:
        st.error("⚠️ Porcentaje de reserva debe ser un número decimal.")
        st.stop()

    tipo = st.text_input("¿Qué tipo de transformador deseas? (Seco o Aceite)")
    tipo_limpio = tipo.strip().upper()
    if tipo_limpio not in ["SECO", "ACEITE"]:
        st.error("⚠️ Debes ingresar 'Seco' o 'Aceite'.")
        st.stop()

    if st.button("Calcular resultados"):
        resultados_cargas, resumen = calcular_resultados_finales(st.session_state["cargas"], fd, res_min, tipo_limpio)
        st.subheader("Listado de Cargas")
        st.dataframe(pd.DataFrame(resultados_cargas))
        st.subheader("Resumen Final")
        for key, val in resumen.items():
            st.write(f"{key}: {round(val, 2)}")
