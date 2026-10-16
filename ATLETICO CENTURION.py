import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import base64
import gspread
from google.oauth2.service_account import Credentials

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONEXIÓN GSHEET
# ==========================================
st.set_page_config(
    page_title="Atlético Centurión - Finanzas & Club",
    page_icon="⚽",
    layout="wide"
)

if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False

@st.cache_resource
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Corrección automática de saltos de línea para evitar el error ValueError en private_key
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open("Finanzas Atletico Centurion")
    return sheet

def get_dataframe(sheet_name, columns):
    try:
        sh = conectar_google_sheets()
        ws = sh.worksheet(sheet_name)
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except Exception:
        return pd.DataFrame(columns=columns)

# Estilos CSS Personalizados
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .header-centurion {
        background: linear-gradient(135deg, #002B49 0%, #0A4B7C 100%);
        color: white; padding: 24px; border-radius: 16px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 43, 73, 0.25);
        border-bottom: 4px solid #00A3E0;
    }
    .header-centurion h1 { color: #FFFFFF !important; font-weight: 800; font-size: 2.2rem; margin: 0; }
    .header-centurion p { color: #E2E8F0; margin-top: 6px; font-size: 1.05rem; margin-bottom: 0; }
    .stButton>button {
        background-color: #002B49 !important; color: #FFFFFF !important;
        border-radius: 8px !important; font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] { color: #002B49 !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E8F0; border-radius: 8px 8px 0 0; padding: 8px 16px; color: #002B49; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #002B49 !important; color: #FFFFFF !important; }
    .footer-sponsors { background-color: #002B49; color: white; padding: 30px; border-radius: 16px; margin-top: 50px; text-align: center; border-top: 4px solid #00A3E0; }
    .sponsor-badge { background-color: #FFFFFF; color: #002B49; padding: 12px 20px; border-radius: 10px; font-weight: 700; display: inline-block; margin: 8px; border: 2px solid #E2E8F0; }
    .sponsor-badge span { display: block; font-size: 0.8rem; color: #64748B; font-weight: 400; }
    .comment-box { background-color: #F1F5F9; border-radius: 8px; padding: 10px 15px; margin-top: 8px; border-left: 3px solid #002B49; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES DE BASE DE DATOS (GOOGLE SHEETS)
# ==========================================
def obtener_auspiciadores():
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    return df.sort_values(by="nombre", ascending=True) if not df.empty and "nombre" in df.columns else df

def agregar_auspiciador(nombre, rubro, contacto):
    sh = conectar_google_sheets()
    ws = sh.worksheet("auspiciadores")
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    nuevo_id = 1
    if not df.empty and "id" in df.columns:
        ids = pd.to_numeric(df["id"], errors='coerce').dropna()
        if not ids.empty:
            nuevo_id = int(ids.max()) + 1
    ws.append_row([nuevo_id, str(nombre).strip(), str(rubro).strip(), str(contacto).strip()])

def eliminar_auspiciador(auspiciador_id):
    sh = conectar_google_sheets()
    ws = sh.worksheet("auspiciadores")
    cell = ws.find(str(int(auspiciador_id)))
    if cell:
        ws.delete_rows(cell.row)

def obtener_jugadores():
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo"])
    if not df.empty and "activo" in df.columns:
        df["activo"] = pd.to_numeric(df["activo"], errors='coerce').fillna(1)
        df = df[df["activo"] == 1]
        return df.sort_values(by="nombre", ascending=True) if "nombre" in df.columns else df
    return df

def agregar_jugador(nombre, dorsal, categoria):
    sh = conectar_google_sheets()
    ws = sh.worksheet("jugadores")
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo"])
    nuevo_id = 1
    if not df.empty and "id" in df.columns:
        ids = pd.to_numeric(df["id"], errors='coerce').dropna()
        if not ids.empty:
            nuevo_id = int(ids.max()) + 1
    ws.append_row([nuevo_id, str(nombre).strip(), str(dorsal).strip(), str(categoria), 1])

def eliminar_jugador(jugador_id):
    sh = conectar_google_sheets()
    ws = sh.worksheet("jugadores")
    cell = ws.find(str(int(jugador_id)))
    if cell:
        ws.update_cell(cell.row, 5, 0)

def registrar_pago_cuota(jugador_id, nombre_jugador, mes, anio, monto, fecha_pago):
    df_cuotas = get_dataframe("cuotas", ["id", "jugador_id", "mes", "anio", "monto", "fecha_pago"])
    if not df_cuotas.empty and "jugador_id" in df_cuotas.columns:
        df_cuotas["jugador_id"] = pd.to_numeric(df_cuotas["jugador_id"], errors='coerce')
        df_cuotas["mes"] = pd.to_numeric(df_cuotas["mes"], errors='coerce')
        df_cuotas["anio"] = pd.to_numeric(df_cuotas["anio"], errors='coerce')
        
        coincide = df_cuotas[(df_cuotas["jugador_id"] == int(jugador_id)) & (df_cuotas["mes"] == int(mes)) & (df_cuotas["anio"] == int(anio))]
        if not coincide.empty:
            return False, "Esta cuota ya se encuentra registrada para este jugador en este mes."

    sh = conectar_google_sheets()
    
    # 1. Guardar en pestaña cuotas
    ws_cuotas = sh.worksheet("cuotas")
    nuevo_id_c = 1
    if not df_cuotas.empty and "id" in df_cuotas.columns:
        ids_c = pd.to_numeric(df_cuotas["id"], errors='coerce').dropna()
        if not ids_c.empty:
            nuevo_id_c = int(ids_c.max()) + 1
            
    fecha_pago_str = fecha_pago.strftime("%Y-%m-%d") if hasattr(fecha_pago, "strftime") else str(fecha_pago)
    ws_cuotas.append_row([nuevo_id_c, int(jugador_id), int(mes), int(anio), float(monto), fecha_pago_str])
    
    # 2. Guardar en pestaña movimientos
    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    detalle = f"Cuota {meses_nombre[mes - 1]} {anio} - {nombre_jugador}"
    
    ws_mov = sh.worksheet("movimientos")
    df_mov = get_dataframe("movimientos", ["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    
    nuevo_id_m = 1
    if not df_mov.empty and "id" in df_mov.columns:
        ids_m = pd.to_numeric(df_mov["id"], errors='coerce').dropna()
        if not ids_m.empty:
            nuevo_id_m = int(ids_m.max()) + 1
            
    ws_mov.append_row([nuevo_id_m, "Cuota Jugador", "Ingreso", float(monto), fecha_pago_str, str(detalle), str(nombre_jugador)])
    
    return True, "Pago de cuota registrado exitosamente."

def registrar_egreso(tipo_egreso, monto, fecha, detalle, responsable="Directiva"):
    sh = conectar_google_sheets()
    ws = sh.worksheet("movimientos")
    df_mov = get_dataframe("movimientos", ["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    
    nuevo_id = 1
    if not df_mov.empty and "id" in df_mov.columns:
        ids_validos = pd.to_numeric(df_mov["id"], errors='coerce').dropna()
        if not ids_validos.empty:
            nuevo_id = int(ids_validos.max()) + 1
            
    fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)
    
    ws.append_row([
        nuevo_id, 
        str(tipo_egreso), 
        "Egreso", 
        float(monto), 
        fecha_str, 
        str(detalle), 
        str(responsable)
    ])

def obtener_movimientos():
    df = get_dataframe("movimientos", ["id", "fecha", "tipo", "subtipo", "monto", "detalle", "responsable"])
    if not df.empty and "monto" in df.columns:
        df["monto"] = pd.to_numeric(df["monto"], errors='coerce').fillna(0)
        return df.sort_values(by="id", ascending=False)
    return df

def calcular_resumen():
    df_mov = obtener_movimientos()
    if not df_mov.empty and "subtipo" in df_mov.columns and "monto" in df_mov.columns:
        ingresos = df_mov[df_mov["subtipo"] == "Ingreso"]["monto"].sum()
        egresos = df_mov[df_mov["subtipo"] == "Egreso"]["monto"].sum()
        return float(ingresos), float(egresos), float(ingresos - egresos)
    return 0.0, 0.0, 0.0

def obtener_estado_cuotas(mes, anio):
    df_jugs = obtener_jugadores()
    df_cuotas = get_dataframe("cuotas", ["id", "jugador_id", "mes", "anio", "monto", "fecha_pago"])
    
    if df_jugs.empty:
        return pd.DataFrame(columns=["id", "nombre", "categoria", "estado", "fecha_pago", "monto"])
        
    if not df_cuotas.empty and "jugador_id" in df_cuotas.columns:
        df_cuotas["jugador_id"] = pd.to_numeric(df_cuotas["jugador_id"], errors='coerce')
        df_cuotas["mes"] = pd.to_numeric(df_cuotas["mes"], errors='coerce')
        df_cuotas["anio"] = pd.to_numeric(df_cuotas["anio"], errors='coerce')
        df_c_filtro = df_cuotas[(df_cuotas["mes"] == int(mes)) & (df_cuotas["anio"] == int(anio))]
    else:
        df_c_filtro = pd.DataFrame(columns=["jugador_id", "fecha_pago", "monto"])
        
    merged = pd.merge(df_jugs, df_c_filtro, left_on="id", right_on="jugador_id", how="left")
    merged["estado"] = merged["fecha_pago"].apply(lambda x: "PAGADO" if pd.notnull(x) and str(x).strip() != "" else "PENDIENTE")
    return merged[["id", "nombre", "categoria", "estado", "fecha_pago", "monto"]].sort_values(by="nombre", ascending=True)

# NOTICIAS Y COMENTARIOS
def agregar_noticia(titulo, contenido, imagen_bytes, autor="Directiva"):
    sh = conectar_google_sheets()
    ws = sh.worksheet("noticias")
    df = get_dataframe("noticias", ["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    nuevo_id = 1
    if not df.empty and "id" in df.columns:
        ids = pd.to_numeric(df["id"], errors='coerce').dropna()
        if not ids.empty:
            nuevo_id = int(ids.max()) + 1
    img_b64 = base64.b64encode(imagen_bytes).decode('utf-8') if imagen_bytes else ""
    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    ws.append_row([nuevo_id, str(titulo).strip(), str(contenido).strip(), img_b64, fecha_act, str(autor).strip()])

def obtener_noticias():
    df = get_dataframe("noticias", ["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    return df.sort_values(by="id", ascending=False) if not df.empty and "id" in df.columns else df

def eliminar_noticia(noticia_id):
    sh = conectar_google_sheets()
    ws = sh.worksheet("noticias")
    cell = ws.find(str(int(noticia_id)))
    if cell:
        ws.delete_rows(cell.row)

def agregar_comentario(noticia_id, nombre_autor, comentario):
    sh = conectar_google_sheets()
    ws = sh.worksheet("comentarios")
    df = get_dataframe("comentarios", ["id", "noticia_id", "nombre_autor", "comentario", "fecha"])
    nuevo_id = 1
    if not df.empty and "id" in df.columns:
        ids = pd.to_numeric(df["id"], errors='coerce').dropna()
        if not ids.empty:
            nuevo_id = int(ids.max()) + 1
    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    ws.append_row([nuevo_id, int(noticia_id), str(nombre_autor).strip(), str(comentario).strip(), fecha_act])

def obtener_comentarios(noticia_id):
    df = get_dataframe("comentarios", ["id", "noticia_id", "nombre_autor", "comentario", "fecha"])
    if not df.empty and "noticia_id" in df.columns:
        df["noticia_id"] = pd.to_numeric(df["noticia_id"], errors='coerce')
        return df[df["noticia_id"] == int(noticia_id)].sort_values(by="id", ascending=True)
    return df

# GENERADOR DE REPORTES PDF CON REPORTLAB
def generar_pdf_informe(mes_nombre, anio, ingresos_tot, egresos_tot, saldo_actual, df_estado, df_mov):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#002B49")
    secondary_color = colors.HexColor("#00A3E0")
    light_bg = colors.HexColor("#F1F5F9")
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=primary_color, alignment=1, spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, textColor=colors.HexColor("#475569"), alignment=1, spaceAfter=15)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=primary_color, spaceBefore=12, spaceAfter=6)
    cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=10)
    cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11)
    
    story = []
    story.append(Paragraph("CLUB DEPORTIVO ATLÉTICO CENTURIÓN", title_style))
    story.append(Paragraph(f"INFORME FINANCIERO Y ESTADO DE CUOTAS — {mes_nombre.upper()} {anio}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_color, spaceAfter=15))
    
    story.append(Paragraph("1. Resumen Ejecutivo de Saldos", h2_style))
    met_data = [
        [Paragraph("<b>Total Ingresos Recaudados</b>", cell_style), Paragraph("<b>Total Egresos (Gastos)</b>", cell_style), Paragraph("<b>Saldo Líquido Disponible</b>", cell_style)],
        [Paragraph(f"<font color='#059669'><b>+ ${ingresos_tot:,.0f}</b></font>".replace(",", "."), cell_bold), Paragraph(f"<font color='#DC2626'><b>- ${egresos_tot:,.0f}</b></font>".replace(",", "."), cell_bold), Paragraph(f"<font color='#002B49'><b>${saldo_actual:,.0f}</b></font>".replace(",", "."), cell_bold)]
    ]
    met_table = Table(met_data, colWidths=[180, 180, 180])
    met_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), light_bg), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(met_table)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"2. Estado de Cuotas de Jugadores — {mes_nombre} {anio}", h2_style))
    total_jug = len(df_estado) if df_estado is not None else 0
    pagados_cnt = len(df_estado[df_estado['estado'] == 'PAGADO']) if df_estado is not None and not df_estado.empty else 0
    deudores_cnt = total_jug - pagados_cnt
    
    story.append(Paragraph(f"<b>Total Plantel:</b> {total_jug} | <b>Al Día (Pagados):</b> {pagados_cnt} | <b>Deudores (Pendientes):</b> {deudores_cnt}", cell_style))
    story.append(Spacer(1, 6))
    
    if df_estado is not None and not df_estado.empty:
        cuotas_data = [[Paragraph("<font color='white'><b>Jugador</b></font>", cell_style), Paragraph("<font color='white'><b>Categoría</b></font>", cell_style), Paragraph("<font color='white'><b>Estado</b></font>", cell_style), Paragraph("<font color='white'><b>Fecha Pago</b></font>", cell_style), Paragraph("<font color='white'><b>Monto ($)</b></font>", cell_style)]]
        for _, r in df_estado.iterrows():
            st_color = "#059669" if r['estado'] == 'PAGADO' else "#DC2626"
            f_pago = r['fecha_pago'] if pd.notnull(r['fecha_pago']) and str(r['fecha_pago']).strip() != "" else "-"
            monto_val = f"${float(r['monto']):,.0f}".replace(",", ".") if pd.notnull(r['monto']) and str(r['monto']).strip() != "" and float(r['monto']) > 0 else "$0"
            cuotas_data.append([Paragraph(str(r['nombre']), cell_style), Paragraph(str(r['categoria']), cell_style), Paragraph(f"<font color='{st_color}'><b>{r['estado']}</b></font>", cell_style), Paragraph(str(f_pago), cell_style), Paragraph(monto_val, cell_style)])
            
        cuotas_table = Table(cuotas_data, colWidths=[160, 110, 90, 90, 90])
        cuotas_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), primary_color), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])]))
        story.append(cuotas_table)
    else:
        story.append(Paragraph("No hay registro de jugadores en el sistema.", cell_style))
        
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("3. Historial de Gastos y Compras del Club", h2_style))
    if df_mov is not None and not df_mov.empty and "subtipo" in df_mov.columns:
        df_egr = df_mov[df_mov['subtipo'] == 'Egreso']
        if not df_egr.empty:
            egr_data = [[Paragraph("<font color='white'><b>Fecha</b></font>", cell_style), Paragraph("<font color='white'><b>Tipo</b></font>", cell_style), Paragraph("<font color='white'><b>Detalle / Concepto</b></font>", cell_style), Paragraph("<font color='white'><b>Monto ($)</b></font>", cell_style)]]
            for _, r in df_egr.iterrows():
                egr_data.append([Paragraph(str(r['fecha']), cell_style), Paragraph(str(r['tipo']), cell_style), Paragraph(str(r['detalle']), cell_style), Paragraph(f"- ${float(r['monto']):,.0f}".replace(",", "."), cell_style)])
            
            egr_table = Table(egr_data, colWidths=[75, 95, 270, 100])
            egr_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), primary_color), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])]))
            story.append(egr_table)
        else:
            story.append(Paragraph("No existen registros de gastos/egresos.", cell_style))
    else:
        story.append(Paragraph("No existen registros de movimientos.", cell_style))
        
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<i>Informe emitido automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M hrs')} por la Directiva del Club Deportivo Atlético Centurión.</i>", ParagraphStyle('Foot', parent=styles['Italic'], fontSize=8, textColor=colors.HexColor("#64748B"))))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 3. ENCABEZADO INSTITUCIONAL Y LOGO
# ==========================================
col_header1, col_header2 = st.columns([1, 5])
logo_path = "logo_centurion.png" if os.path.exists("logo_centurion.png") else "logo.png"

with col_header1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=130)
    else:
        st.markdown('<div style="background-color: #002B49; color: white; width: 110px; height: 110px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: bold; border: 4px solid #00A3E0;">AC</div>', unsafe_allow_html=True)

with col_header2:
    st.markdown('<div class="header-centurion"><h1>CLUB DEPORTIVO ATLÉTICO CENTURIÓN</h1><p>🔵⚪ Sistema Transparente de Control Financiero & Comunidad (Google Sheets Cloud) ⚪🔵</p></div>', unsafe_allow_html=True)

# GESTIÓN DE SESIÓN EN SIDEBAR
st.sidebar.header("🔐 Acceso al Sistema")
if not st.session_state["es_admin"]:
    rol = st.sidebar.radio("Modalidad de Vista:", ["👁️ Transparencia Pública (Ver Datos)", "🔑 Administración"])
    if rol == "🔑 Administración":
        with st.sidebar.form("form_login"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Ingresar")
            if btn_login:
                if usuario == "admin" and clave == "centurion2026":
                    st.session_state["es_admin"] = True
                    st.sidebar.success("Acceso Concedido")
                    st.rerun()
                else:
                    st.sidebar.error("Usuario o contraseña incorrectos.")
else:
    st.sidebar.success("🟢 Sesión de Administrador Activa")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["es_admin"] = False
        st.rerun()

es_admin = st.session_state["es_admin"]

ingresos_tot, egresos_tot, saldo_actual = calcular_resumen()
st.sidebar.divider()
st.sidebar.metric(label="💰 SALDO TOTAL DISPONIBLE", value=f"${saldo_actual:,.0f}".replace(",", "."))

# Pestañas Principales
tab_noticias, tab_cartola, tab_cuotas, tab_arbitros, tab_compras, tab_jugadores, tab_pdf, tab_admin_ausp = st.tabs([
    "📰 Noticias & Club", "📜 Cartola Bancaria", "👟 Cuotas Mensuales", "🏁 Pago a Árbitros", "🛒 Compras del Club", "👥 Plantel de Jugadores", "📄 Descargar Informe PDF", "🤝 Auspiciadores"
])

# TAB 1: NOTICIAS
with tab_noticias:
    st.subheader("📰 Novedades y Muro del Club Atlético Centurión")
    if es_admin:
        with st.expander("➕ Publicar Nueva Noticia / Foto del Partido", expanded=False):
            with st.form("form_nueva_noticia", clear_on_submit=True):
                tit_noticia = st.text_input("Título de la Noticia:")
                autor_noticia = st.text_input("Firma / Autor:", value="Directiva Atlético Centurión")
                foto_noticia = st.file_uploader("Subir Foto (.jpg, .png):", type=["jpg", "jpeg", "png"])
                cont_noticia = st.text_area("Contenido / Detalle de la Noticia:")
                btn_pub = st.form_submit_button("📣 Publicar Noticia")
                if btn_pub:
                    if tit_noticia.strip() and cont_noticia.strip():
                        img_bytes = foto_noticia.getvalue() if foto_noticia is not None else None
                        agregar_noticia(tit_noticia, cont_noticia, img_bytes, autor_noticia)
                        st.toast("Noticia publicada exitosamente.", icon="🎉")
                        st.rerun()
                    else:
                        st.error("Debes ingresar un título y contenido.")

    df_noticias = obtener_noticias()
    if not df_noticias.empty:
        for _, n in df_noticias.iterrows():
            noticia_id = int(n['id'])
            st.markdown(f"### ⚽ {n['titulo']}")
            st.caption(f"📅 Publicado el {n['fecha']} por **{n['autor']}**")
            
            if pd.notnull(n['imagen_b64']) and str(n['imagen_b64']).strip() != "":
                try:
                    img_data = base64.b64decode(n['imagen_b64'])
                    st.image(img_data, use_container_width=True)
                except Exception:
                    pass
            
            st.write(n['contenido'])
            if es_admin:
                if st.button(f"🗑️ Eliminar Noticia N° {noticia_id}", key=f"del_not_{noticia_id}"):
                    eliminar_noticia(noticia_id)
                    st.toast("Noticia eliminada.", icon="🗑️")
                    st.rerun()
            
            st.markdown("##### 💬 Comentarios de la Hinchada y Plantel")
            df_coment = obtener_comentarios(noticia_id)
            if not df_coment.empty:
                for _, c in df_coment.iterrows():
                    st.markdown(f'<div class="comment-box"><b>👤 {c["nombre_autor"]}</b> <small style="color:#64748B;">({c["fecha"]})</small><br><span>{c["comentario"]}</span></div>', unsafe_allow_html=True)
            else:
                st.info("Aún no hay comentarios. ¡Sé el primero en opinar!")
            
            with st.expander(f"✍️ Comentar en '{n['titulo']}'", expanded=False):
                with st.form(key=f"form_comentario_{noticia_id}", clear_on_submit=True):
                    nombre_com = st.text_input("Tu Nombre / Apodo (Obligatorio):", key=f"nom_com_{noticia_id}")
                    texto_com = st.text_area("Escribe tu comentario:", key=f"txt_com_{noticia_id}")
                    btn_coment = st.form_submit_button("💬 Enviar Comentario")
                    if btn_coment:
                        if nombre_com.strip() and texto_com.strip():
                            agregar_comentario(noticia_id, nombre_com, texto_com)
                            st.toast("¡Comentario enviado!", icon="💬")
                            st.rerun()
                        else:
                            st.error("Ingresa tu nombre y comentario para poder enviar.")
            st.divider()
    else:
        st.info("No hay noticias publicadas por el momento.")

# TAB 2: CARTOLA
with tab_cartola:
    st.subheader("📜 Cartola Financiera del Club")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ingresos", f"${ingresos_tot:,.0f}".replace(",", "."))
    c2.metric("Total Egresos", f"${egresos_tot:,.0f}".replace(",", "."))
    c3.metric("Saldo Líquido", f"${saldo_actual:,.0f}".replace(",", "."))
    st.divider()
    
    df_mov = obtener_movimientos()
    if not df_mov.empty and "subtipo" in df_mov.columns and "monto" in df_mov.columns:
        df_display = df_mov.copy()
        df_display["Monto ($)"] = df_display.apply(lambda r: f"+ ${float(r['monto']):,.0f}".replace(",", ".") if r['subtipo'] == 'Ingreso' else f"- ${float(r['monto']):,.0f}".replace(",", "."), axis=1)
        st.dataframe(df_display[['fecha', 'tipo', 'subtipo', 'Monto ($)', 'detalle', 'responsable']], use_container_width=True)
    else:
        st.info("Aún no hay movimientos registrados.")

# TAB 3: CUOTAS
with tab_cuotas:
    st.subheader("👟 Control de Cuotas Mensuales")
    col_mes, col_anio = st.columns(2)
    meses_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    mes_sel = col_mes.selectbox("Seleccionar Mes:", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=datetime.now().month - 1)
    anio_sel = col_anio.number_input("Año:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    if es_admin:
        with st.expander("➕ Registrar Pago de Cuota", expanded=True):
            df_jugs = obtener_jugadores()
            if not df_jugs.empty and "nombre" in df_jugs.columns:
                col_j1, col_j2, col_j3 = st.columns(3)
                jugador_sel = col_j1.selectbox("Seleccionar Jugador:", df_jugs["nombre"].tolist())
                monto_cuota = col_j2.number_input("Monto Cuota ($):", min_value=1000, value=5000, step=1000)
                fecha_cuota = col_j3.date_input("Fecha de Pago:", datetime.now())
                
                if st.button("💰 Registrar Pago de Cuota"):
                    jugador_id = int(df_jugs[df_jugs["nombre"] == jugador_sel]["id"].values[0])
                    exito, msg = registrar_pago_cuota(jugador_id, jugador_sel, mes_sel, anio_sel, monto_cuota, fecha_cuota)
                    if exito:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Primero debes inscribir jugadores en la pestaña 'Plantel de Jugadores'.")

    st.write(f"### Estado de Pagos - {meses_dict[mes_sel]} {anio_sel}")
    df_estado = obtener_estado_cuotas(mes_sel, anio_sel)
    if not df_estado.empty and "estado" in df_estado.columns:
        df_estado["Estado Visual"] = df_estado["estado"].apply(lambda x: "✅ PAGADO" if x == "PAGADO" else "❌ PENDIENTE")
        st.dataframe(df_estado[["nombre", "categoria", "Estado Visual", "fecha_pago", "monto"]], use_container_width=True)
    else:
        st.info("No hay jugadores ingresados.")

# TAB 4: ÁRBITROS
with tab_arbitros:
    st.subheader("🏁 Control de Pago a Árbitros")
    if es_admin:
        with st.form("form_arbitros", clear_on_submit=True):
            col_a1, col_a2 = st.columns(2)
            monto_arb = col_a1.number_input("Monto Pagado ($):", min_value=1000, value=25000, step=1000)
            fecha_arb = col_a2.date_input("Fecha del Partido:", datetime.now())
            rival = st.text_input("Partido / Rival:", placeholder="Ej: vs Deportivo Sur")
            detalle_arb = st.text_input("Detalle:", placeholder="Ej: Pago terna arbitral fecha 5")
            if st.form_submit_button("🚨 Registrar Pago y Descontar del Saldo"):
                concepto = f"Arbitraje: {rival} ({detalle_arb})" if detalle_arb else f"Arbitraje: {rival}"
                registrar_egreso("Pago Árbitros", monto_arb, fecha_arb, concepto, "Tesorería")
                st.toast(f"Pago de ${monto_arb:,.0f} registrado.", icon="⚽")
                st.rerun()

    st.write("### Historial de Pagos a Árbitros")
    df_mov_all = obtener_movimientos()
    if not df_mov_all.empty and "tipo" in df_mov_all.columns:
        df_arb = df_mov_all[df_mov_all["tipo"] == "Pago Árbitros"]
        if not df_arb.empty:
            st.dataframe(df_arb[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 5: COMPRAS
with tab_compras:
    st.subheader("🛒 Compras e Inversiones del Club")
    if es_admin:
        with st.form("form_compras", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            monto_compra = col_c1.number_input("Monto de la Compra ($):", min_value=1000, value=15000, step=1000)
            fecha_compra = col_c2.date_input("Fecha de Compra:", datetime.now())
            concepto_compra = st.text_input("Detalle de la Compra:", placeholder="Ej: 3 Balones N°5, botiquín")
            comprobante = st.text_input("N° Boleta / Factura:", placeholder="Ej: Boleta N° 45812")
            if st.form_submit_button("🛒 Registrar Compra y Descontar del Saldo"):
                detalle_compra = f"Compra: {concepto_compra} [{comprobante}]" if comprobante else f"Compra: {concepto_compra}"
                registrar_egreso("Compra Club", monto_compra, fecha_compra, detalle_compra, "Tesorería")
                st.toast(f"Compra de ${monto_compra:,.0f} registrada.", icon="🛒")
                st.rerun()

    st.write("### Historial de Compras")
    if not df_mov_all.empty and "tipo" in df_mov_all.columns:
        df_comp = df_mov_all[df_mov_all["tipo"] == "Compra Club"]
        if not df_comp.empty:
            st.dataframe(df_comp[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 6: JUGADORES
with tab_jugadores:
    st.subheader("👥 Plantel de Jugadores")
    if es_admin:
        col_j_add, col_j_del = st.columns(2)
        with col_j_add:
            st.markdown("#### ➕ Inscribir Nuevo Jugador")
            with st.form("form_nuevo_jugador", clear_on_submit=True):
                nom_jugador = st.text_input("Nombre Completo:")
                dorsal_jugador = st.text_input("Dorsal o RUT:")
                cat_jugador = st.selectbox("Categoría:", ["Adulto / Serie Honor", "Seniors", "Super Seniors", "Juvenil", "Femenino"])
                btn_add_j = st.form_submit_button("Guardar Jugador")
                if btn_add_j:
                    if nom_jugador.strip():
                        agregar_jugador(nom_jugador, dorsal_jugador, cat_jugador)
                        st.toast(f"Jugador '{nom_jugador}' inscrito exitosamente.", icon="🎉")
                        st.rerun()
                    else:
                        st.error("Debes ingresar al menos el nombre del jugador.")

        with col_j_del:
            st.markdown("#### ❌ Eliminar / Dar de Baja Jugador")
            df_plantel_actual = obtener_jugadores()
            if not df_plantel_actual.empty and "nombre" in df_plantel_actual.columns:
                jugador_del_nombre = st.selectbox("Seleccionar Jugador a Eliminar:", df_plantel_actual["nombre"].tolist(), key="select_del_jugador")
                if st.button("🗑️ Eliminar Jugador Seleccionado", key="btn_del_jugador"):
                    jug_id = int(df_plantel_actual[df_plantel_actual["nombre"] == jugador_del_nombre]["id"].values[0])
                    eliminar_jugador(jug_id)
                    st.toast(f"Jugador '{jugador_del_nombre}' dado de baja.", icon="🗑️")
                    st.rerun()
            else:
                st.info("No hay jugadores registrados para eliminar.")

    df_plantel = obtener_jugadores()
    st.write(f"**Total Jugadores Activos:** {len(df_plantel)}")
    if not df_plantel.empty and "nombre" in df_plantel.columns:
        st.dataframe(df_plantel[["nombre", "dorsal_o_rut", "categoria"]], use_container_width=True)

# TAB 7: GENERAR E IMPRIMIR PDF
with tab_pdf:
    st.subheader("📄 Generación de Informe Financiero Oficial (PDF)")
    st.write("Genera un documento PDF oficial descargable e imprimible con las estadísticas de gastos, cuotas de jugadores al día y deudores.")
    
    col_pdf_m, col_pdf_a = st.columns(2)
    mes_pdf_num = col_pdf_m.selectbox("Mes del Informe PDF:", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=datetime.now().month - 1)
    anio_pdf_val = col_pdf_a.number_input("Año del Informe PDF:", min_value=2024, max_value=2030, value=datetime.now().year, key="anio_pdf_input")
    
    df_est_pdf = obtener_estado_cuotas(mes_pdf_num, anio_pdf_val)
    df_mov_pdf = obtener_movimientos()
    ing_p, egr_p, sal_p = calcular_resumen()
    
    st.divider()
    p1, p2, p3 = st.columns(3)
    p1.metric("Ingresos Totales", f"${ing_p:,.0f}".replace(",", "."))
    p2.metric("Egresos Totales", f"${egr_p:,.0f}".replace(",", "."))
    p3.metric("Saldo Disponible", f"${sal_p:,.0f}".replace(",", "."))
    
    if not df_est_pdf.empty and "estado" in df_est_pdf.columns:
        total_p = len(df_est_pdf)
        al_dia = len(df_est_pdf[df_est_pdf['estado'] == 'PAGADO'])
        deudores = total_p - al_dia
        st.info(f"📊 **Resumen Plantel {meses_dict[mes_pdf_num]} {anio_pdf_val}:** Total Jugadores: {total_p} | ✅ Al día: {al_dia} | ❌ Deudores: {deudores}")
    
    pdf_bytes = generar_pdf_informe(
        mes_nombre=meses_dict[mes_pdf_num],
        anio=anio_pdf_val,
        ingresos_tot=ing_p,
        egresos_tot=egr_p,
        saldo_actual=sal_p,
        df_estado=df_est_pdf,
        df_mov=df_mov_pdf
    )
    
    st.download_button(
        label=f"📥 Descargar Informe PDF ({meses_dict[mes_pdf_num]} {anio_pdf_val})",
        data=pdf_bytes,
        file_name=f"Informe_Financiero_Atletico_Centurion_{meses_dict[mes_pdf_num]}_{anio_pdf_val}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# TAB 8: GESTIÓN DE AUSPICIADORES
with tab_admin_ausp:
    st.subheader("🤝 Gestión de Auspiciadores del Club")
    if es_admin:
        col_aus_add, col_aus_del = st.columns(2)
        with col_aus_add:
            st.markdown("#### ➕ Agregar Nuevo Auspiciador")
            with st.form("form_nuevo_auspiciador", clear_on_submit=True):
                aus_nombre = st.text_input("Nombre de la Empresa / Marca:")
                aus_rubro = st.text_input("Rubro / Tipo de Apoyo:")
                aus_contacto = st.text_input("Contacto / Detalle:")
                btn_add_ausp = st.form_submit_button("Guardar Auspiciador")
                if btn_add_ausp:
                    if aus_nombre.strip():
                        agregar_auspiciador(aus_nombre, aus_rubro, aus_contacto)
                        st.toast(f"Auspiciador '{aus_nombre}' agregado con éxito.", icon="🎉")
                        st.rerun()
                    else:
                        st.error("Ingresa el nombre del auspiciador.")

        with col_aus_del:
            st.markdown("#### ❌ Eliminar Auspiciador")
            df_ausp_actual = obtener_auspiciadores()
            if not df_ausp_actual.empty and "nombre" in df_ausp_actual.columns:
                aus_eliminar_nombre = st.selectbox("Seleccionar Auspiciador a Eliminar:", df_ausp_actual["nombre"].tolist(), key="select_del_ausp")
                if st.button("🗑️ Eliminar Auspiciador Seleccionado", key="btn_del_ausp"):
                    aus_id = int(df_ausp_actual[df_ausp_actual["nombre"] == aus_eliminar_nombre]["id"].values[0])
                    eliminar_auspiciador(aus_id)
                    st.toast(f"Auspiciador '{aus_eliminar_nombre}' eliminado.", icon="🗑️")
                    st.rerun()
            else:
                st.info("No hay auspiciadores para eliminar.")

    df_ausp = obtener_auspiciadores()
    if not df_ausp.empty and "nombre" in df_ausp.columns:
        st.dataframe(df_ausp[["nombre", "rubro", "contacto"]], use_container_width=True)

# FOOTER
st.markdown("---")
df_ausp_footer = obtener_auspiciadores()
sponsors_html = '<div class="footer-sponsors"><h3>🤝 NUESTROS AUSPICIADORES Y PATROCINADORES</h3><p>Agradecemos el constante apoyo al Club Deportivo Atlético Centurión</p><div style="margin-top: 15px;">'
if not df_ausp_footer.empty and "nombre" in df_ausp_footer.columns:
    for _, row in df_ausp_footer.iterrows():
        sponsors_html += f'<div class="sponsor-badge">⭐ {row["nombre"]} <span>{row["rubro"]}</span></div>'
else:
    sponsors_html += '<div class="sponsor-badge">Espacio Disponible <span>Sé nuestro auspiciador</span></div>'
sponsors_html += '</div></div>'
st.markdown(sponsors_html, unsafe_allow_html=True)