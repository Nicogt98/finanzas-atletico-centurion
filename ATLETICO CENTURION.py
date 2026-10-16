import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import io

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTADO DE SESIÓN
# ==========================================
st.set_page_config(
    page_title="Atlético Centurión - Finanzas",
    page_icon="⚽",
    layout="wide"
)

# Inicializar memoria de sesión para el administrador
if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False

# Estilos CSS Personalizados
st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
    }
    
    .header-centurion {
        background: linear-gradient(135deg, #002B49 0%, #0A4B7C 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 43, 73, 0.25);
        border-bottom: 4px solid #00A3E0;
    }
    
    .header-centurion h1 {
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0;
        letter-spacing: 1px;
    }
    
    .header-centurion p {
        color: #E2E8F0;
        margin-top: 6px;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    
    .stButton>button {
        background-color: #002B49 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #002B49 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0A4B7C !important;
        color: #FFFFFF !important;
        border-color: #0A4B7C !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    div[data-testid="stMetricValue"] {
        color: #002B49 !important;
        font-weight: 700;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #E2E8F0;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        color: #002B49;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #002B49 !important;
        color: #FFFFFF !important;
    }

    .footer-sponsors {
        background-color: #002B49;
        color: white;
        padding: 30px;
        border-radius: 16px;
        margin-top: 50px;
        text-align: center;
        border-top: 4px solid #00A3E0;
    }
    
    .sponsor-badge {
        background-color: #FFFFFF;
        color: #002B49;
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 700;
        display: inline-block;
        margin: 8px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        border: 2px solid #E2E8F0;
    }
    
    .sponsor-badge span {
        display: block;
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 400;
    }
    </style>
""", unsafe_allow_html=True)

DB_NAME = "finanzas_centurion.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dorsal_o_rut TEXT,
            categoria TEXT DEFAULT 'Adulto',
            activo INTEGER DEFAULT 1
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            subtipo TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            detalle TEXT NOT NULL,
            responsable TEXT
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS cuotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jugador_id INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            anio INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha_pago TEXT NOT NULL,
            FOREIGN KEY (jugador_id) REFERENCES jugadores (id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS auspiciadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rubro TEXT,
            contacto TEXT
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM auspiciadores")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO auspiciadores (nombre, rubro, contacto) VALUES (?, ?, ?)", [
            ("Mani Centurión", "Insumos & Alimentos", "Contacto Auspiciador"),
            ("Deportes Centurión", "Indumentaria Deportiva", "Sponsor Oficial"),
            ("Agua Purificada Centurión", "Hidratación", "Sponsor Oficial")
        ])
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. FUNCIONES DE BASE DE DATOS Y GENERADOR PDF
# ==========================================
def obtener_auspiciadores():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, nombre, rubro, contacto FROM auspiciadores ORDER BY nombre ASC", conn)
    conn.close()
    return df

def agregar_auspiciador(nombre, rubro, contacto):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO auspiciadores (nombre, rubro, contacto) VALUES (?, ?, ?)", (nombre, rubro, contacto))
    conn.commit()
    conn.close()

def eliminar_auspiciador(auspiciador_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM auspiciadores WHERE id = ?", (auspiciador_id,))
    conn.commit()
    conn.close()

def obtener_jugadores():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, nombre, dorsal_o_rut, categoria FROM jugadores WHERE activo = 1 ORDER BY nombre ASC", conn)
    conn.close()
    return df

def agregar_jugador(nombre, dorsal, categoria):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO jugadores (nombre, dorsal_o_rut, categoria) VALUES (?, ?, ?)", (nombre, dorsal, categoria))
    conn.commit()
    conn.close()

def eliminar_jugador(jugador_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE jugadores SET activo = 0 WHERE id = ?", (jugador_id,))
    conn.commit()
    conn.close()

def registrar_pago_cuota(jugador_id, nombre_jugador, mes, anio, monto, fecha_pago):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM cuotas WHERE jugador_id = ? AND mes = ? AND anio = ?", (jugador_id, mes, anio))
    if c.fetchone():
        conn.close()
        return False, "Esta cuota ya se encuentra registrada para este jugador en este mes."
    
    c.execute("INSERT INTO cuotas (jugador_id, mes, anio, monto, fecha_pago) VALUES (?, ?, ?, ?, ?)",
              (jugador_id, mes, anio, monto, fecha_pago))
    
    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    nombre_mes = meses_nombre[mes - 1]
    detalle = f"Cuota {nombre_mes} {anio} - {nombre_jugador}"
    
    c.execute("INSERT INTO movimientos (tipo, subtipo, monto, fecha, detalle, responsable) VALUES (?, ?, ?, ?, ?, ?)",
              ("Cuota Jugador", "Ingreso", monto, fecha_pago, detalle, nombre_jugador))
    
    conn.commit()
    conn.close()
    return True, "Pago de cuota registrado exitosamente."

def registrar_egreso(tipo_egreso, monto, fecha, detalle, responsable="Directiva"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO movimientos (tipo, subtipo, monto, fecha, detalle, responsable) VALUES (?, ?, ?, ?, ?, ?)",
              (tipo_egreso, "Egreso", monto, fecha, detalle, responsable))
    conn.commit()
    conn.close()

def obtener_movimientos():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, fecha, tipo, subtipo, monto, detalle, responsable FROM movimientos ORDER BY fecha DESC, id DESC", conn)
    conn.close()
    return df

def calcular_resumen():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM movimientos WHERE subtipo = 'Ingreso'")
    ingresos = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(monto) FROM movimientos WHERE subtipo = 'Egreso'")
    egresos = c.fetchone()[0] or 0.0
    saldo = ingresos - egresos
    conn.close()
    return ingresos, egresos, saldo

def obtener_estado_cuotas(mes, anio):
    conn = get_connection()
    query = """
        SELECT j.id, j.nombre, j.categoria,
               CASE WHEN c.id IS NOT NULL THEN 'PAGADO' ELSE 'PENDIENTE' END as estado,
               c.fecha_pago, c.monto
        FROM jugadores j
        LEFT JOIN cuotas c ON j.id = c.jugador_id AND c.mes = ? AND c.anio = ?
        WHERE j.activo = 1
        ORDER BY j.nombre ASC
    """
    df = pd.read_sql_query(query, conn, params=(mes, anio))
    conn.close()
    return df

# GENERADOR DE REPORTES PDF CON REPORTLAB
def generar_pdf_informe(mes_nombre, anio, ingresos_tot, egresos_tot, saldo_actual, df_estado, df_mov):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#002B49")
    secondary_color = colors.HexColor("#00A3E0")
    light_bg = colors.HexColor("#F1F5F9")
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=primary_color, alignment=1, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, textColor=colors.HexColor("#475569"), alignment=1, spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=primary_color, spaceBefore=12, spaceAfter=6
    )
    cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=10
    )
    cell_bold = ParagraphStyle(
        'TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11
    )
    
    story = []
    
    # Encabezado Documento
    story.append(Paragraph("CLUB DEPORTIVO ATLÉTICO CENTURIÓN", title_style))
    story.append(Paragraph(f"INFORME FINANCIERO Y ESTADO DE CUOTAS — {mes_nombre.upper()} {anio}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_color, spaceAfter=15))
    
    # 1. Resumen Ejecutivo
    story.append(Paragraph("1. Resumen Ejecutivo de Saldos", h2_style))
    met_data = [
        [
            Paragraph("<b>Total Ingresos Recaudados</b>", cell_style),
            Paragraph("<b>Total Egresos (Gastos)</b>", cell_style),
            Paragraph("<b>Saldo Líquido Disponible</b>", cell_style)
        ],
        [
            Paragraph(f"<font color='#059669'><b>+ ${ingresos_tot:,.0f}</b></font>".replace(",", "."), cell_bold),
            Paragraph(f"<font color='#DC2626'><b>- ${egresos_tot:,.0f}</b></font>".replace(",", "."), cell_bold),
            Paragraph(f"<font color='#002B49'><b>${saldo_actual:,.0f}</b></font>".replace(",", "."), cell_bold)
        ]
    ]
    met_table = Table(met_data, colWidths=[180, 180, 180])
    met_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(met_table)
    story.append(Spacer(1, 12))
    
    # 2. Estado de Cuotas
    story.append(Paragraph(f"2. Estado de Cuotas de Jugadores — {mes_nombre} {anio}", h2_style))
    total_jug = len(df_estado) if df_estado is not None else 0
    pagados_cnt = len(df_estado[df_estado['estado'] == 'PAGADO']) if df_estado is not None and not df_estado.empty else 0
    deudores_cnt = total_jug - pagados_cnt
    
    stat_text = f"<b>Total Plantel:</b> {total_jug} | <b>Al Día (Pagados):</b> {pagados_cnt} | <b>Deudores (Pendientes):</b> {deudores_cnt}"
    story.append(Paragraph(stat_text, cell_style))
    story.append(Spacer(1, 6))
    
    if df_estado is not None and not df_estado.empty:
        cuotas_data = [[
            Paragraph("<font color='white'><b>Jugador</b></font>", cell_style),
            Paragraph("<font color='white'><b>Categoría</b></font>", cell_style),
            Paragraph("<font color='white'><b>Estado</b></font>", cell_style),
            Paragraph("<font color='white'><b>Fecha Pago</b></font>", cell_style),
            Paragraph("<font color='white'><b>Monto ($)</b></font>", cell_style)
        ]]
        
        for _, r in df_estado.iterrows():
            st_color = "#059669" if r['estado'] == 'PAGADO' else "#DC2626"
            st_text = f"<font color='{st_color}'><b>{r['estado']}</b></font>"
            f_pago = r['fecha_pago'] if pd.notnull(r['fecha_pago']) else "-"
            monto_val = f"${r['monto']:,.0f}".replace(",", ".") if pd.notnull(r['monto']) and r['monto'] > 0 else "$0"
            
            cuotas_data.append([
                Paragraph(str(r['nombre']), cell_style),
                Paragraph(str(r['categoria']), cell_style),
                Paragraph(st_text, cell_style),
                Paragraph(str(f_pago), cell_style),
                Paragraph(monto_val, cell_style)
            ])
            
        cuotas_table = Table(cuotas_data, colWidths=[160, 110, 90, 90, 90])
        cuotas_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])
        ]))
        story.append(cuotas_table)
    else:
        story.append(Paragraph("No hay registro de jugadores en el sistema.", cell_style))
        
    story.append(Spacer(1, 12))
    
    # 3. Detalle de Egresos
    story.append(Paragraph("3. Historial de Gastos y Compras del Club", h2_style))
    if df_mov is not None and not df_mov.empty:
        df_egr = df_mov[df_mov['subtipo'] == 'Egreso']
        if not df_egr.empty:
            egr_data = [[
                Paragraph("<font color='white'><b>Fecha</b></font>", cell_style),
                Paragraph("<font color='white'><b>Tipo</b></font>", cell_style),
                Paragraph("<font color='white'><b>Detalle / Concepto</b></font>", cell_style),
                Paragraph("<font color='white'><b>Monto ($)</b></font>", cell_style)
            ]]
            for _, r in df_egr.iterrows():
                egr_data.append([
                    Paragraph(str(r['fecha']), cell_style),
                    Paragraph(str(r['tipo']), cell_style),
                    Paragraph(str(r['detalle']), cell_style),
                    Paragraph(f"- ${r['monto']:,.0f}".replace(",", "."), cell_style)
                ])
            
            egr_table = Table(egr_data, colWidths=[75, 95, 270, 100])
            egr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), primary_color),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])
            ]))
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

logo_path = "logo_centurion.png"
if not os.path.exists(logo_path):
    logo_path = "logo.png"

with col_header1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=130)
    else:
        st.markdown("""
            <div style="background-color: #002B49; color: white; width: 110px; height: 110px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: bold; border: 4px solid #00A3E0; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                AC
            </div>
        """, unsafe_allow_html=True)

with col_header2:
    st.markdown("""
        <div class="header-centurion">
            <h1>CLUB DEPORTIVO ATLÉTICO CENTURIÓN</h1>
            <p>🔵⚪ Sistema Transparente de Control Financiero (Ingresos & Egresos) ⚪🔵</p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# GESTIÓN DE SESIÓN EN SIDEBAR (PERSISTENTE)
# ==========================================
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

if es_admin:
    st.sidebar.divider()
    st.sidebar.subheader("🖼️ Actualizar Logo del Club")
    logo_upload = st.sidebar.file_uploader("Subir imagen de Logo (.png / .jpg):", type=["png", "jpg", "jpeg"])
    if logo_upload is not None:
        with open("logo_centurion.png", "wb") as f:
            f.write(logo_upload.getbuffer())
        st.sidebar.success("¡Logo actualizado!")
        st.rerun()

ingresos_tot, egresos_tot, saldo_actual = calcular_resumen()
st.sidebar.divider()
st.sidebar.metric(label="💰 SALDO TOTAL DISPONIBLE", value=f"${saldo_actual:,.0f}".replace(",", "."))

# Pestañas Principales
tab_cartola, tab_cuotas, tab_arbitros, tab_compras, tab_jugadores, tab_pdf, tab_admin_ausp = st.tabs([
    "📜 Cartola Bancaria", 
    "👟 Cuotas Mensuales", 
    "🏁 Pago a Árbitros", 
    "🛒 Compras del Club",
    "👥 Plantel de Jugadores",
    "📄 Descargar Informe PDF",
    "🤝 Auspiciadores"
])

# TAB 1: CARTOLA
with tab_cartola:
    st.subheader("📜 Cartola Financiera del Club")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ingresos", f"${ingresos_tot:,.0f}".replace(",", "."))
    c2.metric("Total Egresos", f"${egresos_tot:,.0f}".replace(",", "."))
    c3.metric("Saldo Líquido", f"${saldo_actual:,.0f}".replace(",", "."))
    st.divider()
    
    df_mov = obtener_movimientos()
    if not df_mov.empty:
        df_display = df_mov.copy()
        df_display["Monto ($)"] = df_display.apply(
            lambda r: f"+ ${r['monto']:,.0f}".replace(",", ".") if r['subtipo'] == 'Ingreso' else f"- ${r['monto']:,.0f}".replace(",", "."),
            axis=1
        )
        st.dataframe(df_display[['fecha', 'tipo', 'subtipo', 'Monto ($)', 'detalle', 'responsable']], use_container_width=True)
    else:
        st.info("Aún no hay movimientos registrados.")

# TAB 2: CUOTAS
with tab_cuotas:
    st.subheader("👟 Control de Cuotas Mensuales")
    col_mes, col_anio = st.columns(2)
    meses_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    mes_sel = col_mes.selectbox("Seleccionar Mes:", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=datetime.now().month - 1)
    anio_sel = col_anio.number_input("Año:", min_value=2024, max_value=2030, value=datetime.now().year)
    
    if es_admin:
        with st.expander("➕ Registrar Pago de Cuota", expanded=True):
            df_jugs = obtener_jugadores()
            if not df_jugs.empty:
                col_j1, col_j2, col_j3 = st.columns(3)
                jugador_sel = col_j1.selectbox("Seleccionar Jugador:", df_jugs["nombre"].tolist())
                monto_cuota = col_j2.number_input("Monto Cuota ($):", min_value=1000, value=5000, step=1000)
                fecha_cuota = col_j3.date_input("Fecha de Pago:", datetime.now())
                
                if st.button("💰 Registrar Pago de Cuota"):
                    jugador_id = df_jugs[df_jugs["nombre"] == jugador_sel]["id"].values[0]
                    exito, msg = registrar_pago_cuota(jugador_id, jugador_sel, mes_sel, anio_sel, monto_cuota, fecha_cuota.strftime("%Y-%m-%d"))
                    if exito:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Primero debes inscribir jugadores en la pestaña 'Plantel de Jugadores'.")

    st.write(f"### Estado de Pagos - {meses_dict[mes_sel]} {anio_sel}")
    df_estado = obtener_estado_cuotas(mes_sel, anio_sel)
    if not df_estado.empty:
        df_estado["Estado Visual"] = df_estado["estado"].apply(lambda x: "✅ PAGADO" if x == "PAGADO" else "❌ PENDIENTE")
        st.dataframe(df_estado[["nombre", "categoria", "Estado Visual", "fecha_pago", "monto"]], use_container_width=True)
    else:
        st.info("No hay jugadores ingresados.")

# TAB 3: ÁRBITROS
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
                registrar_egreso("Pago Árbitros", monto_arb, fecha_arb.strftime("%Y-%m-%d"), concepto, "Tesorería")
                st.success(f"Pago de ${monto_arb:,.0f} a árbitros registrado.")
                st.rerun()

    st.write("### Historial de Pagos a Árbitros")
    df_mov_all = obtener_movimientos()
    if not df_mov_all.empty:
        df_arb = df_mov_all[df_mov_all["tipo"] == "Pago Árbitros"]
        if not df_arb.empty:
            st.dataframe(df_arb[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 4: COMPRAS
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
                registrar_egreso("Compra Club", monto_compra, fecha_compra.strftime("%Y-%m-%d"), detalle_compra, "Tesorería")
                st.success(f"Compra de ${monto_compra:,.0f} registrada correctamente.")
                st.rerun()

    st.write("### Historial de Compras")
    if not df_mov_all.empty:
        df_comp = df_mov_all[df_mov_all["tipo"] == "Compra Club"]
        if not df_comp.empty:
            st.dataframe(df_comp[['fecha', 'monto', 'detalle', 'responsable']], use_container_width=True)

# TAB 5: JUGADORES
with tab_jugadores:
    st.subheader("👥 Plantel de Jugadores")
    if es_admin:
        col_j_add, col_j_del = st.columns(2)
        with col_j_add:
            with st.form("form_nuevo_jugador", clear_on_submit=True):
                st.write("#### ➕ Inscribir Nuevo Jugador")
                nom_jugador = st.text_input("Nombre Completo:")
                dorsal_jugador = st.text_input("Dorsal o RUT:")
                cat_jugador = st.selectbox("Categoría:", ["Adulto / Serie Honor", "Seniors", "Super Seniors", "Juvenil", "Femenino"])
                
                if st.form_submit_button("Guardar Jugador"):
                    if nom_jugador.strip():
                        agregar_jugador(nom_jugador, dorsal_jugador, cat_jugador)
                        st.success(f"Jugador '{nom_jugador}' inscrito exitosamente.")
                        st.rerun()
                    else:
                        st.error("Debes ingresar al menos el nombre del jugador.")

        with col_j_del:
            df_plantel_actual = obtener_jugadores()
            if not df_plantel_actual.empty:
                with st.form("form_eliminar_jugador"):
                    st.write("#### ❌ Eliminar / Dar de Baja Jugador")
                    jugador_del = st.selectbox("Seleccionar Jugador a Eliminar:", df_plantel_actual["nombre"].tolist())
                    if st.form_submit_button("Eliminar Jugador Seleccionado"):
                        jug_id = df_plantel_actual[df_plantel_actual["nombre"] == jugador_del]["id"].values[0]
                        eliminar_jugador(jug_id)
                        st.success(f"Jugador '{jugador_del}' dado de baja.")
                        st.rerun()

    df_plantel = obtener_jugadores()
    st.write(f"**Total Jugadores Activos:** {len(df_plantel)}")
    if not df_plantel.empty:
        st.dataframe(df_plantel[["nombre", "dorsal_o_rut", "categoria"]], use_container_width=True)

# TAB 6: GENERAR E IMPRIMIR PDF
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
    
    if not df_est_pdf.empty:
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

# TAB 7: GESTIÓN DE AUSPICIADORES
with tab_admin_ausp:
    st.subheader("🤝 Gestión de Auspiciadores del Club")
    
    if es_admin:
        col_aus_add, col_aus_del = st.columns(2)
        with col_aus_add:
            with st.form("form_nuevo_auspiciador", clear_on_submit=True):
                st.write("#### ➕ Agregar Nuevo Auspiciador")
                aus_nombre = st.text_input("Nombre de la Empresa / Marca:")
                aus_rubro = st.text_input("Rubro / Tipo de Apoyo:")
                aus_contacto = st.text_input("Contacto / Detalle:")
                
                if st.form_submit_button("Guardar Auspiciador"):
                    if aus_nombre.strip():
                        agregar_auspiciador(aus_nombre, aus_rubro, aus_contacto)
                        st.success(f"Auspiciador '{aus_nombre}' agregado con éxito.")
                        st.rerun()
                    else:
                        st.error("Ingresa el nombre del auspiciador.")

        with col_aus_del:
            df_ausp_actual = obtener_auspiciadores()
            if not df_ausp_actual.empty:
                with st.form("form_eliminar_auspiciador"):
                    st.write("#### ❌ Eliminar Auspiciador")
                    aus_eliminar = st.selectbox("Seleccionar Auspiciador a Eliminar:", df_ausp_actual["nombre"].tolist())
                    if st.form_submit_button("Eliminar Auspiciador"):
                        aus_id = df_ausp_actual[df_ausp_actual["nombre"] == aus_eliminar]["id"].values[0]
                        eliminar_auspiciador(aus_id)
                        st.success(f"Auspiciador '{aus_eliminar}' eliminado.")
                        st.rerun()

    df_ausp = obtener_auspiciadores()
    if not df_ausp.empty:
        st.dataframe(df_ausp[["nombre", "rubro", "contacto"]], use_container_width=True)

# ==========================================
# 4. FOOTER INFERIOR - AUSPICIADORES
# ==========================================
st.markdown("---")
df_ausp_footer = obtener_auspiciadores()

sponsors_html = '<div class="footer-sponsors">'
sponsors_html += '<h3>🤝 NUESTROS AUSPICIADORES Y PATROCINADORES</h3>'
sponsors_html += '<p>Agradecemos el constante apoyo al Club Deportivo Atlético Centurión</p>'
sponsors_html += '<div style="margin-top: 15px;">'

if not df_ausp_footer.empty:
    for _, row in df_ausp_footer.iterrows():
        sponsors_html += f'<div class="sponsor-badge">⭐ {row["nombre"]} <span>{row["rubro"]}</span></div>'
else:
    sponsors_html += '<div class="sponsor-badge">Espacio Disponible <span>Sé nuestro auspiciador</span></div>'

sponsors_html += '</div></div>'

st.markdown(sponsors_html, unsafe_allow_html=True)