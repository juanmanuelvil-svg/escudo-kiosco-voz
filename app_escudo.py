import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import tempfile
import os
from gtts import gTTS
import base64

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Kiosco Escudo Ciudadano", page_icon="🛡️", layout="centered")

# --- ESTILOS VISUALES EXTREMOS (Botones gigantes) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 100px;
        font-size: 24px;
        font-weight: bold;
        border-radius: 15px;
    }
    .big-icon { font-size: 50px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- SEGURIDAD ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("⚠️ Falta configurar la Llave API.")
    st.stop()

# --- BOTÓN DE AYUDA HUMANA (Siempre visible arriba) ---
if st.button("🆘 NECESITO AYUDA", type="primary", use_container_width=True):
    st.error("🚨 **ALERTA VISUAL:** POR FAVOR, UN ASESOR ACÉRQUESE A AYUDAR AL CIUDADANO.")
    st.stop()

st.markdown("<h1 style='text-align: center;'>🛡️ ESCUDO CIUDADANO</h1>", unsafe_allow_html=True)
st.divider()

# --- PASO 1: SELECCIÓN VISUAL (ICONOGRAFÍA EXTREMA) ---
st.markdown("### 1️⃣ ¿De qué se trata su problema? Toca un dibujo:")

if 'categoria' not in st.session_state:
    st.session_state['categoria'] = "General"

col1, col2 = st.columns(2)
with col1:
    if st.button("💧 Luz, Agua, Calles"): st.session_state['categoria'] = "Servicios Públicos (Luz, Agua, Calles)"
    if st.button("🏥 Salud y Médicos"): st.session_state['categoria'] = "Atención Médica y Salud"
with col2:
    if st.button("🚓 Multas y Policía"): st.session_state['categoria'] = "Seguridad, Multas y Policía"
    if st.button("🌾 Apoyo y Gobierno"): st.session_state['categoria'] = "Programas Sociales y Trámites"

st.success(f"✅ Tema seleccionado: **{st.session_state['categoria']}**")

# --- PASO 2: EL MICRÓFONO ÚNICO ---
st.markdown("### 2️⃣ Toca el micrófono. Dinos tu Nombre, de dónde eres y cuál es el problema:")
st.info("💡 Puedes hablar en tu propio idioma (Maya, Náhuatl, Zapoteco, etc.) o en Español.")

audio_grabado = st.audio_input("🎤 TOCA AQUÍ PARA HABLAR")

# --- FUNCIÓN PARA GENERAR WORD ---
def crear_word(texto_oficio):
    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Arial'
    estilo.font.size = Pt(12)
    for linea in texto_oficio.split('\n'):
        if linea.strip():
            p = doc.add_paragraph(linea.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    return archivo_memoria.getvalue()

# --- FUNCIÓN PARA QUE LA APP HABLE (Text to Speech) ---
def reproducir_audio(texto):
    tts = gTTS(text=texto, lang='es', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        with open(fp.name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
        os.remove(fp.name)

# --- LÓGICA DE IA ---
if audio_grabado:
    if st.button("🚀 HACER MI DOCUMENTO", use_container_width=True, type="primary"):
        with st.spinner("⏳ Escuchando y escribiendo... por favor espere..."):
            archivos_temporales = []
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Prompt doble: Queremos un resumen hablado y el oficio formal.
                prompt_texto = f"""
                ERES UN ABOGADO PRO BONO MEXICANO. Has recibido un audio de un ciudadano que requiere ayuda sobre: {st.session_state['categoria']}.
                El audio puede estar en español o lengua indígena. Extrae su nombre, dirección y el problema.
                
                Instrucciones estrictas:
                Genera tu respuesta separada por la palabra exacta "DIVISOR_K".
                
                PARTE 1 (Resumen para leer en voz alta al ciudadano):
                Escribe un texto muy breve, amable y en español simple, como si le hablaras a un abuelo. Diciendo: "Hola [Nombre], ya terminé su documento sobre [resumen del problema]. Por favor pida ayuda para imprimirlo."
                
                DIVISOR_K
                
                PARTE 2 (Oficio Legal):
                Redacta el oficio legal completo, fundamentado en leyes mexicanas. 
                REGLA DE ORO: Redactado SIEMPRE en PRIMERA PERSONA ("yo, comparezco por mi propio derecho"), firmado por el ciudadano. Si detectaste lengua indígena en el audio, invoca el Art. 2 Constitucional. Formato texto plano sin asteriscos.
                """
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                    t.write(audio_grabado.getvalue())
                    archivos_temporales.append(t.name)
                    audio_ia = genai.upload_file(t.name)
                
                respuesta = model.generate_content([audio_ia, prompt_texto])
                
                # Separar la respuesta de la IA
                partes = respuesta.text.split("DIVISOR_K")
                if len(partes) == 2:
                    resumen_hablado = partes[0].replace("*", "").strip()
                    oficio_formal = partes[1].replace("*", "").replace("#", "").strip()
                    
                    st.session_state['oficio'] = oficio_formal
                    st.session_state['resumen'] = resumen_hablado
                else:
                    st.error("No se pudo procesar correctamente. Pida ayuda.")
                    
            except Exception as e:
                st.error("❌ Ocurrió un error. Presione el botón de ayuda.")
            finally:
                for ruta in archivos_temporales:
                    if os.path.exists(ruta): os.remove(ruta)
        
        # Recargar para mostrar resultados
        st.rerun()

# --- MOSTRAR RESULTADOS Y REPRODUCIR VOZ ---
if 'oficio' in st.session_state:
    st.success("✅ ¡DOCUMENTO LISTO!")
    
    # Hacer que la aplicación hable (lee el resumen)
    reproducir_audio(st.session_state['resumen'])
    st.info(f"🔊 La computadora dice: *{st.session_state['resumen']}*")
    
    word_bytes = crear_word(st.session_state['oficio'])
    st.download_button("🖨️ DESCARGAR PARA IMPRIMIR", data=word_bytes, file_name="Documento_Ciudadano.docx", type="primary", use_container_width=True)
    
    with st.expander("👀 Ver el documento escrito"):
        st.text_area("Oficio:", value=st.session_state['oficio'], height=300)

    if st.button("🗑️ EMPEZAR DE NUEVO", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
