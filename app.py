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

try: model = joblib.load('concrete_model.pkl'); model_status = "ระบบพร้อมใช้งาน (System Ready)"
except: st.error("Error loading model"); model_status = "Error"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif; }
    div.stButton > button { background-color: #2c3e50; color: white; border-radius: 5px; width: 100%; }
    .validation-box { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-top: 20px; }
    .design-box { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #1976d2; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------
# ฟังก์ชัน PDF (Official - No Stamp)
# -------------------------------------------
class PDF(FPDF):
    def header(self):
        try: self.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
        except: self.set_font('Arial', '', 10)
        
        self.set_font('THSarabunNew', '', 12)
        self.cell(0, 5, 'FERROCRETE   216   ไม่ผสมหิน', 0, 1, 'R')
        self.ln(5)
        
        try: self.set_font('THSarabunNew', '', 22) # ใช้ตัวธรรมดาแต่ขนาดใหญ่แทนตัวหนา
        except: self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'สำนักวิเคราะห์และตรวจสอบ กรมทางหลวง', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        try: self.set_font('THSarabunNew', '', 12)
        except: self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'หน้า {self.page_no()} / {{nb}}', 0, 0, 'R')

def create_official_pdf(inputs, pred_ksc, sample_type):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    try: pdf.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True); font='THSarabunNew'
    except: font='Arial'

    pdf.set_font(font, '', 14)
    lh = 7
    
    # Header Info
    pdf.cell(30, lh, "อันดับทดลองที่:", 0, 0); pdf.cell(60, lh, "CO - 129/2567 (AI Sim)", "B", 0)
    pdf.cell(30, lh, "วันที่รับตัวอย่าง:", 0, 0); pdf.cell(70, lh, f"{time.strftime('%d/%m/%Y')}", "B", 1)
    
    pdf.cell(30, lh, "เจ้าของตัวอย่าง:", 0, 0); pdf.cell(60, lh, "มหาวิทยาลัยเทคโนโลยีราชมงคลล้านนา", "B", 0)
    pdf.cell(30, lh, "หนังสือที่:", 0, 0); pdf.cell(70, lh, "001/2567", "B", 1)
    
    pdf.cell(30, lh, "หน่วยงาน:", 0, 0)
    pdf.cell(160, lh, f"โครงการทดสอบคอนกรีตด้วย AI (ปูน {inputs['Cement']:.0f} | น้ำ {inputs['Water']:.0f})", "B", 1)
    pdf.ln(5)

    pdf.set_font(font, '', 18)
    pdf.cell(0, 10, "รายงานการทดลองแรงอัดของแท่งคอนกรีต", 0, 1, 'C')

    # Table
    pdf.set_font(font, '', 12)
    col_w = [10, 10, 40, 15, 25, 20, 25, 25]
    row_h = 8
    headers = ["ที่", "แท่งที่", "ลักษณะตัวอย่าง", "อายุ", "ขนาด (ซม.)", "นน. (กรัม)", "แรงกด (kN)", "ksc"]
    
    pdf.set_fill_color(240, 240, 240)
    for i, h in enumerate(headers): pdf.cell(col_w[i], row_h, h, 1, 0, 'C', 1)
    pdf.ln()
    
    sample_name = "ทรงกระบอก" if "ทรงกระบอก" in sample_type else "ลูกบาศก์"
    size_str = "15x30" if "ทรงกระบอก" in sample_type else "15x15x15"
    factors = [1.01, 0.99, 1.00]
    
    for i in range(3):
        ksc_val = pred_ksc * factors[i]
        load_kn = (ksc_val * 176.7 * 9.81) / 1000 
        pdf.cell(col_w[0], row_h, "1" if i==0 else "", 1, 0, 'C')
        pdf.cell(col_w[1], row_h, str(i+1), 1, 0, 'C')
        pdf.cell(col_w[2], row_h, sample_name, 1, 0, 'C')
        pdf.cell(col_w[3], row_h, str(int(inputs['Age'])), 1, 0, 'C')
        pdf.cell(col_w[4], row_h, size_str, 1, 0, 'C')
        pdf.cell(col_w[5], row_h, "12,500", 1, 0, 'R')
        pdf.cell(col_w[6], row_h, f"{load_kn:.1f}", 1, 0, 'R')
        pdf.cell(col_w[7], row_h, f"{ksc_val:.1f}", 1, 1, 'R')
        
    pdf.cell(sum(col_w[:7]), row_h, "ค่าเฉลี่ย (Average)", 1, 0, 'R')
    pdf.cell(col_w[7], row_h, f"{pred_ksc:.1f}", 1, 1, 'R')
    pdf.ln(10)

    # Footer (Signatures - No Stamp)
    pdf.set_font(font, '', 14)
    pdf.ln(20) # เว้นที่ว่างแทนตราประทับ
    
    y_sig = pdf.get_y()
    pdf.set_font(font, '', 12)
    pdf.cell(60, 5, "พิจารณาเฉพาะค่าแรงอัดที่ระบุ", 0, 1, 'L')
    
    pdf.set_xy(80, y_sig + 10)
    pdf.cell(60, 5, "............................................", 0, 1, 'C')
    pdf.set_xy(80, y_sig + 16)
    pdf.cell(60, 5, "( ............................................ )", 0, 1, 'C')
    pdf.set_xy(80, y_sig + 22)
    pdf.cell(60, 5, "ผู้ตรวจสอบ", 0, 1, 'C')
    
    pdf.set_y(-20)
    pdf.set_font(font, '', 10)
    pdf.cell(0, 5, "ผลการวิเคราะห์นี้รับรองเฉพาะตัวอย่างที่ได้รับเท่านั้น", 0, 0, 'C')

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
    fig.update_layout(title="Stress-Strain Simulation", height=300)
    return fig

def plot_sens(model, base, col, name):
    try:
        val = base[col].values[0]; x = np.linspace(val*0.5, val*1.5, 20)
        temp = pd.concat([base]*20, ignore_index=True); temp[col] = x; y = model.predict(temp)*10.197
        fig = go.Figure([go.Scatter(x=x, y=y, mode='lines'), go.Scatter(x=[val], y=[model.predict(base)[0]*10.197], mode='markers', marker=dict(size=10, color='red'))])
        fig.update_layout(title=f"Sensitivity: {name}", height=300); return fig
    except: return go.Figure()

# -------------------------------------------
# Logic ออกแบบส่วนผสม (Auto-Design)
# -------------------------------------------
def auto_design_mix(target_ksc, binder_type):
    target_mpa = target_ksc / 10.197
    est_wb = max(0.25, min(0.7, 0.85 - (0.01 * target_mpa)))
    water = 185.0
    total_binder = water / est_wb
    
    c, s, f = 0, 0, 0
    if "ปูนซีเมนต์ล้วน" in binder_type: c = total_binder
    elif "เถ้าลอย" in binder_type: c = total_binder * 0.8; f = total_binder * 0.2
    elif "สแลก" in binder_type: c = total_binder * 0.6; s = total_binder * 0.4
    
    agg_weight = 2350 - (total_binder + water + 5)
    ca = agg_weight * 0.60
    fa = agg_weight * 0.40
    return c, s, f, water, 5.0, ca, fa, 28

# -------------------------------------------
# Sidebar
# -------------------------------------------
with st.sidebar:
    st.title("เมนูหลัก")
    try: st.image("image_19.png", width=150)
    except: pass
    
    app_mode = st.radio("โหมดการทำงาน:", ["1. ทำนาย (Predict)", "2. ออกแบบ (Auto-Design)"])
    st.markdown("---")
    
    c, s, f, w, sp, ca, fa, age = 0,0,0,0,0,0,0,28
    
    if app_mode == "1. ทำนาย (Predict)":
        st.header("กรอกปริมาณวัสดุ")
        c = st.number_input("ปูนซีเมนต์", 0.0, 1000.0, 350.0)
        s = st.number_input("สแลก", 0.0, 1000.0, 0.0)
        f = st.number_input("เถ้าลอย", 0.0, 1000.0, 0.0)
        w = st.number_input("น้ำ", 0.0, 500.0, 180.0)
        sp = st.number_input("สารลดน้ำ", 0.0, 100.0, 0.0)
        ca = st.number_input("หิน", 0.0, 2000.0, 1000.0)
        fa = st.number_input("ทราย", 0.0, 2000.0, 800.0)
        age = st.slider("อายุบ่ม (วัน)", 1, 365, 28)
        if st.button(" คำนวณ", type="primary"): st.session_state['calculated'] = True
            
    else:
        st.header("เป้าหมาย")
        target_ksc = st.number_input("กำลังอัดที่ต้องการ (ksc)", 100.0, 800.0, 350.0)
        binder_opt = st.selectbox("สูตรผสม:", ["ปูนซีเมนต์ล้วน (OPC)", "ผสมเถ้าลอย (Fly Ash 20%)", "ผสมสแลก (Slag 40%)"])
        if st.button("✨ ออกแบบส่วนผสม", type="primary"):
            st.session_state['calculated'] = True
            c, s, f, w, sp, ca, fa, age = auto_design_mix(target_ksc, binder_opt)
            st.session_state['design_res'] = (c, s, f, w, sp, ca, fa, age, target_ksc, binder_opt)

    st.markdown("---")
    enable_val = st.checkbox("Validation Mode")
    act_ksc = st.number_input("Lab Result (ksc)", 0.0) if enable_val else 0.0

# -------------------------------------------
# Main Content
# -------------------------------------------
st.title(" ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

if st.session_state['calculated']:
    
    # ถ้ามาจาก Auto-Design ให้ดึงค่าที่คำนวณไว้
    if app_mode == "2. ออกแบบ (Auto-Design)" and 'design_res' in st.session_state:
        c, s, f, w, sp, ca, fa, age, target_ksc, binder_opt = st.session_state['design_res']
        st.markdown(f"""<div class="design-box"><h3> ผลการออกแบบ (Auto-Design)</h3>เป้าหมาย: <b>{target_ksc:.0f} ksc</b> | สูตร: <b>{binder_opt}</b></div>""", unsafe_allow_html=True)

    input_data = pd.DataFrame([[c, s, f, w, sp, ca, fa, age]], columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    base_ksc = model.predict(input_data)[0] * 10.197
    
    # ✅ แก้ NameError: ใช้ตัวแปร c, s, f แทน cement, slag...
    cost = (c*2.5 + s*1.5 + f*1.0 + w*0.015 + sp*40 + ca*0.35 + fa*0.30)
    
    c1, c2 = st.columns([1, 1])
    with c2:
        st.markdown("#####  เลือกรูปแบบตัวอย่าง")
        shape = st.radio("", ["ก้อนดินซีเมนต์ (ทรงกระบอก)", "คอนกรีต (ลูกบาศก์)", "คอนกรีต (ทรงกระบอก)"], label_visibility="collapsed")
        
        fac = 1.2 if "ลูกบาศก์" in shape else 1.0
        final_ksc = base_ksc * fac
        
        st.plotly_chart(plot_3d_sample(final_ksc, shape), use_container_width=True)
        
        pdf_bytes = create_official_pdf(input_data.iloc[0], final_ksc, shape)
        st.download_button("📄 พิมพ์รายงาน (แบบ บ.216)", pdf_bytes, "official_report.pdf", "application/pdf", type="primary")

    with c1:
        st.subheader("ผลการวิเคราะห์ (AI)")
        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=final_ksc, title={'text':"ksc"}, gauge={'axis':{'range':[None,1200]}, 'bar':{'color':"#2c3e50"}}))
        fig_g.update_layout(height=250, margin=dict(l=20,r=20,t=30,b=20)); st.plotly_chart(fig_g, use_container_width=True)
        
        total_binder = c + s + f
        wb_ratio = w / total_binder if total_binder > 0 else 0
        if wb_ratio > 0.5: st.warning(f"⚠️ w/b = {wb_ratio:.3f} (>0.5)")
        else: st.success(f"✅ w/b = {wb_ratio:.3f}")

    if enable_val and act_ksc > 0:
        err = abs(act_ksc - final_ksc)/act_ksc * 100
        st.markdown(f"""<div class="validation-box"><h3>🧪 ผลการเทียบ Lab</h3>ค่าพยากรณ์: <b>{final_ksc:.2f}</b> vs ค่าจริง: <b>{act_ksc:.2f}</b> (Error: {err:.2f}%)</div>""", unsafe_allow_html=True)

    st.markdown("---")
    r1, r2 = st.columns(2)
    with r1: st.plotly_chart(plot_stress_strain(final_ksc), use_container_width=True)
    with r2: st.bar_chart(pd.DataFrame({"วัสดุ":["ปูน","สแลก","เถ้า","น้ำ","สาร","หิน","ทราย"], "ปริมาณ":[c,s,f,w,sp,ca,fa]}).set_index("วัสดุ"))
    
    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1: 
        tv = st.selectbox("Sensitivity:", ["Cement", "Water", "Age"])
        mv = {"Cement":"Cement", "Water":"Water", "Age":"Age"}
        st.plotly_chart(plot_sens(model, input_data, mv[tv], tv), use_container_width=True)
    with s2:
        st.metric("ราคาประเมิน (บาท/ลบ.ม.)", f"{cost:,.2f}")
        cost_df = pd.DataFrame({'Mat':['Cement','Slag','FlyAsh','Water','SP','Rock','Sand'], 'Cost':[c*2.5, s*1.5, f*1.0, w*0.015, sp*40, ca*0.35, fa*0.30]})
        fig_pie = go.Figure(data=[go.Pie(labels=cost_df['Mat'], values=cost_df['Cost'], hole=.4)])
        fig_pie.update_layout(height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("👈 กรุณาเลือกโหมดและกดปุ่มคำนวณ")
