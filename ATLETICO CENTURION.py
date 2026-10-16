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
    page_title="Atlético Centurión - Comunidad & Finanzas",
    page_icon="⚽",
    layout="wide"
)

if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
if "rol_actual" not in st.session_state:
    st.session_state["rol_actual"] = None

DB_FILES = {
    "jugadores": "jugadores.csv",
    "movimientos": "movimientos.csv",
    "cuotas": "cuotas.csv",
    "noticias": "noticias.csv",
    "comentarios": "comentarios.csv",
    "auspiciadores": "auspiciadores.csv",
    "configuracion": "configuracion.csv",
    "usuarios_club": "usuarios_club.csv"
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

# Estilos CSS con llaves duplicadas para evitar errores f-string
st.markdown(f"""
    <style>
    .stApp {{ background-color: {cfg.get("bg_color", "#F8FAFC")}; }}
    .header-centurion {{
        background: linear-gradient(135deg, #002B49 0%, #0A4B7C 100%);
        color: white; padding: 24px; border-radius: 16px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 43, 73, 0.25);
        border-bottom: 4px solid #00A3E0;
    }}
    .header-centurion h1 {{ color: #FFFFFF !important; font-weight: 800; font-size: 2.2rem; margin: 0; }}
    .header-centurion p {{ color: #E2E8F0; margin-top: 6px; font-size: 1.05rem; margin-bottom: 0; }}
    .stButton>button {{
        background-color: #002B49 !important; color: #FFFFFF !important;
        border-radius: 8px !important; font-weight: 600 !important;
    }}
    div[data-testid="stMetricValue"] {{ color: #002B49 !important; font-weight: 700; }}
    .stTabs [data-baseweb="tab"] {{ background-color: #E2E8F0; border-radius: 8px 8px 0 0; padding: 8px 16px; color: #002B49; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ background-color: #002B49 !important; color: #FFFFFF !important; }}
    .footer-sponsors {{ background-color: #002B49; color: white; padding: 30px; border-radius: 16px; margin-top: 50px; text-align: center; border-top: 4px solid #00A3E0; }}
    .sponsor-badge {{ background-color: #FFFFFF; color: #002B49; padding: 12px 20px; border-radius: 10px; font-weight: 700; display: inline-block; margin: 8px; border: 2px solid #E2E8F0; }}
    .sponsor-badge span {{ display: block; font-size: 0.8rem; color: #64748B; font-weight: 400; }}
    .post-card {{ background-color: #FFFFFF; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; }}
    .comment-box {{ background-color: #F1F5F9; border-radius: 8px; padding: 10px 15px; margin-top: 8px; border-left: 3px solid #002B49; color: #1E293B; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTIÓN DE USUARIOS Y ROLES
# ==========================================
def obtener_usuarios():
    df = get_dataframe("usuarios_club", ["username", "password", "nombre_completo", "rol"])
    return df

def registrar_usuario(username, password, nombre_completo, rol):
    df = get_dataframe("usuarios_club", ["username", "password", "nombre_completo", "rol"])
    if not df.empty and username in df["username"].values:
        return False, "El nombre de usuario ya existe."
    nuevo = pd.DataFrame([[username, password, nombre_completo, rol]], columns=["username", "password", "nombre_completo", "rol"])
    df = pd.concat([df, nuevo], ignore_index=True)
    save_dataframe("usuarios_club", df)
    return True, "Usuario creado exitosamente."

df_users_init = obtener_usuarios()
if df_users_init.empty:
    registrar_usuario("admin", "centurion2026", "Administrador Maestro", "Maestro")
    registrar_usuario("dirigente", "dirigente2026", "Dirigente de Turno", "Administrador")

# ==========================================
# 3. FUNCIONES DE NEGOCIO Y DATOS BLINDADAS
# ==========================================
def obtener_jugadores():
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64", "username"])
    if not df.empty and "activo" in df.columns:
        df["activo"] = pd.to_numeric(df["activo"], errors='coerce').fillna(1)
        df = df[df["activo"] == 1]
        return df.sort_values(by="nombre", ascending=True) if "nombre" in df.columns else df
    return df

def agregar_jugador(nombre, dorsal, categoria, foto_bytes, username="", password=""):
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64", "username"])
    nuevo_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns and not df["id"].dropna().empty else 1
    foto_b64 = base64.b64encode(foto_bytes).decode('utf-8') if foto_bytes else ""
    
    if username.strip() and password.strip():
        registrar_usuario(username.strip(), password.strip(), nombre, "Jugador")
    
    nuevo_reg = pd.DataFrame([[nuevo_id, str(nombre).strip(), str(dorsal).strip(), str(categoria), 1, foto_b64, str(username).strip()]], columns=["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64", "username"])
    df = pd.concat([df, nuevo_reg], ignore_index=True)
    save_dataframe("jugadores", df)

def eliminar_jugador(jugador_id):
    df = get_dataframe("jugadores", ["id", "nombre", "dorsal_o_rut", "categoria", "activo", "foto_b64", "username"])
    if not df.empty and "id" in df.columns:
        df.loc[df["id"].astype(int) == int(jugador_id), "activo"] = 0
        save_dataframe("jugadores", df)

def registrar_pago_cuota(jugador_id, nombre_jugador, mes, anio, monto, fecha_pago, nro_transaccion=""):
    df_cuotas = get_dataframe("cuotas", ["id", "jugador_id", "mes", "anio", "monto", "fecha_pago", "nro_transaccion"])
    if not df_cuotas.empty and "jugador_id" in df_cuotas.columns:
        df_cuotas["jugador_id"] = pd.to_numeric(df_cuotas["jugador_id"], errors='coerce')
        df_cuotas["mes"] = pd.to_numeric(df_cuotas["mes"], errors='coerce')
        df_cuotas["anio"] = pd.to_numeric(df_cuotas["anio"], errors='coerce')
        
        coincide = df_cuotas[(df_cuotas["jugador_id"] == int(jugador_id)) & (df_cuotas["mes"] == int(mes)) & (df_cuotas["anio"] == int(anio))]
        if not coincide.empty:
            return False, "Esta cuota ya se encuentra registrada para este jugador en este mes."

    fecha_pago_str = fecha_pago.strftime("%Y-%m-%d") if hasattr(fecha_pago, "strftime") else str(fecha_pago)
    
    nuevo_id_c = int(df_cuotas["id"].max()) + 1 if not df_cuotas.empty and "id" in df_cuotas.columns and not df_cuotas["id"].dropna().empty else 1
    nueva_c = pd.DataFrame([[nuevo_id_c, int(jugador_id), int(mes), int(anio), float(monto), fecha_pago_str, str(nro_transaccion)]], columns=["id", "jugador_id", "mes", "anio", "monto", "fecha_pago", "nro_transaccion"])
    df_cuotas = pd.concat([df_cuotas, nueva_c], ignore_index=True)
    save_dataframe("cuotas", df_cuotas)
    
    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    detalle = f"Cuota {meses_nombre[mes - 1]} {anio} - {nombre_jugador} (Tx: {nro_transaccion if nro_transaccion else 'S/N'})"
    
    df_mov = get_dataframe("movimientos", ["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    nuevo_id_m = int(df_mov["id"].max()) + 1 if not df_mov.empty and "id" in df_mov.columns and not df_mov["id"].dropna().empty else 1
    nuevo_m = pd.DataFrame([[nuevo_id_m, "Cuota Jugador", "Ingreso", float(monto), fecha_pago_str, str(detalle), str(nombre_jugador)]], columns=["id", "tipo", "subtipo", "monto", "fecha", "detalle", "responsable"])
    df_mov = pd.concat([df_mov, nuevo_m], ignore_index=True)
    save_dataframe("movimientos", df_mov)
    
    return True, "Pago de cuota y transacción registrados exitosamente."

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
    df_cuotas = get_dataframe("cuotas", ["id", "jugador_id", "mes", "anio", "monto", "fecha_pago", "nro_transaccion"])
    
    if df_jugs.empty:
        return pd.DataFrame(columns=["id", "nombre", "categoria", "estado", "fecha_pago", "monto", "nro_transaccion"])
        
    for col in ["jugador_id", "mes", "anio", "fecha_pago", "monto", "nro_transaccion"]:
        if col not in df_cuotas.columns:
            df_cuotas[col] = None

    if not df_cuotas.empty:
        df_cuotas["jugador_id"] = pd.to_numeric(df_cuotas["jugador_id"], errors='coerce')
        df_cuotas["mes"] = pd.to_numeric(df_cuotas["mes"], errors='coerce')
        df_cuotas["anio"] = pd.to_numeric(df_cuotas["anio"], errors='coerce')
        df_c_filtro = df_cuotas[(df_cuotas["mes"] == int(mes)) & (df_cuotas["anio"] == int(anio))]
    else:
        df_c_filtro = pd.DataFrame(columns=["jugador_id", "fecha_pago", "monto", "nro_transaccion"])
        
    merged = pd.merge(df_jugs, df_c_filtro, left_on="id", right_on="jugador_id", how="left")
    
    if "fecha_pago" not in merged.columns:
        merged["fecha_pago"] = None
    if "monto" not in merged.columns:
        merged["monto"] = 0
    if "nro_transaccion" not in merged.columns:
        merged["nro_transaccion"] = "-"
        
    merged["estado"] = merged["fecha_pago"].apply(lambda x: "PAGADO" if pd.notnull(x) and str(x).strip() != "" else "PENDIENTE")
    return merged[["id", "nombre", "categoria", "estado", "fecha_pago", "monto", "nro_transaccion"]].sort_values(by="nombre", ascending=True)

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
        cuotas_data = [[Paragraph("<font color='white'><b>Jugador</b></font>", cell_style), Paragraph("<font color='white'><b>Categoría</b></font>", cell_style), Paragraph("<font color='white'><b>Estado</b></font>", cell_style), Paragraph("<font color='white'><b>N° Tx / Pago</b></font>", cell_style), Paragraph("<font color='white'><b>Monto ($)</b></font>", cell_style)]]
        for _, r in df_estado.iterrows():
            st_color = "#059669" if r['estado'] == 'PAGADO' else "#DC2626"
            n_tx = r['nro_transaccion'] if pd.notnull(r['nro_transaccion']) and str(r['nro_transaccion']).strip() != "" else "-"
            monto_val = f"${float(r['monto']):,.0f}".replace(",", ".") if pd.notnull(r['monto']) and str(r['monto']).strip() != "" and float(r['monto']) > 0 else "$0"
            cuotas_data.append([Paragraph(str(r['nombre']), cell_style), Paragraph(str(r['categoria']), cell_style), Paragraph(f"<font color='{st_color}'><b>{r['estado']}</b></font>", cell_style), Paragraph(str(n_tx), cell_style), Paragraph(monto_val, cell_style)])
            
        cuotas_table = Table(cuotas_data, colWidths=[150, 110, 90, 100, 90])
        cuotas_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), primary_color), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])]))
        story.append(cuotas_table)
    else:
        story.append(Paragraph("No hay registro de jugadores en el sistema.", cell_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 4. INTERFAZ GRÁFICA Y SISTEMA DE ACCESO
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
    st.markdown(f'<div class="header-centurion"><h1>{titulo_banner}</h1><p>🔵⚪ Comunidad Interactiva & Control Financiero ⚪🔵</p></div>', unsafe_allow_html=True)

st.sidebar.header