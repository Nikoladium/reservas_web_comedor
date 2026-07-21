import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials
import unicodedata

# ╔══════════════════════════════════════════════════════════════════╗
# ║  COMEDOR UNIVERSITARIO — Sistema de Reservas                    ║
# ║  Versión optimizada de alto rendimiento y arquitectura limpia   ║
# ╚══════════════════════════════════════════════════════════════════╝

# ─── 1. CONFIGURACIÓN Y ESTILOS CSS ────────────────────────────────

st.set_page_config(
    page_title="Comedor Universitario",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* Ocultar barra superior de desarrollo */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Contenedor principal responsivo */
    .main .block-container {
        max-width: 720px;
        padding-top: 1rem;
    }

    /* Cabecera atractiva */
    .app-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 4px 24px rgba(99, 102, 241, 0.3);
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .app-header p {
        margin: 0.4rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }

    /* Secciones del formulario */
    .section-label {
        background: linear-gradient(90deg, #f0f0ff 0%, #faf5ff 100%);
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin: 1.2rem 0 0.6rem 0;
        border-left: 4px solid #8b5cf6;
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Botón de envío */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
    }
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
    }

    /* Resumen de reserva confirmada */
    .reserva-ok {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 0.5rem;
    }

    /* Footer personalizado */
    .app-footer {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        color: #9ca3af;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── 2. FUNCIONES DE UTILIDAD Y NORMALIZACIÓN ─────────────────────

def normalizar_nombre(texto: str) -> str:
    """Normaliza texto removiendo acentos, espacios y convirtiendo a minúsculas."""
    if not texto:
        return ""
    texto = texto.strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def parsear_fecha_menu(texto: str) -> str:
    """Formatea la fecha del menú en español (ej: Martes, 21 de Julio de 2026)."""
    DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.now()
    
    if not texto or not str(texto).strip():
        return f"{DIAS[now.weekday()]}, {now.day} de {MESES[now.month - 1]} de {now.year}"
        
    txt = str(texto).strip().lower()
    txt_norm = normalizar_nombre(txt)
    
    if txt_norm == "manana":
        manana = now + timedelta(days=1)
        return f"{DIAS[manana.weekday()]}, {manana.day} de {MESES[manana.month - 1]} de {manana.year}"
    elif txt_norm == "hoy":
        return f"{DIAS[now.weekday()]}, {now.day} de {MESES[now.month - 1]} de {now.year}"
        
    try:
        partes = txt.split("/")
        if len(partes) >= 2:
            dia = int(partes[0])
            mes = int(partes[1])
            anio = int(partes[2]) if len(partes) >= 3 else now.year
            dt = datetime(anio, mes, dia)
            return f"{DIAS[dt.weekday()]}, {dt.day} de {MESES[dt.month - 1]} de {dt.year}"
    except Exception:
        pass
        
    return str(texto).strip()


# ─── 3. ESTADOS INICIALES EN MEMORIA ──────────────────────────────

if "db_menu" not in st.session_state:
    st.session_state.db_menu = pd.DataFrame({
        "Codigo": ["1a", "1b", "2a", "2b", "3a", "3b", "3c", "3d", "4a", "4b", "4c", "5a", "5b"],
        "Plato": [
            "Lentejas estofadas", "Crema de calabacín",
            "Pollo asado con hierbas", "Merluza a la plancha",
            "Fruta", "Yogur", "Tarta de chocolate", "Flan casero",
            "Patatas fritas", "Arroz blanco", "Verduras salteadas",
            "Ensalada mixta", "Ensalada César"
        ],
        "Stock": [15, 15, 12, 10, 999, 999, 8, 0, 20, 20, 18, 20, 0]
    })

if "db_reservas" not in st.session_state:
    st.session_state.db_reservas = []
if "ultima_reserva" not in st.session_state:
    st.session_state.ultima_reserva = None
if "trigger_balloons" not in st.session_state:
    st.session_state.trigger_balloons = False
if "cancel_step" not in st.session_state:
    st.session_state.cancel_step = "search"
if "cancel_reserva_data" not in st.session_state:
    st.session_state.cancel_reserva_data = None


# ─── 4. CAPA DE BASE DE DATOS OPTIMIZADA CON CACHÉ ─────────────────

@st.cache_resource(ttl=3600, show_spinner=False)
def get_sheets_client():
    """Cachea la autenticación con Google Sheets durante 1 hora (ultra rápido)."""
    if "gcloud" in st.secrets and "private_gsheets_url" in st.secrets:
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(st.secrets["gcloud"], scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url(st.secrets["private_gsheets_url"])
            return sheet
        except Exception:
            return None
    return None


@st.cache_data(ttl=10, show_spinner=False)
def load_menu():
    """Cachea la lectura del menú durante 10 segundos para respuestas instantáneas."""
    sheet = get_sheets_client()
    if sheet:
        try:
            menu_ws = sheet.worksheet("Menu")
            values = menu_ws.get_all_values()
            if values:
                # Extraer celda D1 si contiene fecha personalizada
                fecha_custom = ""
                if len(values[0]) >= 4 and values[0][3].strip():
                    if normalizar_nombre(values[0][3]) != "fecha":
                        fecha_custom = values[0][3].strip()
                elif len(values) >= 2 and len(values[1]) >= 4 and values[1][3].strip():
                    fecha_custom = values[1][3].strip()

                first_cell = normalizar_nombre(str(values[0][0]))
                rows = values[1:] if "cod" in first_cell else values
                
                data = []
                for row in rows:
                    if len(row) >= 2 and row[0].strip():
                        codigo = row[0].strip()
                        plato = row[1].strip() if len(row) >= 2 else ""
                        stock_raw = row[2].strip() if len(row) >= 3 else "0"
                        try:
                            stock = int(stock_raw) if stock_raw.isdigit() else (999 if (plato != "" and stock_raw == "") else 0)
                        except ValueError:
                            stock = 999 if (plato != "" and stock_raw == "") else 0
                        data.append({"Codigo": codigo, "Plato": plato, "Stock": stock})
                
                df = pd.DataFrame(data)
                if not df.empty:
                    return df, fecha_custom
        except Exception:
            pass
    return st.session_state.db_menu, ""


def adjust_stock(sheet, item_names, delta):
    """Modifica el stock en Google Sheets y limpia el caché."""
    if not item_names:
        return
    try:
        menu_ws = sheet.worksheet("Menu")
        records = menu_ws.get_all_values()
        if not records:
            return
        
        first_cell = normalizar_nombre(str(records[0][0]))
        start_idx = 1 if "cod" in first_cell else 0
        
        name_to_row = {}
        for idx in range(start_idx, len(records)):
            row = records[idx]
            if len(row) < 2:
                continue
            plato = row[1].strip()
            if not plato:
                continue
            try:
                stock = int(row[2]) if len(row) >= 3 and row[2].strip() != "" else 0
            except ValueError:
                stock = 999
            name_to_row[plato] = {"row": idx + 1, "stock": stock}
            
        for name in item_names:
            if not name:
                continue
            if name in name_to_row:
                info = name_to_row[name]
                if info["stock"] < 999:
                    new_stock = max(0, info["stock"] + delta)
                    menu_ws.update_cell(info["row"], 3, new_stock)
        
        # Limpiar caché para reflejar el stock inmediatamente
        load_menu.clear()
    except Exception as e:
        st.error(f"Error al actualizar stock: {e}")


def save_reserva(reserva: dict):
    """Guarda la reserva y actualiza el stock."""
    sheet = get_sheets_client()
    items_to_deduct = [
        reserva["Primero"], reserva["Segundo"],
        reserva["Acomp1"], reserva["Acomp2"],
        reserva["Ensalada"], reserva["Postre"]
    ]
    items_to_deduct = [item for item in items_to_deduct if item]
    
    if sheet:
        try:
            reservas_ws = sheet.worksheet("Reservas")
            row = [
                reserva["Timestamp"], reserva["Nombre"], reserva["TipoMenu"],
                reserva["Primero"], reserva["Segundo"], reserva["Acomp1"],
                reserva["Acomp2"], reserva["Ensalada"], reserva["Postre"],
                reserva["Comentarios"], reserva["Estado"]
            ]
            reservas_ws.append_row(row)
            adjust_stock(sheet, items_to_deduct, -1)
            return True
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            return False
    else:
        st.session_state.db_reservas.append(reserva)
        for item in items_to_deduct:
            st.session_state.db_menu.loc[st.session_state.db_menu["Plato"] == item, "Stock"] = (
                st.session_state.db_menu.loc[st.session_state.db_menu["Plato"] == item, "Stock"].apply(lambda x: max(0, x - 1))
            )
        return True


def find_active_reserva(nombre: str):
    """Busca una reserva activa por nombre de forma insensible a acentos/mayúsculas."""
    sheet = get_sheets_client()
    if sheet:
        try:
            reservas_ws = sheet.worksheet("Reservas")
            rows = reservas_ws.get_all_values()
            for idx in range(len(rows) - 1, 0, -1):
                row = rows[idx]
                if len(row) >= 11:
                    row_nombre = row[1].strip()
                    row_estado = row[10].strip()
                    if normalizar_nombre(row_nombre) == normalizar_nombre(nombre) and row_estado == "Pendiente":
                        return {
                            "row_idx": idx + 1, "Timestamp": row[0], "Nombre": row[1],
                            "TipoMenu": row[2], "Primero": row[3], "Segundo": row[4],
                            "Acomp1": row[5], "Acomp2": row[6], "Ensalada": row[7],
                            "Postre": row[8], "Comentarios": row[9], "Estado": row[10]
                        }
        except Exception:
            pass
    else:
        for r in reversed(st.session_state.db_reservas):
            if normalizar_nombre(r["Nombre"]) == normalizar_nombre(nombre) and r["Estado"] == "Pendiente":
                return r
    return None


def cancel_reserva_by_data(reserva: dict):
    """Cancela la reserva indicada y devuelve el stock."""
    sheet = get_sheets_client()
    items_to_replenish = [
        reserva["Primero"], reserva["Segundo"], reserva["Acomp1"],
        reserva["Acomp2"], reserva["Ensalada"], reserva["Postre"]
    ]
    items_to_replenish = [item.strip() for item in items_to_replenish if item and item.strip()]
    
    if sheet:
        try:
            reservas_ws = sheet.worksheet("Reservas")
            row_idx = reserva["row_idx"]
            reservas_ws.update_cell(row_idx, 11, "Cancelada")
            adjust_stock(sheet, items_to_replenish, 1)
            return True, f"¡Reserva de **{reserva['Nombre']}** cancelada correctamente! El stock ha sido devuelto."
        except Exception as e:
            return False, f"Error al cancelar en la hoja: {e}"
    else:
        for r in st.session_state.db_reservas:
            if r["Nombre"] == reserva["Nombre"] and r["Timestamp"] == reserva["Timestamp"] and r["Estado"] == "Pendiente":
                r["Estado"] = "Cancelada"
                for item in items_to_replenish:
                    if item:
                        st.session_state.db_menu.loc[st.session_state.db_menu["Plato"] == item, "Stock"] += 1
                return True, f"¡Reserva de **{reserva['Nombre']}** cancelada en memoria! El stock ha sido devuelto."
        return False, "No se encontró la reserva activa correspondiente."


# ─── 5. OBTENCIÓN Y FILTRADO DEL MENÚ ──────────────────────────────

df_menu, fecha_custom_menu = load_menu()

def get_available(df: pd.DataFrame, prefix: str) -> list[dict]:
    mask = (
        df["Codigo"].astype(str).str.startswith(prefix)
        & (df["Stock"] > 0)
        & (df["Plato"].astype(str).str.strip() != "")
    )
    return df[mask].to_dict("records")

def fmt_stock(nombre: str, stock: int) -> str:
    if stock >= 999:
        return nombre
    return f"{nombre}  ·  🔢 {stock} disp."

primeros = get_available(df_menu, "1")
segundos = get_available(df_menu, "2")
postres = get_available(df_menu, "3")
acomps = get_available(df_menu, "4")
ensaladas = get_available(df_menu, "5")

todos_platos = (
    [("Primero", p["Plato"], p["Stock"]) for p in primeros]
    + [("Segundo", s["Plato"], s["Stock"]) for s in segundos]
)


# ─── 6. CABECERA DE LA PÁGINA ──────────────────────────────────────

fecha_menu_str = parsear_fecha_menu(fecha_custom_menu)

st.markdown(f"""
<div class="app-header">
    <h1>🍽️ Comedor Universitario</h1>
    <p>Reserva tu menú del día</p>
    <div style="margin-top: 0.8rem; background: rgba(255, 255, 255, 0.22); display: inline-block; padding: 0.35rem 1.1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600; letter-spacing: 0.01em;">
        📅 Menú del día: {fecha_menu_str}
    </div>
</div>
""", unsafe_allow_html=True)

if not primeros and not segundos:
    st.warning("⏳ El menú de hoy aún no está disponible o se ha agotado el stock. Vuelve más tarde.")
    st.stop()

st.info("🥤 Todos los menús incluyen **bebida, ensalada y postre**  ·  Selecciona tus opciones abajo")

if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False


# ─── 7. VISTA REACTIVA Y FORMULARIO ────────────────────────────────

st.markdown("🍴 **Tipo de Menú**")
st.caption("💡 *Menú Entero: 1 primero + 1 segundo  ·  Medio Menú: 1 plato a elegir*")
tipo_menu = st.radio(
    "Tipo de Menú",
    options=["Menú Entero", "Medio Menú"],
    horizontal=True,
    label_visibility="collapsed",
)

if tipo_menu == "Medio Menú":
    st.markdown('<div class="section-label">🍲 Platos Principales (Elige 1)</div>', unsafe_allow_html=True)
    if todos_platos:
        labels = [f"🍽️ {fmt_stock(nombre_p, stock)}" for cat, nombre_p, stock in todos_platos]
        plato_idx = st.radio(
            "Plato único medio menú",
            options=range(len(labels)),
            format_func=lambda i: labels[i],
            label_visibility="collapsed",
        )
        plato_medio_sel = todos_platos[plato_idx]
    else:
        st.error("No hay platos disponibles")
        plato_medio_sel = None
else:
    plato_medio_sel = None

st.divider()

with st.form("reserva_form", clear_on_submit=False):

    nombre = st.text_input("👤 Nombre y Apellido *", placeholder="Ej: María García")

    if tipo_menu == "Menú Entero":
        st.markdown('<div class="section-label">🍲 Platos Principales</div>', unsafe_allow_html=True)
        col_p, col_s = st.columns(2)
        with col_p:
            st.markdown("**Primer plato**")
            if primeros:
                primero_sel = st.radio(
                    "Primer plato",
                    options=[p["Plato"] for p in primeros],
                    format_func=lambda x: fmt_stock(x, next(p["Stock"] for p in primeros if p["Plato"] == x)),
                    label_visibility="collapsed",
                )
            else:
                st.error("No hay primeros disponibles")
                primero_sel = None

        with col_s:
            st.markdown("**Segundo plato**")
            if segundos:
                segundo_sel = st.radio(
                    "Segundo plato",
                    options=[s["Plato"] for s in segundos],
                    format_func=lambda x: fmt_stock(x, next(s["Stock"] for s in segundos if s["Plato"] == x)),
                    label_visibility="collapsed",
                )
            else:
                st.error("No hay segundos disponibles")
                segundo_sel = None
        plato_unico = None
    else:
        plato_unico = plato_medio_sel
        primero_sel = None
        segundo_sel = None

    # ── Acompañamientos ──
    es_primer_plato_medio = (tipo_menu == "Medio Menú" and plato_unico and plato_unico[0] == "Primero")

    st.markdown(
        '<div class="section-label">🥗 Acompañamientos <span style="font-weight:400; color:#6b7280;">(máximo 2)</span></div>',
        unsafe_allow_html=True,
    )

    if es_primer_plato_medio:
        st.info("ℹ️ El primer plato no incluye acompañamiento.")
        acomp_sel = []
    elif acomps:
        acomp_sel = st.multiselect(
            "Elige tus guarniciones",
            options=[a["Plato"] for a in acomps],
            placeholder="Selecciona hasta 2 acompañamientos",
            format_func=lambda x: fmt_stock(x, next(a["Stock"] for a in acomps if a["Plato"] == x)),
            label_visibility="collapsed",
        )
    else:
        st.info("No hay acompañamientos disponibles hoy")
        acomp_sel = []

    # ── Ensalada ──
    st.markdown('<div class="section-label">🥬 Ensalada</div>', unsafe_allow_html=True)
    if ensaladas:
        ensalada_opts = [e["Plato"] for e in ensaladas] + ["Sin ensalada"]
        ensalada_sel_raw = st.radio(
            "Elige tu ensalada",
            options=ensalada_opts,
            format_func=lambda x: "🚫 Sin ensalada" if x == "Sin ensalada" else fmt_stock(
                x, next((e["Stock"] for e in ensaladas if e["Plato"] == x), 999)
            ),
            label_visibility="collapsed",
        )
        ensalada_sel = "" if ensalada_sel_raw == "Sin ensalada" else ensalada_sel_raw
    else:
        st.warning("No hay ensalada disponible en este momento")
        ensalada_sel = None

    # ── Postre ──
    st.markdown('<div class="section-label">🍰 Postre</div>', unsafe_allow_html=True)
    if postres:
        postre_sel = st.radio(
            "Elige tu postre",
            options=[p["Plato"] for p in postres],
            format_func=lambda x: fmt_stock(x, next(p["Stock"] for p in postres if p["Plato"] == x)),
            label_visibility="collapsed",
        )
    else:
        st.warning("No hay postre disponible en este momento")
        postre_sel = None

    # ── Comentarios ──
    st.markdown('<div class="section-label">💬 Observaciones o Alergias (opcional)</div>', unsafe_allow_html=True)
    comentarios = st.text_area(
        "Observaciones",
        placeholder="Ej: Sin sal, alergia a frutos secos...",
        label_visibility="collapsed",
        height=80,
    )

    st.markdown("")
    submitted = st.form_submit_button("✅ Enviar Reserva", use_container_width=True, type="primary")


# ─── 8. PROCESAR ENVÍO ────────────────────────────────────────────

if submitted:
    if not nombre or not nombre.strip():
        st.error("⚠️ Por favor, escribe tu nombre y apellido.")
    elif tipo_menu == "Menú Entero" and (not primero_sel or not segundo_sel):
        st.error("⚠️ Selecciona un primer plato y un segundo plato.")
    elif tipo_menu == "Medio Menú" and not plato_unico:
        st.error("⚠️ Selecciona un plato.")
    elif len(acomp_sel) > 2:
        st.error("⚠️ Solo puedes elegir un máximo de 2 acompañamientos. Desmarca alguno.")
    else:
        ahora_ts = time.time()
        ultimo_ts = st.session_state.get("last_submit_ts", 0)
        ultimo_nom = st.session_state.get("last_submit_nom", "")
        
        if (ahora_ts - ultimo_ts < 6) and (normalizar_nombre(nombre) == normalizar_nombre(ultimo_nom)):
            st.warning("⏳ Tu reserva se está procesando o ya ha sido enviada. Por favor, no hace falta pulsar dos veces.")
        else:
            st.session_state.last_submit_ts = ahora_ts
            st.session_state.last_submit_nom = nombre

            progress_bar = st.progress(0, text="👨‍🍳 Conectando con la cocina...")
            steps = [
                (25, "🥗 Verificando disponibilidad y cubiertos..."),
                (60, "🍳 Guardando tu menú en cocina..."),
                (90, "🥤 Asignando tu bebida y detalles..."),
                (100, "✨ ¡Reserva registrada con éxito!")
            ]
            for pct, txt in steps:
                time.sleep(0.12)
                progress_bar.progress(pct, text=txt)

            if tipo_menu == "Menú Entero":
                primero_final = primero_sel
                segundo_final = segundo_sel
            else:
                cat, plato_nombre, _ = plato_unico
                primero_final = plato_nombre if cat == "Primero" else ""
                segundo_final = plato_nombre if cat == "Segundo" else ""

            reserva = {
                "Timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Nombre": nombre.strip(),
                "TipoMenu": tipo_menu,
                "Primero": primero_final,
                "Segundo": segundo_final,
                "Acomp1": acomp_sel[0] if len(acomp_sel) >= 1 else "",
                "Acomp2": acomp_sel[1] if len(acomp_sel) >= 2 else "",
                "Ensalada": ensalada_sel or "",
                "Postre": postre_sel or "",
                "Comentarios": comentarios.strip() if comentarios else "",
                "Estado": "Pendiente",
            }

            ok = save_reserva(reserva)

            if ok:
                st.session_state.ultima_reserva = reserva
                st.session_state.trigger_balloons = True
                st.rerun()
            else:
                st.error("❌ Error al guardar la reserva. Inténtalo de nuevo.")

# Resumen de última reserva confirmada
if st.session_state.ultima_reserva:
    ur = st.session_state.ultima_reserva
    st.markdown(f"""
    <div class="reserva-ok">
        <h4 style="margin:0 0 0.3rem 0; color:#0f5132; font-size:1.05rem;">🟢 Reserva confirmada</h4>
        <p style="margin:0; font-size:0.95rem; color:#155724;">
            Registrada con éxito a nombre de: <b>{ur['Nombre']}</b> ({ur['TipoMenu']})
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("👁️ Ver detalle de tu reserva confirmada", expanded=True):
        col_ur1, col_ur2 = st.columns(2)
        with col_ur1:
            if ur.get('Primero'): st.markdown(f"**Primero:** {ur['Primero']}")
            if ur.get('Segundo'): st.markdown(f"**Segundo:** {ur['Segundo']}")
            acomp_u = []
            if ur.get('Acomp1'): acomp_u.append(ur['Acomp1'])
            if ur.get('Acomp2'): acomp_u.append(ur['Acomp2'])
            if acomp_u: st.markdown(f"**Acomp.:** {', '.join(acomp_u)}")
        with col_ur2:
            if ur.get('Ensalada'):
                st.markdown(f"**Ensalada:** {ur['Ensalada']}")
            else:
                st.markdown("**Ensalada:** Sin ensalada")
            if ur.get('Postre'): st.markdown(f"**Postre:** {ur['Postre']}")
            st.markdown("**Bebida:** Incluida")
        st.caption(f"Registrado el {ur['Timestamp']}. Si necesitas cambiarla, puedes cancelarla abajo.")

st.divider()


# ─── 9. SECCIÓN VER / CANCELAR RESERVA ─────────────────────────────

st.subheader("🔍 Ver / Cancelar reserva")

cancel_col1, cancel_col2 = st.columns([3, 1])

with cancel_col1:
    search_nombre = st.text_input(
        "Introduce tu Nombre y Apellido para buscar tu reserva:",
        placeholder="Ej: María García",
        key="search_cancel_input"
    )

with cancel_col2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    buscar_btn = st.button("🔍 Buscar", use_container_width=True)

if buscar_btn and search_nombre:
    found = find_active_reserva(search_nombre)
    if found:
        st.session_state.cancel_reserva_data = found
        st.session_state.cancel_step = "confirm"
    else:
        st.session_state.cancel_reserva_data = None
        st.session_state.cancel_step = "search"
        st.error(f"❌ No se encontró ninguna reserva activa a nombre de **{search_nombre}**.")

if st.session_state.cancel_step == "confirm" and st.session_state.cancel_reserva_data:
    r_data = st.session_state.cancel_reserva_data
    
    st.info(f"📋 **Reserva encontrada a nombre de:** {r_data['Nombre']}")
    
    with st.expander("📄 Ver lo que reservaste", expanded=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write(f"**Tipo de menú:** {r_data['TipoMenu']}")
            if r_data['Primero']: st.write(f"**Primero:** {r_data['Primero']}")
            if r_data['Segundo']: st.write(f"**Segundo:** {r_data['Segundo']}")
            acomp_list = [r_data[a] for a in ['Acomp1', 'Acomp2'] if r_data.get(a)]
            if acomp_list: st.write(f"**Acompañamientos:** {', '.join(acomp_list)}")
        with col_c2:
            if r_data['Ensalada']: st.write(f"**Ensalada:** {r_data['Ensalada']}")
            if r_data['Postre']: st.write(f"**Postre:** {r_data['Postre']}")
            st.write(f"**Fecha reserva:** {r_data['Timestamp']}")
            
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🗑️ Cancelar reserva", type="primary", use_container_width=True):
            ok, msg = cancel_reserva_by_data(r_data)
            if ok:
                st.session_state.cancel_step = "search"
                st.session_state.cancel_reserva_data = None
                if st.session_state.ultima_reserva and st.session_state.ultima_reserva.get('Nombre') == r_data['Nombre']:
                    st.session_state.ultima_reserva = None
                st.success(msg)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(msg)
                
    with col_btn2:
        if st.button("↩️ Volver sin cancelar", use_container_width=True):
            st.session_state.cancel_step = "search"
            st.session_state.cancel_reserva_data = None
            st.rerun()

st.markdown("""
<div class="app-footer">
    Comedor Universitario • Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)
