import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import streamlit as st

# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
st.set_page_config(page_title="T-Bar Bending Stress", page_icon="🔩", layout="wide")

st.title("🔩 Bending Stress in a T-Bar")
st.caption("Flexure formula:  σ = − M · (y − ȳ) / I   |   Units: mm, kN·m, MPa")

# --------------------------------------------------------------------------
# Sidebar inputs
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Section dimensions (mm)")
    b_f = st.number_input("Flange width, b_f", min_value=10.0, value=120.0, step=5.0)
    t_f = st.number_input("Flange thickness, t_f", min_value=1.0, value=20.0, step=1.0)
    h_w = st.number_input("Web height, h_w", min_value=10.0, value=100.0, step=5.0)
    t_w = st.number_input("Web thickness, t_w", min_value=1.0, value=20.0, step=1.0)

    orientation = st.radio("Orientation", ["Flange on top (⊤)", "Flange at bottom (⊥)"])

    st.header("Loading")
    M_kNm = st.number_input(
        "Bending moment, M (kN·m)", value=10.0, step=1.0,
        help="Positive = sagging (top compression, bottom tension). Negative = hogging.",
    )

    st.header("Check (optional)")
    sigma_allow = st.number_input("Allowable stress (MPa)", min_value=1.0, value=150.0, step=10.0)

if t_w > b_f:
    st.error("Web thickness cannot be greater than flange width. Please adjust the inputs.")
    st.stop()

# --------------------------------------------------------------------------
# Section properties (y measured from the bottom of the section)
# --------------------------------------------------------------------------
H = t_f + h_w  # total depth

if orientation.startswith("Flange on top"):
    web_y0, flange_y0 = 0.0, h_w
else:
    flange_y0, web_y0 = 0.0, t_f

A_f, A_w = b_f * t_f, t_w * h_w
yc_f, yc_w = flange_y0 + t_f / 2, web_y0 + h_w / 2

A = A_f + A_w
y_bar = (A_f * yc_f + A_w * yc_w) / A  # centroid from bottom

# Moment of inertia about the neutral axis (parallel-axis theorem)
I_f = b_f * t_f**3 / 12 + A_f * (yc_f - y_bar) ** 2
I_w = t_w * h_w**3 / 12 + A_w * (yc_w - y_bar) ** 2
I = I_f + I_w

# Bending stress along the depth (MPa).  M: kN·m -> N·mm
M = M_kNm * 1e6
y = np.linspace(0, H, 500)
sigma = -M * (y - y_bar) / I

sigma_top, sigma_bot = sigma[-1], sigma[0]
sigma_max = np.max(np.abs(sigma))
c_top, c_bot = H - y_bar, y_bar
Z_top, Z_bot = I / c_top, I / c_bot

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Centroid ȳ (from bottom)", f"{y_bar:.2f} mm")
c2.metric("Moment of inertia, I", f"{I / 1e4:.2f} ×10⁴ mm⁴")
c3.metric("σ at top fibre", f"{sigma_top:.2f} MPa", "Compression" if sigma_top < 0 else "Tension",
          delta_color="off")
c4.metric("σ at bottom fibre", f"{sigma_bot:.2f} MPa", "Compression" if sigma_bot < 0 else "Tension",
          delta_color="off")

if sigma_max <= sigma_allow:
    st.success(f"✅ Safe: max |σ| = {sigma_max:.2f} MPa ≤ allowable {sigma_allow:.0f} MPa "
               f"(utilisation {sigma_max / sigma_allow * 100:.0f}%)")
else:
    st.error(f"⚠️ Unsafe: max |σ| = {sigma_max:.2f} MPa > allowable {sigma_allow:.0f} MPa "
             f"(utilisation {sigma_max / sigma_allow * 100:.0f}%)")

# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5), sharey=True,
                               gridspec_kw={"width_ratios": [1, 1.4]})

# ---- Cross-section ----
ax1.add_patch(Rectangle((-b_f / 2, flange_y0), b_f, t_f, fc="#9ecae1", ec="k", lw=1.5))
ax1.add_patch(Rectangle((-t_w / 2, web_y0), t_w, h_w, fc="#9ecae1", ec="k", lw=1.5))
ax1.axhline(y_bar, color="green", ls="--", lw=1.5, label=f"Neutral axis (ȳ = {y_bar:.1f} mm)")
ax1.plot(0, y_bar, "go", ms=7)
pad = 0.15 * b_f
ax1.set_xlim(-b_f / 2 - pad, b_f / 2 + pad)
ax1.set_ylim(-0.12 * H, 1.12 * H)
ax1.set_aspect("equal", adjustable="datalim")
ax1.set_xlabel("Width (mm)")
ax1.set_ylabel("Height y from bottom (mm)")
ax1.set_title("T-section")
ax1.legend(loc="upper right", fontsize=8)
ax1.grid(alpha=0.3)

# ---- Stress distribution ----
ax2.fill_betweenx(y, 0, sigma, where=sigma >= 0, color="#e34a33", alpha=0.6,
                  interpolate=True, label="Tension")
ax2.fill_betweenx(y, 0, sigma, where=sigma <= 0, color="#3182bd", alpha=0.6,
                  interpolate=True, label="Compression")
ax2.plot(sigma, y, "k", lw=1.8)
ax2.axvline(0, color="k", lw=1)
ax2.axhline(y_bar, color="green", ls="--", lw=1.5)

# Mark flange/web junction
y_junc = h_w if orientation.startswith("Flange on top") else t_f
ax2.axhline(y_junc, color="gray", ls=":", lw=1)

ax2.annotate(f"{sigma_top:.1f} MPa", xy=(sigma_top, H), xytext=(5, -2),
             textcoords="offset points", ha="left" if sigma_top >= 0 else "right",
             va="top", fontsize=9, fontweight="bold")
ax2.annotate(f"{sigma_bot:.1f} MPa", xy=(sigma_bot, 0), xytext=(5, 2),
             textcoords="offset points", ha="left" if sigma_bot >= 0 else "right",
             va="bottom", fontsize=9, fontweight="bold")

lim = 1.35 * sigma_max if sigma_max > 0 else 1
ax2.set_xlim(-lim, lim)
ax2.set_xlabel("Bending stress σ (MPa)")
ax2.set_title("Bending stress distribution")
ax2.legend(loc="upper right" if sigma_top < 0 else "lower right", fontsize=8)
ax2.grid(alpha=0.3)

fig.tight_layout()
st.pyplot(fig)

# --------------------------------------------------------------------------
# Detailed working
# --------------------------------------------------------------------------
with st.expander("📘 Show calculation steps"):
    st.markdown("**1. Areas**")
    st.latex(rf"A_f = {b_f:.0f}\times{t_f:.0f} = {A_f:.0f}\ \text{{mm}}^2,\quad "
             rf"A_w = {t_w:.0f}\times{h_w:.0f} = {A_w:.0f}\ \text{{mm}}^2")
    st.markdown("**2. Centroid (from bottom)**")
    st.latex(rf"\bar y = \frac{{A_f y_f + A_w y_w}}{{A_f + A_w}} = {y_bar:.2f}\ \text{{mm}}")
    st.markdown("**3. Moment of inertia (parallel-axis theorem)**")
    st.latex(r"I = \sum\left(\frac{b h^3}{12} + A d^2\right)"
             rf" = {I:,.0f}\ \text{{mm}}^4")
    st.markdown("**4. Bending stress**")
    st.latex(r"\sigma = -\frac{M\,(y-\bar y)}{I}")
    st.markdown(
        f"- Distance to top fibre: **{c_top:.2f} mm** → Z_top = I/c = **{Z_top:,.0f} mm³**\n"
        f"- Distance to bottom fibre: **{c_bot:.2f} mm** → Z_bot = I/c = **{Z_bot:,.0f} mm³**\n"
        f"- σ_top = **{sigma_top:.2f} MPa**, σ_bottom = **{sigma_bot:.2f} MPa**"
    )
    st.caption("Sign convention: tension is positive, compression is negative.")