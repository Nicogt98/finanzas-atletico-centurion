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
            if df.empty or list(df.columns) != list(columns):
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

# Estilos CSS
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
# 2. GESTIÓN DE USUARIOS Y ROLES (BLINDADO)
# ==========================================
def obtener_usuarios():
    df = get_dataframe("usuarios_club", ["username", "password", "nombre_completo", "rol"])
    return df

def registrar_usuario(username, password, nombre_completo, rol):
    df = get_dataframe("usuarios_club", ["username", "password", "nombre_completo", "rol"])
    if not df.empty and "username" in df.columns and username in df["username"].values:
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
# 3. FUNCIONES DE NEGOCIO Y DATOS
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

st.sidebar.markdown("### 🔐 Acceso al Sistema")
df_all_users = obtener_usuarios()

if st.session_state["usuario_actual"] is None:
    tipo_login = st.sidebar.radio("Ingresar como:", ["🔑 Iniciar Sesión", "👁️ Modo Público / Invitado"])
    if tipo_login == "🔑 Iniciar Sesión":
        with st.sidebar.form("form_login_general"):
            u_input = st.text_input("Usuario")
            p_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if not df_all_users.empty and "username" in df_all_users.columns:
                    user_row = df_all_users[(df_all_users["username"] == u_input) & (df_all_users["password"] == p_input)]
                    if not user_row.empty:
                        st.session_state["usuario_actual"] = user_row.iloc[0]["nombre_completo"]
                        st.session_state["rol_actual"] = user_row.iloc[0]["rol"]
                        st.toast("¡Bienvenido al sistema!", icon="⚽")
                        st.rerun()
                    else:
                        st.sidebar.error("Usuario o contraseña incorrectos.")
                else:
                    st.sidebar.error("Error al leer la base de datos de usuarios.")
    else:
        st.session_state["usuario_actual"] = "Invitado"
        st.session_state["rol_actual"] = "Público"
else:
    st.sidebar.success(f"👤 Conectado: **{st.session_state['usuario_actual']}**")
    st.sidebar.info(f"🏷️ Rol: **{st.session_state['rol_actual']}**")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["usuario_actual"] = None
        st.session_state["rol_actual"] = None
        st.rerun()

rol = st.session_state["rol_actual"]
es_maestro = (rol == "Maestro")
es_admin = (rol in ["Maestro", "Administrador"])
es_jugador_o_mas = (rol in ["Maestro", "Administrador", "Jugador"])

ingresos_tot, egresos_tot, saldo_actual = calcular_resumen()
st.sidebar.divider()
st.sidebar.metric(label="💰 SALDO TOTAL DISPONIBLE", value=f"${saldo_actual:,.0f}".replace(",", "."))

tabs_list = ["📰 Muro Social", "📜 Cartola", "👟 Cuotas", "👥 Plantel", "📄 PDF", "🤝 Auspiciadores"]
if es_admin:
    tabs_list.extend(["🏁 Árbitros", "🛒 Compras"])
if es_maestro:
    tabs_list.append("🎨 Personalizar Web")

tabs = st.tabs(tabs_list)

tab_idx = 0
tab_muro = tabs[tab_idx]; tab_idx += 1
tab_cartola = tabs[tab_idx]; tab_idx += 1
tab_cuotas = tabs[tab_idx]; tab_idx += 1
tab_plantel = tabs[tab_idx]; tab_idx += 1
tab_pdf = tabs[tab_idx]; tab_idx += 1
tab_ausp = tabs[tab_idx]; tab_idx += 1

if es_admin:
    tab_arbitros = tabs[tab_idx]; tab_idx += 1
    tab_compras = tabs[tab_idx]; tab_idx += 1
if es_maestro:
    tab_config = tabs[tab_idx]; tab_idx += 1

# TAB 1: MURO SOCIAL
with tab_muro:
    st.subheader("📰 Muro Social y Novedades del Club")
    if rol != "Público" and rol is not None:
        with st.container():
            st.markdown("##### ✍️ ¿Qué está pasando en el club hoy?")
            with st.form("form_crear_publicacion", clear_on_submit=True):
                tit_post = st.text_input("Título de la publicación:")
                foto_post = st.file_uploader("Adjuntar foto o imagen:", type=["jpg", "jpeg", "png"])
                cont_post = st.text_area("Escribe tu mensaje para la comunidad...")
                if st.form_submit_button("📢 Publicar en el Muro"):
                    if tit_post.strip() and cont_post.strip():
                        b_img_post = foto_post.getvalue() if foto_post is not None else None
                        agregar_noticia(tit_post, cont_post, b_img_post, st.session_state["usuario_actual"])
                        st.toast("¡Publicado con éxito!", icon="🎉")
                        st.rerun()
                    else:
                        st.error("Debes ingresar un título y contenido.")
    else:
        st.info("💡 Inicia sesión para publicar en el muro y comentar con la comunidad.")

    st.divider()
    df_n = obtener_noticias()
    if not df_n.empty:
        for _, n in df_n.iterrows():
            nid = int(n['id'])
            st.markdown(f"""
                <div class="post-card">
                    <h3>⚽ {n['titulo']}</h3>
                    <p style="color: #64748B; font-size: 0.85rem;">📅 {n['fecha']} | Publicado por: <b>{n['autor']}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            if pd.notnull(n['imagen_b64']) and str(n['imagen_b64']).strip() != "":
                try:
                    st.image(base64.b64decode(n['imagen_b64']), use_container_width=True)
                except Exception:
                    pass
            
            st.write(n['contenido'])
            
            if es_maestro or (rol != "Público" and n['autor'] == st.session_state["usuario_actual"]):
                if st.button(f"🗑️ Eliminar Publicación #{nid}", key=f"del_post_{nid}"):
                    eliminar_noticia(nid)
                    st.rerun()
            
            st.markdown("##### 💬 Comentarios")
            df_c = obtener_comentarios(nid)
            if not df_c.empty:
                for _, c in df_c.iterrows():
                    st.markdown(f'<div class="comment-box"><b>👤 {c["nombre_autor"]}</b> <small style="color:#64748B;">({c["fecha"]})</small><br><span>{c["comentario"]}</span></div>', unsafe_allow_html=True)
            else:
                st.write("*(Sin comentarios aún)*")
            
            if rol != "Público" and rol is not None:
                with st.form(key=f"form_com_post_{nid}", clear_on_submit=True):
                    txt_com = st.text_input("Escribe un comentario...", key=f"txt_c_{nid}")
                    if st.form_submit_button("💬 Comentar"):
                        if txt_com.strip():
                            agregar_comentario(nid, st.session_state["usuario_actual"], txt_com)
                            st.rerun()
            st.markdown("---")
    else:
        st.info("No hay publicaciones en el muro todavía.")

# TAB 2: CARTOLA
with tab_cartola:
    st.subheader("📜 Cartola Bancaria y Transparencia")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos Totales", f"${ingresos_tot:,.0f}".replace(",", "."))
    c2.metric("Egresos Totales", f"${egresos_tot:,.0f}".replace(",", "."))
    c3.metric("Saldo Líquido", f"${saldo_actual:,.0f}".replace(",", "."))
    st.divider()
    df_m = obtener_movimientos()
    if not df_m.empty:
        df_disp = df_m.copy()
        df_disp["Monto ($)"] = df_disp.apply(lambda r: f"+ ${float(r['monto']):,.0f}".replace(",", ".") if r['subtipo'] == 'Ingreso' else f"- ${float(r['monto']):,.0f}".replace(",", "."), axis=1)
        st.dataframe(df_disp[['fecha', 'tipo', 'subtipo', 'Monto ($)', 'detalle', 'responsable']], use_container_width=True)
    else:
        st.info("No hay movimientos registrados.")

# TAB 3: CUOTAS
with tab_cuotas:
    st.subheader("👟 Control de Cuotas Mensuales y Transacciones")
    cm, ca = st.columns(2)
    m_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    ms = cm.selectbox("Mes:", list(m_dict.keys()), format_func=lambda x: m_dict[x], index=datetime.now().month - 1)
    ans = ca.number_input("Año:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    if es_admin:
        with st.expander("➕ Registrar Pago de Cuota y N° de Transacción"):
            df_j = obtener_jugadores()
            if not df_j.empty:
                j1, j2, j3, j4 = st.columns(4)
                jsel = j1.selectbox("Jugador:", df_j["nombre"].tolist())
                monto_c = j2.number_input("Monto:", min_value=1000, value=5000, step=1000)
                f_c = j3.date_input("Fecha Pago:", datetime.now())
                nro_tx = j4.text_input("N° de Transacción / Boleta:", placeholder="Ej: TX-984125")
                
                if st.button("💰 Registrar Pago con Transacción"):
                    jid = int(df_j[df_j["nombre"] == jsel]["id"].values[0])
                    ex, msg = registrar_pago_cuota(jid, jsel, ms, ans, monto_c, f_c, nro_tx)
                    if ex:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
    
    df_est = obtener_estado_cuotas(ms, ans)
    if not df_est.empty:
        df_est["Estado Visual"] = df_est["estado"].apply(lambda x: "✅ PAGADO" if x == "PAGADO" else "❌ PENDIENTE")
        st.dataframe(df_est[["nombre", "categoria", "Estado Visual", "nro_transaccion", "fecha_pago", "monto"]], use_container_width=True)

# TAB 4: PLANTEL
with tab_plantel:
    st.subheader("👥 Plantel de Jugadores y Usuarios del Club")
    if es_admin:
        j_add, j_del = st.columns(2)
        with j_add:
            st.markdown("#### ➕ Inscribir Jugador y Crear Usuario")
            with st.form("fnj_user", clear_on_submit=True):
                nom_j = st.text_input("Nombre Completo:")
                dor_j = st.text_input("Dorsal o RUT:")
                cat_j = st.selectbox("Categoría:", ["Adulto / Serie Honor", "Seniors", "Super Seniors", "Juvenil", "Femenino"])
                fot_j = st.file_uploader("Foto de Perfil:", type=["jpg", "jpeg", "png"])
                
                st.markdown("---")
                st.markdown("##### 🔑 Credenciales de Acceso (Manual sin correo)")
                crear_usr = st.checkbox("Crear cuenta de usuario para este jugador")
                u_user = st.text_input("Nombre de Usuario (Login):")
                u_pass = st.text_input("Contraseña de Acceso:", type="password")
                
                if st.form_submit_button("Guardar Jugador y Usuario"):
                    if nom_j.strip():
                        b_foto = fot_j.getvalue() if fot_j is not None else None
                        usr_final = u_user if crear_usr else ""
                        pass_final = u_pass if crear_usr else ""
                        agregar_jugador(nom_j, dor_j, cat_j, b_foto, usr_final, pass_final)
                        st.toast("Jugador y cuenta creados con éxito.", icon="🎉")
                        st.rerun()
        with j_del:
            st.markdown("#### ❌ Dar de Baja Jugador")
            df_p_act = obtener_jugadores()
            if not df_p_act.empty:
                jsel_del = st.selectbox("Seleccionar Jugador:", df_p_act["nombre"].tolist())
                if st.button("🗑️ Eliminar Jugador"):
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
                usr_tag = f" | 👤 User: `{jp['username']}`" if pd.notnull(jp['username']) and str(jp['username']).strip() != "" else ""
                st.markdown(f"**{jp['nombre']}** — *Dorsal:* {jp['dorsal_o_rut']} — *Cat:* {jp['categoria']}{usr_tag}")
            st.divider()

# TAB 5: PDF
with tab_pdf:
    st.subheader("📄 Generación de Informe PDF con Transacciones")
    pm, pa = st.columns(2)
    mpdf = pm.selectbox("Mes PDF:", list(m_dict.keys()), format_func=lambda x: m_dict[x], index=datetime.now().month - 1)
    apdf = pa.number_input("Año PDF:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    df_ep = obtener_estado_cuotas(mpdf, apdf)
    ing_p, egr_p, sal_p = calcular_resumen()
    
    pdf_b = generar_pdf_informe(m_dict[mpdf], apdf, ing_p, egr_p, sal_p, df_ep, obtener_movimientos())
    st.download_button("📥 Descargar Informe en PDF", data=pdf_b, file_name=f"Informe_{m_dict[mpdf]}_{apdf}.pdf", mime="application/pdf", use_container_width=True)

# TAB 6: AUSPICIADORES
with tab_ausp:
    st.subheader("🤝 Auspiciadores del Club")
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

# TAB 7: ÁRBITROS
if es_admin:
    with tab_arbitros:
        st.subheader("🏁 Pago a Árbitros")
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

# TAB 8: COMPRAS
if es_admin:
    with tab_compras:
        st.subheader("🛒 Compras del Club")
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

# TAB 9: PERSONALIZAR WEB
if es_maestro:
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