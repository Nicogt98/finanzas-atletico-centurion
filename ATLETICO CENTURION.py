import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import base64

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Atlético Centurión - Finanzas & Club",
    page_icon="⚽",
    layout="wide"
)

# Inicializar sesión de administrador de forma segura
if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False

DB_FILES = {
    "jugadores": "jugadores.csv",
    "movimientos": "movimientos.csv",
    "cuotas": "cuotas.csv",
    "noticias": "noticias.csv",
    "comentarios": "comentarios.csv",
    "auspiciadores": "auspiciadores.csv",
    "configuracion": "configuracion.csv"
}

def get_dataframe(sheet_name, columns):
    filename = DB_FILES.get(sheet_name, f"{sheet_name}.csv")
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            if df.empty:
                return pd.DataFrame(columns=columns)
            return df
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
        return df

def save_dataframe(sheet_name, df):
    filename = DB_FILES.get(sheet_name, f"{sheet_name}.csv")
    df.to_csv(filename, index=False)

def obtener_config():
    df = get_dataframe("configuracion", ["clave", "valor"])
    config = {
        "bg_color": "#F8FAFC",
        "logo_b64": "",
        "banner_titulo": "CLUB DEPORTIVO ATLÉTICO CENTURIÓN"
    }
    if not df.empty and "clave" in df.columns:
        for _, r in df.iterrows():
            config[str(r["clave"])] = str(r["valor"])
    return config

def guardar_config(clave, valor):
    df = get_dataframe("configuracion", ["clave", "valor"])
    if not df.empty and "clave" in df.columns:
        df = df[df["clave"] != clave]
    nuevo = pd.DataFrame([[clave, str(valor)]], columns=["clave", "valor"])
    df = pd.concat([df, nuevo], ignore_index=True)
    save_dataframe("configuracion", df)

cfg = obtener_config()

# Estilos CSS Dinámicos
st.markdown(f"""
    <style>
    .stApp {{ background-color: {cfg.get("bg_color", "#F8FAFC")}; }}
    .header-centurion {{
        background: linear-gradient(135deg, #002B49 0%, #0A4B7C 100%);
        color: white; padding: 24px; border-radius: 16px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 43, 73, 0.25);
        border-bottom: 4px solid #00A3E0;
    
    .header-centurion h1 {{ color: #FFFFFF !important; font-weight: 800; font-size: 2.2rem; margin: 0; }}
    .header-centurion p {{ color: #E2E8F0; margin-top: 6px; font-size: 1.05rem; margin-bottom: 0; }}
    .stButton>button {{
        background-color: #002B49 !important; color: #FFFFFF !important;
        border-radius: 8px !important; font-weight: 600 !important;
    
    div[data-testid="stMetricValue"] {{ color: #002B49 !important; font-weight: 700; }}
    .stTabs [data-baseweb="tab"] {{ background-color: #E2E8F0; border-radius: 8px 8px 0 0; padding: 8px 16px; color: #002B49; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ background-color: #002B49 !important; color: #FFFFFF !important; }}
    .footer-sponsors {{ background-color: #002B49; color: white; padding: 30px; border-radius: 16px; margin-top: 50px; text-align: center; border-top: 4px solid #00A3E0; }}
    .sponsor-badge {{ background-color: #FFFFFF; color: #002B49; padding: 12px 20px; border-radius: 10px; font-weight: 700; display: inline-block; margin: 8px; border: 2px solid #E2E8F0; }}
    .sponsor-badge span {{ display: block; font-size: 0.8rem; color: #64748B; font-weight: 400; }}
    .comment-box {{ background-color: #F1F5F9; border-radius: 8px; padding: 10px 15px; margin-top: 8px; border-left: 3px solid #002B49; color: #1E293B; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES DE NEGOCIO Y DATOS
# ==========================================
def obtener_jugadores():
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64"])
    if not df.empty and "activo" in df.columns:
        df["activo"] = pd.to_numeric(df["activo"], errors='coerce').fillna(1)
        df = df[df["activo"] == 1]
        return df.sort_values(by="nombre", ascending=True) if "nombre" in df.columns else df
    return df

def agregar_jugador(nombre, dorsal, categoria, foto_bytes):
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64"])
    nuevo_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns and not df["id"].dropna().empty else 1
    foto_b64 = base64.b64encode(foto_bytes).decode('utf-8') if foto_bytes else ""
    nuevo_reg = pd.DataFrame([[nuevo_id, str(nombre).strip(), str(dorsal).strip(), str(categoria), 1, foto_b64]], columns=["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64"])
    df = pd.concat([df, nuevo_reg], ignore_index=True)
    save_dataframe("jugadores", df)

def eliminar_jugador(jugador_id):
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64"])
    if not df.empty and "id" in df.columns:
        df.loc[df["id"].astype(int) == int(jugador_id), "activo"] = 0
        save_dataframe("jugadores", df)

def registrar_pago_cuota(jugador_id, nombre_jugador, mes, anio, monto, fecha_pago):
    df_cuotas = get_dataframe("cuotas", ["id", "jugador_id", "mes", "anio", "monto", "fecha_pago"])
    if not df_cuotas.empty and "jugador_id" in df_cuotas.columns:
        df_cuotas["jugador_id"] = pd.to_numeric(df_cuotas["jugador_id"], errors='coerce')
        df_cuotas["mes"] = pd.to_numeric(df_cuotas["mes"], errors='coerce')
        df_cuotas["anio"] = pd.to_numeric(df_cuotas["anio"], errors='coerce')
        
        coincide = df_cuotas[(df_cuotas["jugador_id"] == int(jugador_id)) & (df_cuotas["mes"] == int(mes)) & (df_cuotas["anio"] == int(anio))]
        if not coincide.empty:
            return False, "Esta cuota ya se encuentra registrada para este jugador en este mes."

    fecha_pago_str = fecha_pago.strftime("%Y-%m-%d") if hasattr(fecha_pago, "strftime") else str(fecha_pago)
    
    nuevo_id_c = int(df_cuotas["id"].max()) + 1 if not df_cuotas.empty and "id" in df_cuotas.columns and not df_cuotas["id"].dropna().empty else 1
    nueva_c = pd.DataFrame([[nuevo_id_c, int(jugador_id), int(mes), int(anio), float(monto), fecha_pago_str]], columns=["id", "jugador_id", "mes", "anio", "monto", "fecha_pago"])
    df_cuotas = pd.concat([df_cuotas, nueva_c], ignore_index=True)
    save_dataframe("cuotas", df_cuotas)
    
    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    detalle = f"Cuota {meses_nombre[mes - 1]} {anio} - {nombre_jugador}"
    df_mov = get_dataframe("movimientos", ["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    nuevo_id_m = int(df_mov["id"].max()) + 1 if not df_mov.empty and "id" in df_mov.columns and not df_mov["id"].dropna().empty else 1
    nuevo_m = pd.DataFrame([[nuevo_id_m, "Cuota Jugador", "Ingreso", float(monto), fecha_pago_str, str(detalle), str(nombre_jugador)]], columns=["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    df_mov = pd.concat([df_mov, nuevo_m], ignore_index=True)
    save_dataframe("movimientos", df_mov)
    
    return True, "Pago de cuota registrado exitosamente."

def registrar_egreso(tipo_egreso, monto, fecha, detalle, responsable="Directiva"):
    df_mov = get_dataframe("movimientos", ["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    nuevo_id = int(df_mov["id"].max()) + 1 if not df_mov.empty and "id" in df_mov.columns and not df_mov["id"].dropna().empty else 1
    fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)
    nuevo_m = pd.DataFrame([[nuevo_id, str(tipo_egreso), "Egreso", float(monto), fecha_str, str(detalle), str(responsable)]], columns=["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    df_mov = pd.concat([df_mov, nuevo_m], ignore_index=True)
    save_dataframe("movimientos", df_mov)

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

def obtener_auspiciadores():
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    return df.sort_values(by="nombre", ascending=True) if not df.empty and "nombre" in df.columns else df

def agregar_auspiciador(nombre, rubro, contacto):
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    nuevo_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns and not df["id"].dropna().empty else 1
    nuevo_reg = pd.DataFrame([[nuevo_id, str(nombre).strip(), str(rubro).strip(), str(contacto).strip()]], columns=["id", "nombre", "rubro", "contacto"])
    df = pd.concat([df, nuevo_reg], ignore_index=True)
    save_dataframe("auspiciadores", df)

def eliminar_auspiciador(auspiciador_id):
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    if not df.empty and "id" in df.columns:
        df = df[df["id"].astype(int) != int(auspiciador_id)]
        save_dataframe("auspiciadores", df)

def agregar_noticia(titulo, contenido, imagen_bytes, autor="Directiva"):
    df = get_dataframe("noticias", ["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    nuevo_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns and not df["id"].dropna().empty else 1
    img_b64 = base64.b64encode(imagen_bytes).decode('utf-8') if imagen_bytes else ""
    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    nueva_n = pd.DataFrame([[nuevo_id, str(titulo).strip(), str(contenido).strip(), img_b64, fecha_act, str(autor).strip()]], columns=["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    df = pd.concat([df, nueva_n], ignore_index=True)
    save_dataframe("noticias", df)

def obtener_noticias():
    df = get_dataframe("noticias", ["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    return df.sort_values(by="id", ascending=False) if not df.empty and "id" in df.columns else df

def eliminar_noticia(noticia_id):
    df = get_dataframe("noticias", ["id", "titulo", "contenido", "imagen_b64", "fecha", "autor"])
    if not df.empty and "id" in df.columns:
        df = df[df["id"].astype(int) != int(noticia_id)]
        save_dataframe("noticias", df)

def agregar_comentario(noticia_id, nombre_autor, comentario):
    df = get_dataframe("comentarios", ["id", "noticia_id", "nombre_autor", "comentario", "fecha"])
    nuevo_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns and not df["id"].dropna().empty else 1
    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    nuevo_c = pd.DataFrame([[nuevo_id, int(noticia_id), str(nombre_autor).strip(), str(comentario).strip(), fecha_act]], columns=["id", "noticia_id", "nombre_autor", "comentario", "fecha"])
    df = pd.concat([df, nuevo_c], ignore_index=True)
    save_dataframe("comentarios", df)

def obtener_comentarios(noticia_id):
    df = get_dataframe("comentarios", ["id", "noticia_id", "nombre_autor", "comentario", "fecha"])
    if not df.empty and "noticia_id" in df.columns:
        df["noticia_id"] = pd.to_numeric(df["noticia_id"], errors='coerce')
        return df[df["noticia_id"] == int(noticia_id)].sort_values(by="id", ascending=True)
    return df

# GENERADOR PDF
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
            story.append(Paragraph("No existen registros de gastos.", cell_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 3. INTERFAZ GRÁFICA Y PERSONALIZACIÓN
# ==========================================
col_header1, col_header2 = st.columns([1, 5])
with col_header1:
    logo_b64 = cfg.get("logo_b64", "")
    if logo_b64 and logo_b64.strip() != "":
        try:
            st.image(base64.b64decode(logo_b64), width=120)
        except Exception:
            st.markdown('<div style="background-color: #002B49; color: white; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 35px; font-weight: bold; border: 4px solid #00A3E0;">AC</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background-color: #002B49; color: white; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 35px; font-weight: bold; border: 4px solid #00A3E0;">AC</div>', unsafe_allow_html=True)

with col_header2:
    titulo_banner = cfg.get("banner_titulo", "CLUB DEPORTIVO ATLÉTICO CENTURIÓN")
    st.markdown(f'<div class="header-centurion"><h1>{titulo_banner}</h1><p>🔵⚪ Sistema Transparente de Control Financiero & Comunidad ⚪🔵</p></div>', unsafe_allow_html=True)

st.sidebar.header("🔐 Acceso al Sistema")
if not st.session_state["es_admin"]:
    rol = st.sidebar.radio("Modalidad de Vista:", ["👁️ Transparencia Pública (Ver Datos)", "🔑 Administración"])
    if rol == "🔑 Administración":
        with st.sidebar.form("form_login"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
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

# Pestañas Principales Dinámicas
tabs_list = [
    "📰 Noticias", "📜 Cartola", "👟 Cuotas", "🏁 Árbitros", 
    "🛒 Compras", "👥 Plantel", "📄 PDF", "🤝 Auspiciadores"
]
if es_admin:
    tabs_list.append("🎨 Personalizar Web")

tabs = st.tabs(tabs_list)

tab_noticias = tabs[0]
tab_cartola = tabs[1]
tab_cuotas = tabs[2]
tab_arbitros = tabs[3]
tab_compras = tabs[4]
tab_jugadores = tabs[5]
tab_pdf = tabs[6]
tab_admin_ausp = tabs[7]
if es_admin:
    tab_config = tabs[8]

# TAB 1: NOTICIAS
with tab_noticias:
    st.subheader("📰 Novedades y Muro del Club")
    if es_admin:
        with st.expander("➕ Publicar Noticia o Foto", expanded=False):
            with st.form("form_noticia", clear_on_submit=True):
                tit = st.text_input("Título:")
                aut = st.text_input("Autor:", value="Directiva Atlético Centurión")
                foto = st.file_uploader("Foto asociada:", type=["jpg", "jpeg", "png"])
                cont = st.text_area("Contenido:")
                if st.form_submit_button("📣 Publicar"):
                    if tit.strip() and cont.strip():
                        b_img = foto.getvalue() if foto is not None else None
                        agregar_noticia(tit, cont, b_img, aut)
                        st.toast("Noticia publicada.", icon="🎉")
                        st.rerun()

    df_n = obtener_noticias()
    if not df_n.empty:
        for _, n in df_n.iterrows():
            nid = int(n['id'])
            st.markdown(f"### ⚽ {n['titulo']}")
            st.caption(f"📅 {n['fecha']} por **{n['autor']}**")
            if pd.notnull(n['imagen_b64']) and str(n['imagen_b64']).strip() != "":
                try:
                    st.image(base64.b64decode(n['imagen_b64']), use_container_width=True)
                except Exception:
                    pass
            st.write(n['contenido'])
            if es_admin:
                if st.button(f"🗑️ Eliminar Noticia #{nid}", key=f"del_n_{nid}"):
                    eliminar_noticia(nid)
                    st.rerun()
            
            st.markdown("##### 💬 Comentarios")
            df_c = obtener_comentarios(nid)
            if not df_c.empty:
                for _, c in df_c.iterrows():
                    st.markdown(f'<div class="comment-box"><b>👤 {c["nombre_autor"]}</b> <small>({c["fecha"]})</small><br><span>{c["comentario"]}</span></div>', unsafe_allow_html=True)
            
            with st.expander(f"✍️ Comentar en '{n['titulo']}'"):
                with st.form(key=f"fc_{nid}", clear_on_submit=True):
                    n_aut = st.text_input("Tu Nombre:", key=f"na_{nid}")
                    t_com = st.text_area("Comentario:", key=f"tc_{nid}")
                    if st.form_submit_button("Enviar"):
                        if n_aut.strip() and t_com.strip():
                            agregar_comentario(nid, n_aut, t_com)
                            st.rerun()
            st.divider()

# TAB 2: CARTOLA
with tab_cartola:
    st.subheader("📜 Cartola Financiera")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos", f"${ingresos_tot:,.0f}".replace(",", "."))
    c2.metric("Egresos", f"${egresos_tot:,.0f}".replace(",", "."))
    c3.metric("Saldo", f"${saldo_actual:,.0f}".replace(",", "."))
    st.divider()
    df_m = obtener_movimientos()
    if not df_m.empty:
        df_disp = df_m.copy()
        df_disp["Monto ($)"] = df_disp.apply(lambda r: f"+ ${float(r['monto']):,.0f}".replace(",", ".") if r['subtipo'] == 'Ingreso' else f"- ${float(r['monto']):,.0f}".replace(",", "."), axis=1)
        st.dataframe(df_disp[['fecha', 'tipo', 'subtipo', 'Monto ($)', 'detalle', 'responsable']], use_container_width=True)

# TAB 3: CUOTAS
with tab_cuotas:
    st.subheader("👟 Control de Cuotas")
    cm, ca = st.columns(2)
    m_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    ms = cm.selectbox("Mes:", list(m_dict.keys()), format_func=lambda x: m_dict[x], index=datetime.now().month - 1)
    ans = ca.number_input("Año:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    if es_admin:
        with st.expander("➕ Registrar Pago de Cuota"):
            df_j = obtener_jugadores()
            if not df_j.empty:
                j1, j2, j3 = st.columns(3)
                jsel = j1.selectbox("Jugador:", df_j["nombre"].tolist())
                monto_c = j2.number_input("Monto:", min_value=1000, value=5000, step=1000)
                f_c = j3.date_input("Fecha:", datetime.now())
                if st.button("💰 Registrar Cuota"):
                    jid = int(df_j[df_j["nombre"] == jsel]["id"].values[0])
                    ex, msg = registrar_pago_cuota(jid, jsel, ms, ans, monto_c, f_c)
                    if ex:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
    
    df_est = obtener_estado_cuotas(ms, ans)
    if not df_est.empty:
        df_est["Estado Visual"] = df_est["estado"].apply(lambda x: "✅ PAGADO" if x == "PAGADO" else "❌ PENDIENTE")
        st.dataframe(df_est[["nombre", "categoria", "Estado Visual", "fecha_pago", "monto"]], use_container_width=True)

# TAB 4: ÁRBITROS
with tab_arbitros:
    st.subheader("🏁 Pago a Árbitros")
    if es_admin:
        with st.form("fa", clear_on_submit=True):
            a1, a2 = st.columns(2)
            marb = a1.number_input("Monto ($):", min_value=1000, value=25000, step=1000)
            farb = a2.date_input("Fecha:", datetime.now())
            riv = st.text_input("Rival / Partido:")
            det = st.text_input("Detalle:")
            if st.form_submit_button("🚨 Registrar Egreso Árbitro"):
                concepto = f"Arbitraje: {riv} ({det})" if det else f"Arbitraje: {riv}"
                registrar_egreso("Pago Árbitros", marb, farb, concepto, "Tesorería")
                st.toast("Registrado.", icon="⚽")
                st.rerun()
    df_ma = obtener_movimientos()
    if not df_ma.empty:
        df_arb = df_ma[df_ma["tipo"] == "Pago Árbitros"]
        if not df_arb.empty:
            st.dataframe(df_arb[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 5: COMPRAS
with tab_compras:
    st.subheader("🛒 Compras del Club")
    if es_admin:
        with st.form("fc", clear_on_submit=True):
            c1, c2 = st.columns(2)
            mcomp = c1.number_input("Monto ($):", min_value=1000, value=15000, step=1000)
            fcomp = c2.date_input("Fecha:", datetime.now())
            ccomp = st.text_input("Concepto / Inversión:")
            bol = st.text_input("N° Boleta:")
            if st.form_submit_button("🛒 Registrar Compra"):
                d_comp = f"Compra: {ccomp} [{bol}]" if bol else f"Compra: {ccomp}"
                registrar_egreso("Compra Club", mcomp, fcomp, d_comp, "Tesorería")
                st.toast("Compra registrada.", icon="🛒")
                st.rerun()
    if not df_m.empty:
        df_comp = df_m[df_m["tipo"] == "Compra Club"]
        if not df_comp.empty:
            st.dataframe(df_comp[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 6: JUGADORES (Con Fotos de Perfil)
with tab_jugadores:
    st.subheader("👥 Plantel de Jugadores")
    if es_admin:
        j_add, j_del = st.columns(2)
        with j_add:
            st.markdown("#### ➕ Inscribir Jugador con Foto")
            with st.form("fnj", clear_on_submit=True):
                nom_j = st.text_input("Nombre Completo:")
                dor_j = st.text_input("Dorsal o RUT:")
                cat_j = st.selectbox("Categoría:", ["Adulto / Serie Honor", "Seniors", "Super Seniors", "Juvenil", "Femenino"])
                fot_j = st.file_uploader("Foto de Perfil:", type=["jpg", "jpeg", "png"])
                if st.form_submit_button("Guardar Jugador"):
                    if nom_j.strip():
                        b_foto = fot_j.getvalue() if fot_j is not None else None
                        agregar_jugador(nom_j, dor_j, cat_j, b_foto)
                        st.toast("Jugador inscrito.", icon="🎉")
                        st.rerun()
        with j_del:
            st.markdown("#### ❌ Dar de Baja")
            df_p_act = obtener_jugadores()
            if not df_p_act.empty:
                jsel_del = st.selectbox("Seleccionar:", df_p_act["nombre"].tolist())
                if st.button("🗑️ Eliminar"):
                    jid = int(df_p_act[df_p_act["nombre"] == jsel_del]["id"].values[0])
                    eliminar_jugador(jid)
                    st.rerun()

    df_p = obtener_jugadores()
    st.write(f"**Total Jugadores Activos:** {len(df_p)}")
    if not df_p.empty:
        for _, jp in df_p.iterrows():
            cols = st.columns([1, 4])
            with cols[0]:
                if pd.notnull(jp['foto_b64']) and str(jp['foto_b64']).strip() != "":
                    try:
                        st.image(base64.b64decode(jp['foto_b64']), width=80)
                    except Exception:
                        st.markdown("⚽")
                else:
                    st.markdown("⚽ *Sin foto*")
            with cols[1]:
                st.markdown(f"**{jp['nombre']}** — *Dorsal/RUT:* {jp['dorsal_o_rut']} — *Cat:* {jp['categoria']}")
            st.divider()

# TAB 7: PDF
with tab_pdf:
    st.subheader("📄 Generación de Informe PDF")
    pm, pa = st.columns(2)
    mpdf = pm.selectbox("Mes PDF:", list(m_dict.keys()), format_func=lambda x: m_dict[x], index=datetime.now().month - 1)
    apdf = pa.number_input("Año PDF:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    df_ep = obtener_estado_cuotas(mpdf, apdf)
    ing_p, egr_p, sal_p = calcular_resumen()
    
    pdf_b = generar_pdf_informe(m_dict[mpdf], apdf, ing_p, egr_p, sal_p, df_ep, obtener_movimientos())
    st.download_button("📥 Descargar Informe en PDF", data=pdf_b, file_name=f"Informe_{m_dict[mpdf]}_{apdf}.pdf", mime="application/pdf", use_container_width=True)

# TAB 8: AUSPICIADORES
with tab_admin_ausp:
    st.subheader("🤝 Auspiciadores")
    if es_admin:
        with st.form("fausp", clear_on_submit=True):
            an = st.text_input("Empresa:")
            ar = st.text_input("Rubro:")
            ac = st.text_input("Contacto:")
            if st.form_submit_button("Guardar"):
                if an.strip():
                    agregar_auspiciador(an, ar, ac)
                    st.rerun()
    df_a = obtener_auspiciadores()
    if not df_a.empty:
        st.dataframe(df_a, use_container_width=True)

# TAB 9: PERSONALIZAR WEB (Admin)
if es_admin:
    with tab_config:
        st.subheader("🎨 Personalización y Apariencia de la Web")
        with st.form("form_config"):
            nuevo_titulo = st.text_input("Título del Banner Principal:", value=cfg.get("banner_titulo", "CLUB DEPORTIVO ATLÉTICO CENTURIÓN"))
            color_fondo = st.color_picker("Color de Fondo de la Página:", value=cfg.get("bg_color", "#F8FAFC"))
            nuevo_logo = st.file_uploader("Subir Escudo / Logo Oficial (.png, .jpg):", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("💾 Guardar Cambios de Apariencia"):
                guardar_config("banner_titulo", nuevo_titulo)
                guardar_config("bg_color", color_fondo)
                if nuevo_logo is not None:
                    l_bytes = nuevo_logo.getvalue()
                    guardar_config("logo_b64", base64.b64encode(l_bytes).decode('utf-8'))
                st.toast("¡Apariencia actualizada con éxito!", icon="🎨")
                st.rerun()

# FOOTER
st.markdown("---")
df_af = obtener_auspiciadores()
s_html = '<div class="footer-sponsors"><h3>🤝 NUESTROS AUSPICIADORES</h3><div style="margin-top: 15px;">'
if not df_af.empty:
    for _, row in df_af.iterrows():
        s_html += f'<div class="sponsor-badge">⭐ {row["nombre"]} <span>{row["rubro"]}</span></div>'
else:
    s_html += '<div class="sponsor-badge">Espacio Disponible <span>Sé nuestro auspiciador</span></div>'
s_html += '</div></div>'
st.markdown(s_html, unsafe_allow_html=True)