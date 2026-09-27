import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

# --- CONFIGURACIÓN DE PÁGINA Y ENCABEZADO ---
st.set_page_config(page_title="Análisis y Diseño ELR", layout="wide")
st.title("Cálculo Estructural y Diseño por ELR")

st.markdown("""
**Diseñado por Gómez Arizmendi Diego**  
**Mecánica de materiales 2, grupo 6**  

*27 de septiembre de 2026*
""")
st.markdown("Automatización de diagramas de Cortante (V), Momento (M) y diseño de sección de concreto.")

# ==========================================
# 1. MÓDULO DE ANÁLISIS ESTRUCTURAL
# ==========================================
st.sidebar.header("1. Análisis Estructural")
tipo_apoyo = st.sidebar.selectbox("Tipo de Viga", ["Simplemente Apoyada", "Voladizo (Empotrada)"])
L = st.sidebar.number_input("Claro de la viga, L (m)", value=7.0, step=0.5)

st.sidebar.subheader("Cargas sin factorizar")
tipo_carga = st.sidebar.selectbox("Distribución de Carga", ["Uniformemente Distribuida", "Puntual al Centro / Extremo"])
w_cm = st.sidebar.number_input("Carga Muerta, CM (t/m o t)", value=2.64, step=0.1)
w_cv = st.sidebar.number_input("Carga Viva, CV (t/m o t)", value=0.93, step=0.1)

# Factorización de cargas (1.5 CM + 1.7 CV)
wu = 1.5 * w_cm + 1.7 * w_cv
st.sidebar.info(f"**Carga Última Factorizada:**\nWu = {wu:.2f} (t/m o t)")

x = np.linspace(0, L, 500)
V = np.zeros_like(x)
M = np.zeros_like(x)

if tipo_apoyo == "Simplemente Apoyada":
    if tipo_carga == "Uniformemente Distribuida":
        V = wu * L / 2 - wu * x
        M = (wu * x / 2) * (L - x)
        texto_rx = f"Ra = {wu*L/2:.2f} t | Rb = {wu*L/2:.2f} t"
    else: 
        V = np.where(x < L/2, wu/2, -wu/2)
        M = np.where(x <= L/2, (wu/2)*x, (wu/2)*(L-x))
        texto_rx = f"Ra = {wu/2:.2f} t | Rb = {wu/2:.2f} t"
else: 
    if tipo_carga == "Uniformemente Distribuida":
        V = wu * (L - x)
        M = -(wu / 2) * (L - x)**2
        texto_rx = f"Ra = {wu*L:.2f} t | Ma = {(wu*L**2)/2:.2f} t-m"
    else: 
        V = np.full_like(x, wu)
        M = -wu * (L - x)
        texto_rx = f"Ra = {wu:.2f} t | Ma = {wu*L:.2f} t-m"

Mu_calc = np.max(np.abs(M))

st.subheader("I. Diagramas de Elementos Mecánicos")
st.markdown(f"**Reacciones en los apoyos:** {texto_rx}")

fig_est, (ax_V, ax_M) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax_V.plot(x, V, color='navy', lw=2)
ax_V.fill_between(x, V, 0, alpha=0.3, color='steelblue')
ax_V.axhline(0, color='black', lw=1)
ax_V.set_ylabel("Cortante, V (t)", weight='bold')
ax_V.grid(True, linestyle='--', alpha=0.6)

ax_M.plot(x, M, color='darkred', lw=2)
ax_M.fill_between(x, M, 0, alpha=0.3, color='salmon')
ax_M.axhline(0, color='black', lw=1)
ax_M.set_ylabel("Momento, M (t-m)", weight='bold')
ax_M.set_xlabel("Longitud (m)", weight='bold')
ax_M.grid(True, linestyle='--', alpha=0.6)
if tipo_apoyo == "Simplemente Apoyada": ax_M.invert_yaxis() 

st.pyplot(fig_est)

# ==========================================
# 2. MÓDULO DE DISEÑO DE SECCIÓN
# ==========================================
st.sidebar.markdown("---")
st.sidebar.header("2. Geometría y Materiales")
h = st.sidebar.number_input("Altura de la viga, h (cm)", value=60.0, step=1.0)
b = st.sidebar.number_input("Base de la viga, b (cm)", value=35.0, step=1.0)
r = st.sidebar.number_input("Recubrimiento, r (cm)", value=5.0, step=0.5)
fc = st.sidebar.number_input("f'c (kg/cm²)", value=250.0, step=10.0)
fy = st.sidebar.number_input("fy (kg/cm²)", value=4200.0, step=100.0)
Es = 2.1e6

d = h - r
ecu = 0.003
fbc = 0.85 * fc 
beta1 = 0.85 if fc <= 300 else max(0.65, 1.05 - (fc / 1400))
ey = fy / Es

st.sidebar.markdown("---")
st.sidebar.header("3. Propuesta de Acero (As)")
modo_as = st.sidebar.radio("Método de ingreso:", ["Por cuantía (ρ %)", "Área directa (cm²)"])
if modo_as == "Por cuantía (ρ %)":
    rho_input = st.sidebar.number_input("Porcentaje de acero, ρ (%)", value=1.0, step=0.1)
    As_input = (rho_input / 100) * b * d
    st.sidebar.success(f"As Calculado = {As_input:.2f} cm²")
else:
    As_input = st.sidebar.number_input("Área As (cm²)", value=19.25, step=0.5)

if As_input > 0:
    a = (As_input * fy) / (fbc * b)
    c = a / beta1
    es = ecu * (d - c) / c
    if es >= ey:
        Mn = As_input * fy * (d - a / 2)
        FR = 0.9
        falla = "Dúctil (El acero fluye)"
    else:
        A_eq = fbc * beta1 * b
        B_eq = As_input * ecu * Es
        C_eq = - As_input * ecu * Es * d
        c = (-B_eq + np.sqrt(max(0, B_eq**2 - 4 * A_eq * C_eq))) / (2 * A_eq)
        a = beta1 * c
        fs = ecu * Es * (d - c) / c
        Mn = As_input * fs * (d - a / 2)
        FR = 0.65
        falla = "Frágil (Aplastamiento)"
    
    Mn = Mn / 1e5
    MR = FR * Mn
else:
    Mn = MR = c = es = a = 0
    falla = "N/A"

st.markdown("---")
st.subheader("II. Comprobación y Diseño Transversal")

col1, col2, col3 = st.columns(3)
col1.metric("Demanda: Momento Último (Mu)", f"{Mu_calc:.2f} t-m")
col2.metric("Capacidad: Momento Resistente (MR)", f"{MR:.2f} t-m")
col3.metric("Tipo de Falla", falla)

if MR > 0:
    ratio = Mu_calc / MR
    if 0.9 <= ratio <= 1.0:
        st.success(f"**Ratio = {ratio:.3f}** ➔ Diseño Óptimo (0.9 ≤ Ratio ≤ 1.0)")
    elif ratio < 0.9:
        st.warning(f"**Ratio = {ratio:.3f}** ➔ Sobrediseñado (Ratio < 0.9)")
    else:
        st.error(f"**Ratio = {ratio:.3f}** ➔ Falla Estructural (Ratio > 1.0)")

varillas_comerciales = {
    "No. 3 (3/8\")": 0.71, "No. 4 (1/2\")": 1.27, "No. 5 (5/8\")": 1.99, 
    "No. 6 (3/4\")": 2.85, "No. 8 (1\")": 5.07, "No. 10 (1.25\")": 7.92, 
    "No. 12 (1.5\")": 11.40, "No. 14 (1.75\")": 15.52
}

col_v1, col_v2 = st.columns([1, 2])

with col_v1:
    varilla_sel = st.selectbox("Selecciona varilla:", list(varillas_comerciales.keys()), index=4)
    area_v = varillas_comerciales[varilla_sel]
    num_varillas = int(np.ceil(As_input / area_v))
    st.info(f"Para cubrir **{As_input:.2f} cm²** se colocan:\n\n**{num_varillas} varillas** {varilla_sel}\n\nÁrea real = **{num_varillas * area_v:.2f} cm²**")

with col_v2:
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    ax2.add_patch(Rectangle((0, 0), b, h, fill=None, edgecolor='black', lw=2.5))
    espaciamiento = b / (num_varillas + 1)
    
    for i in range(1, num_varillas + 1):
        ax2.add_patch(Circle((i * espaciamiento, r), radius=b*0.03, edgecolor='darkred', facecolor='none', lw=2))
    
    ax2.plot([-b*0.1, b*1.1], [h-c, h-c], color='green', linestyle='-.', lw=1.5, label=f'Eje Neutro (c={c:.2f})')
    ax2.plot([0, b], [h-a, h-a], color='blue', linestyle=':', lw=1.5, label=f'Bloque (a={a:.2f})')
    
    # Acotaciones base y altura
    ax2.text(b/2, -h*0.08, f'b={b} cm', ha='center', weight='bold')
    ax2.text(-b*0.12, h/2, f'h={h} cm', va='center', ha='right', weight='bold')
    
    # Nuevas acotaciones de d y r
    ax2.plot([0, b*1.15], [r, r], color='gray', linestyle='--', lw=0.8)
    ax2.annotate('', xy=(b*1.1, h), xytext=(b*1.1, r), arrowprops=dict(arrowstyle='<->', color='navy'))
    ax2.text(b*1.15, (h+r)/2, f'd={d} cm', va='center', ha='left', color='navy', weight='bold')
    
    ax2.annotate('', xy=(b*1.1, r), xytext=(b*1.1, 0), arrowprops=dict(arrowstyle='<->', color='darkorange'))
    ax2.text(b*1.15, r/2, f'r={r} cm', va='center', ha='left', color='darkorange', weight='bold')
    
    ax2.set_xlim(-b*0.3, b*1.6) 
    ax2.set_ylim(-h*0.15, h*1.1)
    ax2.axis('off')
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize='small')
    st.pyplot(fig2)

# ==========================================
# 3. GRÁFICA DE COMPORTAMIENTO
# ==========================================
st.markdown("---")
st.subheader("III. Gráfica de Comportamiento de la Sección")

c_bal = d * ecu / (ecu + ey)
a_bal = beta1 * c_bal
As_bal = (fbc * a_bal * b) / fy

As_vals = np.linspace(0.1, 140, 200)
Mn_vals = []
MR_vals = []

for As_iter in As_vals:
    a_iter = (As_iter * fy) / (fbc * b)
    c_iter = a_iter / beta1
    es_iter = ecu * (d - c_iter) / c_iter
    
    if es_iter >= ey:
        Mn_iter = As_iter * fy * (d - a_iter / 2)
        FR_iter = 0.9
    else:
        A_eq = fbc * beta1 * b
        B_eq = As_iter * ecu * Es
        C_eq = - As_iter * ecu * Es * d
        c_iter_f = (-B_eq + np.sqrt(max(0, B_eq**2 - 4 * A_eq * C_eq))) / (2 * A_eq)
        a_iter_f = beta1 * c_iter_f
        fs_iter = ecu * Es * (d - c_iter_f) / c_iter_f
        Mn_iter = As_iter * fs_iter * (d - a_iter_f / 2)
        FR_iter = 0.65
        
    Mn_vals.append(Mn_iter / 1e5)
    MR_vals.append((FR_iter * Mn_iter) / 1e5)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.plot(As_vals, Mn_vals, label='Mn (t-m)', color='#4A7BC7')
ax3.plot(As_vals, MR_vals, label='MR (t-m)', color='#C0504D')
ax3.axvline(x=As_bal, color='red', linestyle='--', linewidth=1.5, label='As Balanceado')

if As_input > 0:
    ax3.plot(As_input, MR, marker='*', markersize=15, color='gold', markeredgecolor='black', label=f'Diseño actual (As={As_input:.2f})')

ax3.grid(True, linestyle='--', linewidth=0.5)
ax3.set_xlabel('Área de acero As (cm²)', weight='bold')
ax3.set_ylabel('Momento (t-m)', weight='bold')
ax3.legend(loc='lower right')

st.pyplot(fig3)