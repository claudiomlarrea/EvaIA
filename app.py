import os
import json
import io
from datetime import datetime
from typing import Dict, List

import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="EvaIA - Inmunología",
    page_icon="🧪",
    layout="wide"
)

DATA_DIR = "data"
RESPUESTAS_FILE = os.path.join(DATA_DIR, "respuestas.csv")
CASES_FILE = "cases.json"


# =========================================================
# ESTILOS
# =========================================================
def aplicar_estilos():
    st.markdown(
        """
        <style>
        .main {
            background-color: #F8FAFC;
        }

        .evaia-header {
            background: linear-gradient(90deg, #0B4F8A 0%, #1669B2 100%);
            padding: 18px 22px;
            border-radius: 12px;
            color: white;
            margin-bottom: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        }

        .evaia-header h1 {
            margin: 0;
            font-size: 30px;
            font-weight: 700;
        }

        .evaia-header p {
            margin: 4px 0 0 0;
            font-size: 15px;
        }

        .subbox {
            background-color: white;
            padding: 14px 16px;
            border-radius: 10px;
            border-left: 5px solid #0B4F8A;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        }

        .metric-box {
            background-color: white;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .stButton > button,
        .stDownloadButton > button {
            background-color: #0B4F8A !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600 !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: #083A66 !important;
            color: white !important;
        }

        div[data-testid="stForm"] {
            background-color: white;
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 5px rgba(0,0,0,0.05);
        }

        .small-note {
            color: #4B5563;
            font-size: 13px;
        }
        div[data-testid="stForm"] label {
            color: #111111 !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def mostrar_encabezado():
    st.markdown(
        """
        <div class="evaia-header">
            <h1>EvaIA</h1>
            <p>Plataforma de aprendizaje basado en problemas con inteligencia artificial</p>
            <p><strong>Universidad Católica de Cuyo</strong> · Secretaría de Investigación · Asignatura Inmunología</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def asegurar_directorio():
    os.makedirs(DATA_DIR, exist_ok=True)


def cargar_casos() -> List[Dict]:
    if not os.path.exists(CASES_FILE):
        st.error(f"No se encontró el archivo {CASES_FILE}.")
        st.stop()

    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower().strip()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n"
    }
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)
    return texto


def puntuar_respuesta(respuesta: str, palabras_clave: List[str]) -> int:
    texto = normalizar_texto(respuesta)
    encontrados = 0

    for palabra in palabras_clave:
        if normalizar_texto(palabra) in texto:
            encontrados += 1

    if encontrados == 0:
        return 0
    elif encontrados <= max(1, len(palabras_clave) // 2):
        return 1
    else:
        return 2


def evaluar_caso(respuestas: Dict[str, str], caso: Dict) -> Dict:
    palabras = caso["evaluation_keywords"]

    comprension = puntuar_respuesta(
        respuestas["pregunta_1"], palabras["comprension_problema"]
    )
    aplicacion = puntuar_respuesta(
        respuestas["pregunta_2"], palabras["aplicacion_conceptual"]
    )
    razonamiento = puntuar_respuesta(
        respuestas["pregunta_3"], palabras["razonamiento_inmunologico"]
    )
    hipotesis = puntuar_respuesta(
        respuestas["pregunta_4"], palabras["hipotesis_diagnostica"]
    )
    fundamentacion = puntuar_respuesta(
        respuestas["pregunta_5"], palabras["fundamentacion"]
    )

    total = comprension + aplicacion + razonamiento + hipotesis + fundamentacion

    feedback = generar_feedback(
        comprension,
        aplicacion,
        razonamiento,
        hipotesis,
        fundamentacion,
        caso["model_answer"]
    )

    return {
        "comprension_problema": comprension,
        "aplicacion_conceptual": aplicacion,
        "razonamiento_inmunologico": razonamiento,
        "hipotesis_diagnostica": hipotesis,
        "fundamentacion": fundamentacion,
        "puntaje_total": total,
        "feedback": feedback
    }


def generar_feedback(
    comprension: int,
    aplicacion: int,
    razonamiento: int,
    hipotesis: int,
    fundamentacion: int,
    respuesta_modelo: str
) -> str:
    fortalezas = []
    mejoras = []

    if comprension >= 1:
        fortalezas.append("identificaste el problema clínico principal")
    else:
        mejoras.append("revisar la identificación del problema central")

    if aplicacion >= 1:
        fortalezas.append("reconociste componentes relevantes del sistema inmunológico")
    else:
        mejoras.append("fortalecer la aplicación de conceptos inmunológicos")

    if razonamiento >= 1:
        fortalezas.append("relacionaste la alteración inmunológica con la clínica")
    else:
        mejoras.append("mejorar el razonamiento inmunológico y fisiopatológico")

    if hipotesis >= 1:
        fortalezas.append("planteaste una hipótesis diagnóstica plausible")
    else:
        mejoras.append("precisar mejor la hipótesis diagnóstica")

    if fundamentacion >= 1:
        fortalezas.append("incorporaste cierta fundamentación científica")
    else:
        mejoras.append("ampliar la fundamentación con nociones de anticuerpos, linfocitos B e inmunidad humoral")

    texto_fortalezas = "; ".join(fortalezas) if fortalezas else "todavía no se evidencian fortalezas suficientes"
    texto_mejoras = "; ".join(mejoras) if mejoras else "continuar profundizando para consolidar el aprendizaje"

    return (
        f"Fortalezas: {texto_fortalezas}. "
        f"Aspectos a mejorar: {texto_mejoras}. "
        f"Respuesta modelo orientativa: {respuesta_modelo}"
    )


def guardar_resultado(registro: Dict):
    asegurar_directorio()

    df_nuevo = pd.DataFrame([registro])

    if os.path.exists(RESPUESTAS_FILE):
        df_existente = pd.read_csv(RESPUESTAS_FILE)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_csv(RESPUESTAS_FILE, index=False, encoding="utf-8-sig")


def cargar_resultados() -> pd.DataFrame:
    if os.path.exists(RESPUESTAS_FILE):
        return pd.read_csv(RESPUESTAS_FILE)
    return pd.DataFrame()


def generar_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resultados", index=False)

        resumen = pd.DataFrame({
            "Indicador": [
                "Cantidad de respuestas",
                "Promedio total",
                "Puntaje máximo",
                "Promedio comprensión del problema",
                "Promedio aplicación conceptual",
                "Promedio razonamiento inmunológico",
                "Promedio hipótesis diagnóstica",
                "Promedio fundamentación"
            ],
            "Valor": [
                len(df),
                round(df["puntaje_total"].mean(), 2) if not df.empty else 0,
                round(df["puntaje_total"].max(), 2) if not df.empty else 0,
                round(df["comprension_problema"].mean(), 2) if not df.empty else 0,
                round(df["aplicacion_conceptual"].mean(), 2) if not df.empty else 0,
                round(df["razonamiento_inmunologico"].mean(), 2) if not df.empty else 0,
                round(df["hipotesis_diagnostica"].mean(), 2) if not df.empty else 0,
                round(df["fundamentacion"].mean(), 2) if not df.empty else 0
            ]
        })
        resumen.to_excel(writer, sheet_name="Resumen", index=False)

    output.seek(0)
    return output.getvalue()


# =========================================================
# INTERFAZ
# =========================================================
aplicar_estilos()
mostrar_encabezado()

casos = cargar_casos()
caso = casos[0]

st.sidebar.title("EvaIA")
modo = st.sidebar.radio("Seleccioná un modo", ["Estudiante", "Docente"])
st.sidebar.markdown("---")
st.sidebar.write("**Carrera:** Medicina")
st.sidebar.write("**Asignatura:** Inmunología")
st.sidebar.write("**Versión:** Piloto 1 caso")
st.sidebar.write("**Caso activo:**")
st.sidebar.caption(caso["title"])


# =========================================================
# MODO ESTUDIANTE
# =========================================================
if modo == "Estudiante":
    st.subheader("Resolución del caso clínico")

    col_info1, col_info2 = st.columns([2, 1])

    with col_info1:
        st.markdown(
            f"""
            <div class="subbox">
                <strong>Caso clínico:</strong> {caso["title"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_info2:
        st.markdown(
            """
            <div class="subbox">
                <strong>Escala de evaluación:</strong> 0 a 10 puntos
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### Historia clínica")
    st.info(caso["clinical_story"])

    st.markdown("### Consigna")
    st.write(
        "Respondé cada pregunta de manera clara, precisa y fundamentada. "
        "Al finalizar, presioná **Evaluar caso**."
    )

    with st.form("form_estudiante"):
        col_a, col_b = st.columns(2)
        with col_a:
            nombre_estudiante = st.text_input("Nombre y apellido")
        with col_b:
            comision = st.text_input("Comisión / grupo", value="Comisión A")

        st.markdown("### Preguntas")
        respuesta_1 = st.text_area(f"1. {caso['questions'][0]}", height=100)
        respuesta_2 = st.text_area(f"2. {caso['questions'][1]}", height=100)
        respuesta_3 = st.text_area(f"3. {caso['questions'][2]}", height=100)
        respuesta_4 = st.text_area(f"4. {caso['questions'][3]}", height=100)
        respuesta_5 = st.text_area(f"5. {caso['questions'][4]}", height=130)

        enviado = st.form_submit_button("Evaluar caso")

    if enviado:
        if not nombre_estudiante.strip():
            st.warning("Ingresá el nombre y apellido del estudiante.")
            st.stop()

        respuestas = {
            "pregunta_1": respuesta_1,
            "pregunta_2": respuesta_2,
            "pregunta_3": respuesta_3,
            "pregunta_4": respuesta_4,
            "pregunta_5": respuesta_5
        }

        evaluacion = evaluar_caso(respuestas, caso)

        registro = {
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estudiante": nombre_estudiante,
            "comision": comision,
            "caso_id": caso["id"],
            "caso_titulo": caso["title"],
            "respuesta_1": respuesta_1,
            "respuesta_2": respuesta_2,
            "respuesta_3": respuesta_3,
            "respuesta_4": respuesta_4,
            "respuesta_5": respuesta_5,
            "comprension_problema": evaluacion["comprension_problema"],
            "aplicacion_conceptual": evaluacion["aplicacion_conceptual"],
            "razonamiento_inmunologico": evaluacion["razonamiento_inmunologico"],
            "hipotesis_diagnostica": evaluacion["hipotesis_diagnostica"],
            "fundamentacion": evaluacion["fundamentacion"],
            "puntaje_total": evaluacion["puntaje_total"],
            "feedback": evaluacion["feedback"]
        }

        guardar_resultado(registro)

        st.success("La respuesta fue evaluada y guardada correctamente.")

        st.markdown("## Resultado de la evaluación")

        m1, m2, m3 = st.columns(3)
        m1.metric("Comprensión del problema", f"{evaluacion['comprension_problema']}/2")
        m2.metric("Aplicación conceptual", f"{evaluacion['aplicacion_conceptual']}/2")
        m3.metric("Razonamiento inmunológico", f"{evaluacion['razonamiento_inmunologico']}/2")

        m4, m5, m6 = st.columns(3)
        m4.metric("Hipótesis diagnóstica", f"{evaluacion['hipotesis_diagnostica']}/2")
        m5.metric("Fundamentación", f"{evaluacion['fundamentacion']}/2")
        m6.metric("Puntaje total", f"{evaluacion['puntaje_total']}/10")

        st.markdown("### Retroalimentación")
        st.write(evaluacion["feedback"])

        with st.expander("Ver respuesta modelo docente"):
            st.write(caso["model_answer"])

        st.caption(
            "Esta evaluación es automática y orientativa. Puede complementarse luego con revisión docente."
        )


# =========================================================
# MODO DOCENTE
# =========================================================
else:
    st.subheader("Panel docente")

    df = cargar_resultados()

    if df.empty:
        st.info("Todavía no hay respuestas registradas.")
    else:
        st.markdown("## Indicadores generales")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Respuestas", len(df))
        c2.metric("Promedio total", round(df["puntaje_total"].mean(), 2))
        c3.metric("Puntaje máximo", round(df["puntaje_total"].max(), 2))
        c4.metric("Puntaje mínimo", round(df["puntaje_total"].min(), 2))

        st.markdown("## Promedio por dimensión")
        resumen_dim = pd.DataFrame({
            "Dimensión": [
                "Comprensión del problema",
                "Aplicación conceptual",
                "Razonamiento inmunológico",
                "Hipótesis diagnóstica",
                "Fundamentación"
            ],
            "Promedio": [
                round(df["comprension_problema"].mean(), 2),
                round(df["aplicacion_conceptual"].mean(), 2),
                round(df["razonamiento_inmunologico"].mean(), 2),
                round(df["hipotesis_diagnostica"].mean(), 2),
                round(df["fundamentacion"].mean(), 2)
            ]
        })
        st.dataframe(resumen_dim, use_container_width=True)

        st.markdown("## Respuestas registradas")
        st.dataframe(df, use_container_width=True)

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            csv_data = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="Descargar resultados en CSV",
                data=csv_data,
                file_name="resultados_evaia_inmunologia.csv",
                mime="text/csv"
            )

        with col_dl2:
            excel_data = generar_excel(df)
            st.download_button(
                label="Descargar resultados en Excel",
                data=excel_data,
                file_name="resultados_evaia_inmunologia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with st.expander("Ver respuesta modelo del caso"):
            st.write(caso["model_answer"])
