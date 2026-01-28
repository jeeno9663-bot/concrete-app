import streamlit as st
import pandas as pd
import joblib
import time
import numpy as np
import plotly.graph_objects as go
import io
from PIL import Image
from fpdf import FPDF

# -------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
# -------------------------------------------
st.set_page_config(page_title="ระบบทำนายกำลังอัดคอนกรีต/ดินซีเมนต์", page_icon="🏗️", layout="wide")

if 'calculated' not in st.session_state: st.session_state['calculated'] = False

try: model = joblib.load('concrete_model.pkl'); model_status = "System Ready"
except: st.error("Error loading model"); model_status = "Error"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif; }
    div.stButton > button { background-color: #2c3e50; color: white; border-radius: 5px; width: 100%; }
    .validation-box { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------
# ฟังก์ชัน PDF แบบราชการ (Official Form)
# -------------------------------------------
class PDF(FPDF):
    def header(self):
        try: self.image('image_19.png', 10, 8, 20)
        except: pass
        
        try: self.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
        except: pass
        
        self.set_font('THSarabunNew', '', 12)
        self.cell(0, 5, 'แบบ บ. 216', 0, 1, 'R')
        
        self.set_font('THSarabunNew', 'B', 20)
        self.cell(0, 10, 'รายงานผลการทดสอบแรงอัดของแท่งคอนกรีต/ดินซีเมนต์', 0, 1, 'C')
        self.set_font('THSarabunNew', '', 16)
        self.cell(0, 8, 'สำนักวิเคราะห์และตรวจสอบ (AI System Simulation)', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('THSarabunNew', '', 12)
        self.cell(0, 10, f'หน้า {self.page_no()} / {{nb}}', 0, 0, 'R')

def create_official_pdf(inputs, pred_ksc, sample_type):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    try:
        pdf.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
        pdf.add_font('THSarabunNew', 'B', 'THSarabunNew.ttf', uni=True)
        font = 'THSarabunNew'
    except: font = 'Arial'

    # --- Header Info ---
    pdf.set_font(font, '', 14)
    line_h = 7
    project_name = "โครงการก่อสร้างอาคารทดสอบ (AI Simulation Project)"
    contract_no = "AI-2024/001"
    owner = "มหาวิทยาลัยเทคโนโลยีราชมงคลล้านนา"
    date_test = time.strftime('%d/%m/%Y')
    
    pdf.cell(30, line_h, "โครงการ:", 0, 0)
    pdf.cell(110, line_h, project_name, "B", 0)
    pdf.cell(20, line_h, "  เลขที่:", 0, 0)
    pdf.cell(30, line_h, contract_no, "B", 1)
    
    pdf.cell(30, line_h, "เจ้าของงาน:", 0, 0)
    pdf.cell(110, line_h, owner, "B", 0)
    pdf.cell(20, line_h, "  วันที่:", 0, 0)
    pdf.cell(30, line_h, date_test, "B", 1)
    
    pdf.cell(30, line_h, "ส่วนผสม:", 0, 0)
    pdf.cell(160, line_h, f"ปูน {inputs['Cement']} | สแลก {inputs['Blast Furnace Slag']} | เถ้าลอย {inputs['Fly Ash']} | น้ำ {inputs['Water']} (กก./ลบ.ม.)", "B", 1)
    pdf.ln(5)

    # --- Table ---
    pdf.set_font(font, 'B', 14)
    w = [15, 60, 25, 30, 30, 30] 
    h = 10
    headers = ["ลำดับ", "ลักษณะตัวอย่าง", "อายุ (วัน)", "น้ำหนัก (กรัม)", "แรงกด (kN)", "แรงอัด (ksc)"]
    for i in range(len(headers)): pdf.cell(w[i], h, headers[i], 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font(font, '', 14)
    sample_desc = sample_type.split(' ')[0]
    
    # Mockup 3 Samples
    factors = [1.0, 1.01, 0.99]
    for i, fac in enumerate(factors, 1):
        pdf.cell(w[0], h, str(i), 1, 0, 'C')
        pdf.cell(w[1], h, sample_desc, 1, 0, 'L')
        pdf.cell(w[2], h, str(int(inputs['Age'])), 1, 0, 'C')
        pdf.cell(w[3], h, "2,450", 1, 0, 'R')
        pdf.cell(w[4], h, f"{pred_ksc * 1.5 * fac:.1f}", 1, 0, 'R')
        pdf.cell(w[5], h, f"{pred_ksc * fac:.2f}", 1, 1, 'R')
    
    pdf.set_font(font, 'B', 14)
    pdf.cell(sum(w[:5]), h, "ค่าเฉลี่ย (Average)", 1, 0, 'R')
    pdf.cell(w[5], h, f"{pred_ksc:.2f}", 1, 1, 'R')
    pdf.ln(10)

    # --- Signatures ---
    pdf.set_font(font, '', 14)
    pdf.cell(0, 8, "หมายเหตุ: ผลการทดสอบนี้ได้จากการจำลองด้วยระบบปัญญาประดิษฐ์ (AI Simulation)", 0, 1, 'L')
    pdf.ln(15)
    
    col_w = 63
    y_sig = pdf.get_y()
    
    labels = [("ผู้ทดสอบ", "( นายทดสอบ ระบบ )"), ("วิศวกรโยธา", "( นายวิศวกร คุมงาน )"), ("ผู้อนุมัติ", "( ผศ.ดร.อาจารย์ ที่ปรึกษา )")]
    for i, (role, name) in enumerate(labels):
        pdf.set_xy(10 + col_w*i, y_sig)
        pdf.cell(col_w, 5, "............................................", 0, 1, 'C')
        pdf.set_xy(10 + col_w*i, y_sig + 6)
        pdf.cell(col_w, 5, name, 0, 1, 'C')
        pdf.set_xy(10 + col_w*i, y_sig + 12)
        pdf.cell(col_w, 5, role, 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# -------------------------------------------
# กราฟและ 3D
# -------------------------------------------
def plot_3d_sample(ksc, shape_type):
    fig = go.Figure()
    intensity = min(1.0, ksc / 800)
    if "ดิน" in shape_type: r,g,b = int(101-(intensity*20)), int(78-(intensity*20)), int(60-(intensity*20)); base_color = f'rgb({r},{g},{b})'; cap_color = f'rgb({r-10},{g-10},{b-10})'
    else: g = int(200-(intensity*100)); base_color = f'rgb({g},{g},{g})'; cap_color = f'rgb({g-20},{g-20},{g-20})'
    
    if "ทรงกระบอก" in shape_type:
        theta, z = np.linspace(0, 2*np.pi, 50), np.linspace(0, 2, 20); T, Z = np.meshgrid(theta, z)
        fig.add_trace(go.Surface(x=np.cos(T), y=np.sin(T), z=Z, colorscale=[[0, base_color], [1, base_color]], showscale=False))
        fig.add_trace(go.Surface(x=np.cos(T)*np.linspace(0,1,10)[:,None], y=np.sin(T)*np.linspace(0,1,10)[:,None], z=np.zeros_like(T)+2, colorscale=[[0, cap_color], [1, cap_color]], showscale=False))
    elif "ลูกบาศก์" in shape_type:
        fig.add_trace(go.Mesh3d(x=[0,1,1,0,0,1,1,0], y=[0,0,1,1,0,0,1,1], z=[0,0,0,0,1,1,1,1], color=base_color, i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6]))
    
    fig.update_layout(title=f"Sample: {shape_type}", scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)), height=350, margin=dict(l=0,r=0,b=0,t=30))
    return fig

def plot_stress_strain(fc):
    e = np.linspace(0, 0.0035, 100)
    s = np.where(e<=0.002, fc*(2*(e/0.002)-(e/0.002)**2), fc-((fc*0.15)/0.0015)*(e-0.002))
    fig = go.Figure(go.Scatter(x=e, y=s, mode='lines', line=dict(color='#2c3e50', width=3)))
    fig.update_layout(title="Stress-Strain", height=300)
    return fig

def plot_sens(model, base, col, name):
    try:
        val = base[col].values[0]; x = np.linspace(val*0.5, val*1.5, 20)
        temp = pd.concat([base]*20, ignore_index=True); temp[col] = x; y = model.predict(temp)*10.197
        fig = go.Figure([go.Scatter(x=x, y=y, mode='lines'), go.Scatter(x=[val], y=[model.predict(base)[0]*10.197], mode='markers', marker=dict(size=10, color='red'))])
        fig.update_layout(title=f"Sensitivity: {name}", height=300); return fig
    except: return go.Figure()

# -------------------------------------------
# Sidebar
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดพารามิเตอร์")
    try: st.image("image_19.png", width=150)
    except: pass
    st.markdown("---")
    c = st.number_input("Cement", 0.0, 1000.0, 350.0); s = st.number_input("Slag", 0.0, 1000.0, 0.0)
    f = st.number_input("FlyAsh", 0.0, 1000.0, 0.0); w = st.number_input("Water", 0.0, 500.0, 180.0)
    sp = st.number_input("Superplasticizer", 0.0, 100.0, 0.0); ca = st.number_input("Coarse Agg", 0.0, 2000.0, 1000.0)
    fa = st.number_input("Fine Agg", 0.0, 2000.0, 800.0); age = st.slider("Age (Days)", 1, 365, 28)
    
    if st.button("🚀 คำนวณ", type="primary"): st.session_state['calculated'] = True
    
    st.markdown("---")
    enable_val = st.checkbox("Validation Mode")
    act_ksc = st.number_input("Lab Result (ksc)", 0.0) if enable_val else 0.0

# -------------------------------------------
# Main Content
# -------------------------------------------
st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**Status:** {model_status}")
st.markdown("---")

if st.session_state['calculated']:
    input_data = pd.DataFrame([[c, s, f, w, sp, ca, fa, age]], columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    base_ksc = model.predict(input_data)[0] * 10.197
    cost = (c*2.5 + s*1.5 + f*1.0 + w*0.015 + sp*40 + ca*0.35 + fa*0.30)
    
    c1, c2 = st.columns([1, 1])
    with c2:
        shape = st.radio("รูปแบบตัวอย่าง:", ["ก้อนดินซีเมนต์ (ทรงกระบอก)", "คอนกรีต (ลูกบาศก์)", "คอนกรีต (ทรงกระบอก)"])
        fac = 1.2 if "ลูกบาศก์" in shape else 1.0
        final_ksc = base_ksc * fac
        
        st.plotly_chart(plot_3d_sample(final_ksc, shape), use_container_width=True)
        
        pdf_bytes = create_official_pdf(input_data.iloc[0], final_ksc, shape)
        st.download_button("📄 พิมพ์รายงาน (แบบ บ.216)", pdf_bytes, "official_report.pdf", "application/pdf", type="primary")

    with c1:
        st.subheader("ผลการทำนาย")
        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=final_ksc, title={'text':"ksc"}, gauge={'axis':{'range':[None,1200]}, 'bar':{'color':"#2c3e50"}}))
        fig_g.update_layout(height=250, margin=dict(l=20,r=20,t=30,b=20)); st.plotly_chart(fig_g, use_container_width=True)
        
        # =======================================================
        # ✅ กลับมาใช้ w/b (Water / Binder) ตามที่คุณต้องการ
        # =======================================================
        total_binder = c + s + f
        wb_ratio = w / total_binder if total_binder > 0 else 0
        
        if wb_ratio > 0.5: st.warning(f"⚠️ w/b = {wb_ratio:.3f} (>0.5)")
        else: st.success(f"✅ w/b = {wb_ratio:.3f}")

    if enable_val and act_ksc > 0:
        err = abs(act_ksc - final_ksc)/act_ksc * 100
        st.info(f"Compare: AI={final_ksc:.2f} vs Lab={act_ksc:.2f} (Error {err:.2f}%)")

    st.markdown("---")
    r1, r2 = st.columns(2)
    with r1: st.plotly_chart(plot_stress_strain(final_ksc), use_container_width=True)
    with r2: st.bar_chart(pd.DataFrame({"Item":["C","S","F","W","SP","CA","FA"], "Qty":[c,s,f,w,sp,ca,fa]}).set_index("Item"))
    
    st.markdown("---")
    with st.expander("📝 รายการคำนวณ (Calculation Sheet)"):
        st.latex(rf"Binder = {c} + {s} + {f} = {total_binder} \; kg/m^3")
        st.latex(rf"w/b = \frac{{{w}}}{{{total_binder}}} = \mathbf{{{wb_ratio:.3f}}}")
        st.latex(rf"Final Strength = {final_ksc:.2f} \; ksc")

    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1: 
        tv = st.selectbox("Sensitivity:", ["Cement", "Water", "Age"])
        mv = {"Cement":"Cement", "Water":"Water", "Age":"Age"}
        st.plotly_chart(plot_sens(model, input_data, mv[tv], tv), use_container_width=True)
    with s2:
        st.metric("Cost (THB/m3)", f"{cost:,.2f}")
else:
    st.info("👈 กดปุ่มคำนวณเพื่อเริ่มใช้งาน")
