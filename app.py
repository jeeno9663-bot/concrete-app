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
st.set_page_config(
    page_title="ระบบทำนายกำลังอัดคอนกรีต/ดินซีเมนต์",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------
# 2. ระบบจำค่า (Session State)
# -------------------------------------------
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False

# โหลดโมเดล
try:
    model = joblib.load('concrete_model.pkl')
    model_status = "ระบบพร้อมใช้งาน (System Ready)"
except:
    st.error("ข้อผิดพลาด: ไม่พบไฟล์โมเดล (concrete_model.pkl) กรุณาตรวจสอบ")
    model_status = "เกิดข้อผิดพลาด (System Error)"

# -------------------------------------------
# 3. CSS Style
# -------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif; }
    div.stButton > button {
        background-color: #2c3e50; color: white; border-radius: 5px; border: none;
        padding: 10px 20px; font-size: 16px; width: 100%; transition: all 0.3s;
    }
    div.stButton > button:hover { background-color: #34495e; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------
# ฟังก์ชันสร้าง PDF
# -------------------------------------------
class PDF(FPDF):
    def header(self):
        try: self.image('image_19.png', 10, 8, 25)
        except: pass
        try:
            self.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
            self.set_font('THSarabunNew', '', 20)
        except:
            self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'รายงานผลการออกแบบ (Design Report)', 0, 0, 'C')
        self.ln(20)
    def footer(self):
        self.set_y(-15)
        try: self.set_font('THSarabunNew', '', 14)
        except: self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'หน้า {self.page_no()}', 0, 0, 'C')

def create_pdf(inputs, results, cost_total, sample_type):
    pdf = PDF()
    pdf.add_page()
    try:
        pdf.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
        pdf.add_font('THSarabunNew', 'B', 'THSarabunNew.ttf', uni=True)
        font = 'THSarabunNew'
    except: font = 'Arial'
    
    pdf.set_font(font, 'B', 16)
    pdf.cell(200, 10, "1. ข้อมูลโครงการ (Project Info)", ln=True)
    pdf.set_font(font, '', 16)
    pdf.cell(200, 10, f"วันที่: {time.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(200, 10, f"ประเภทตัวอย่าง: {sample_type}", ln=True)
    pdf.ln(5)
    
    pdf.set_font(font, 'B', 16)
    pdf.cell(200, 10, "2. ส่วนผสม (Mix Proportion)", ln=True)
    pdf.set_font(font, '', 16)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(100, 10, "รายการ", 1, 0, 'C', 1)
    pdf.cell(50, 10, "ปริมาณ (kg)", 1, 1, 'C', 1)
    
    mix = {"Cement": inputs['Cement'], "Slag": inputs['Blast Furnace Slag'], "Fly Ash": inputs['Fly Ash'], 
           "Water": inputs['Water'], "Superplasticizer": inputs['Superplasticizer'], 
           "Coarse Agg": inputs['Coarse Aggregate'], "Fine Agg": inputs['Fine Aggregate']}
    for k,v in mix.items():
        pdf.cell(100, 10, k, 1)
        pdf.cell(50, 10, f"{v:.2f}", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.set_font(font, 'B', 16)
    pdf.cell(200, 10, f"ผลการทำนาย: {results['ksc']:.2f} ksc", ln=True)
    pdf.cell(200, 10, f"ราคาประเมิน: {cost_total:,.2f} บาท", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# -------------------------------------------
# [NEW] ฟังก์ชันสร้างโมเดล 3 มิติ (เลือกทรงได้)
# -------------------------------------------
def plot_3d_sample(ksc, shape_type):
    fig = go.Figure()
    
    # คำนวณความเข้มสีตามค่า ksc (ยิ่งเยอะ ยิ่งเข้ม)
    intensity = min(1.0, ksc / 800)
    
    # 1. กำหนดสี (Texture)
    if "ดิน" in shape_type:
        # โทนน้ำตาล (Soil)
        r = int(180 - (intensity * 60))
        g = int(140 - (intensity * 60))
        b = int(100 - (intensity * 60))
        base_color = f'rgb({r},{g},{b})'
        cap_color = '#5D4037'
    else:
        # โทนเทา (Concrete)
        gray_val = int(200 - (intensity * 100))
        base_color = f'rgb({gray_val},{gray_val},{gray_val})'
        cap_color = f'rgb({gray_val-20},{gray_val-20},{gray_val-20})'

    # 2. วาดรูปทรง
    if "ทรงกระบอก" in shape_type: # Cylinder
        r_cyl = 1
        h_cyl = 2
        theta = np.linspace(0, 2*np.pi, 50)
        z = np.linspace(0, h_cyl, 20)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = r_cyl * np.cos(theta_grid)
        y = r_cyl * np.sin(theta_grid)
        
        # ผิวข้าง
        fig.add_trace(go.Surface(x=x, y=y, z=z_grid, colorscale=[[0, base_color], [1, base_color]], showscale=False, opacity=1.0))
        
        # ฝาปิด
        r_cap = np.linspace(0, r_cyl, 10)
        th_cap = np.linspace(0, 2*np.pi, 30)
        r_grid, th_grid = np.meshgrid(r_cap, th_cap)
        x_cap = r_grid * np.cos(th_grid)
        y_cap = r_grid * np.sin(th_grid)
        z_top = np.full_like(x_cap, h_cyl)
        z_bot = np.full_like(x_cap, 0)
        
        fig.add_trace(go.Surface(x=x_cap, y=y_cap, z=z_top, colorscale=[[0, cap_color], [1, cap_color]], showscale=False))
        fig.add_trace(go.Surface(x=x_cap, y=y_cap, z=z_bot, colorscale=[[0, cap_color], [1, cap_color]], showscale=False))
        
    elif "ลูกบาศก์" in shape_type: # Cube
        # ใช้ Mesh3d วาดลูกบาศก์
        fig.add_trace(go.Mesh3d(
            # พิกัดจุดมุมทั้ง 8 ของลูกบาศก์
            x=[0, 1, 1, 0, 0, 1, 1, 0],
            y=[0, 0, 1, 1, 0, 0, 1, 1],
            z=[0, 0, 0, 0, 1, 1, 1, 1],
            # กำหนดสี
            color=base_color,
            opacity=1.0,
            # การเชื่อมจุด (Triangulation) - i, j, k
            i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            flatshading = True
        ))

    fig.update_layout(
        title=f"ตัวอย่าง: {shape_type}",
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        height=350, margin=dict(l=0, r=0, b=0, t=30)
    )
    return fig

# -------------------------------------------
# ฟังก์ชันกราฟอื่นๆ
# -------------------------------------------
def plot_stress_strain(fc_prime):
    eps_0, eps_u = 0.002, 0.0035
    strain = np.linspace(0, eps_u, 100)
    stress = []
    for e in strain:
        if e <= eps_0: f = fc_prime*(2*(e/eps_0)-(e/eps_0)**2)
        else: f = fc_prime - ((fc_prime-0.85*fc_prime)/(eps_u-eps_0))*(e-eps_0)
        stress.append(max(0, f))
    stress = np.array(stress)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strain, y=stress, mode='lines', line=dict(color='#2c3e50', width=3), name='Stress-Strain'))
    idx_el = np.abs(stress[:50] - fc_prime*0.45).argmin()
    idx_pk = np.argmax(stress)
    fig.add_trace(go.Scatter(x=[strain[idx_el]], y=[stress[idx_el]], mode='markers', marker=dict(color='orange', size=8), name='Elastic'))
    fig.add_trace(go.Scatter(x=[strain[idx_pk]], y=[stress[idx_pk]], mode='markers', marker=dict(color='red', size=10), name='Ultimate'))
    fig.add_trace(go.Scatter(x=[strain[-1]], y=[stress[-1]], mode='markers', marker=dict(color='black', size=8, symbol='x'), name='Failure'))
    
    fig.update_layout(title="พฤติกรรมรับแรง (Stress-Strain)", height=350, template='plotly_white')
    return fig

def plot_sensitivity(model, base_df, col_name, label):
    try:
        val = base_df[col_name].values[0]
        x = np.linspace(0 if val==0 else val*0.5, val*1.5 if val!=0 else 100, 20)
        temp = pd.concat([base_df]*len(x), ignore_index=True)
        temp[col_name] = x
        y = model.predict(temp) * 10.197
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Trend'))
        fig.add_trace(go.Scatter(x=[val], y=[model.predict(base_df)[0]*10.197], mode='markers', marker=dict(color='red', size=10), name='Current'))
        fig.update_layout(title=f"แนวโน้มเมื่อปรับ {label}", height=300, template='plotly_white')
        return fig
    except: return go.Figure()

# -------------------------------------------
# 4. Sidebar Input
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดค่าพารามิเตอร์")
    try: st.image(Image.open("image_19.png"), width=150)
    except: pass
    st.markdown("---")
    
    cement = st.number_input("ปูนซีเมนต์", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย", 0.0, 1000.0, 0.0)
    water = st.number_input("น้ำ", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ", 0.0, 100.0, 0.0)
    coarse = st.number_input("หิน", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย", 0.0, 2000.0, 800.0)
    age = st.slider("อายุบ่ม (วัน)", 1, 365, 28)
    
    if st.button("🚀 คำนวณกำลังอัด", type="primary"):
        st.session_state['calculated'] = True

# -------------------------------------------
# 5. Main Content
# -------------------------------------------
st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

if st.session_state['calculated']:
    
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    cost_total = (cement*2.5 + slag*1.5 + flyash*1.0 + water*0.015 + superplastic*40 + coarse*0.35 + fine*0.30)
    
    # --- Layout Grid ---
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("ผลการทำนาย")
        # Gauge
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number", value = pred_ksc,
            title = {'text': "กำลังอัด (ksc)", 'font': {'size': 24}},
            gauge = {'axis': {'range': [None, 1000]}, 'bar': {'color': "#2c3e50"},
                     'steps': [{'range': [0, 180], 'color': '#ff4b4b'}, {'range': [280, 450], 'color': '#21c354'}],
                     'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pred_ksc}}
        ))
        fig_g.update_layout(height=250, margin=dict(l=20,r=20,t=30,b=20))
        st.plotly_chart(fig_g, use_container_width=True)
        
        # Standard Check
        st.markdown("##### ✅ ตรวจสอบมาตรฐาน (ACI)")
        wb = water/(cement+slag+flyash) if (cement+slag+flyash)>0 else 0
        if wb > 0.5: st.warning(f"⚠️ w/b = {wb:.2f} (>0.5) ไม่เหมาะกับงานภายนอก")
        else: st.success(f"✅ w/b = {wb:.2f} ผ่านเกณฑ์")

    with c2:
        # [NEW] Selector for 3D Shape
        shape_opt = st.radio("เลือกรูปแบบตัวอย่าง (Sample Type):", 
                             ["ก้อนดินซีเมนต์ (ทรงกระบอก)", "คอนกรีต (ลูกบาศก์)", "คอนกรีต (ทรงกระบอก)"], 
                             horizontal=True)
        
        st.plotly_chart(plot_3d_sample(pred_ksc, shape_opt), use_container_width=True)
        
        # Download Buttons
        b_ex = io.BytesIO()
        with pd.ExcelWriter(b_ex, engine='xlsxwriter') as w:
            pd.DataFrame({'Result': [pred_ksc]}).to_excel(w)
        
        pdf_dat = create_pdf(input_data.iloc[0], {'ksc': pred_ksc}, cost_total, shape_opt)
        
        col_d1, col_d2 = st.columns(2)
        col_d1.download_button("📥 Excel", b_ex, "res.xlsx")
        col_d2.download_button("📄 PDF", pdf_dat, "rep.pdf", "application/pdf")

    st.markdown("---")
    
    # Row 2: Charts
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.plotly_chart(plot_stress_strain(pred_ksc), use_container_width=True)
    with r2_c2:
        df_mix = pd.DataFrame({"Item": ["Cement", "Slag", "FlyAsh", "Water", "SP", "Coarse", "Fine"], 
                               "Qty": [cement, slag, flyash, water, superplastic, coarse, fine]})
        st.bar_chart(df_mix.set_index("Item"))

    # Row 3: Calculation & Sensitivity
    st.markdown("---")
    with st.expander("📝 รายการคำนวณ (Calculation Sheet)"):
        st.latex(rf"Binder = {cement+slag+flyash} \; kg/m^3")
        st.latex(rf"w/b = {wb:.3f}")
        st.latex(rf"Strength = {pred_ksc:.2f} \; ksc")

    st.markdown("### 🔍 วิเคราะห์แนวโน้ม & ราคา")
    sens_c1, sens_c2 = st.columns(2)
    
    with sens_c1:
        t_var = st.selectbox("ปัจจัย:", ["ปูนซีเมนต์", "น้ำ", "อายุบ่ม"])
        m_var = {"ปูนซีเมนต์":"Cement", "น้ำ":"Water", "อายุบ่ม":"Age"}
        st.plotly_chart(plot_sensitivity(model, input_data, m_var[t_var], t_var), use_container_width=True)
        
    with sens_c2:
        st.metric("ราคาประเมิน (บาท/ลบ.ม.)", f"{cost_total:,.2f}")
        # Pie Chart
        cost_df = pd.DataFrame({'Mat':['Cement','Slag','FlyAsh','Water','SP','Rock','Sand'],
                                'Cost':[cement*2.5, slag*1.5, flyash*1.0, water*0.015, superplastic*40, coarse*0.35, fine*0.30]})
        fig_pie = go.Figure(data=[go.Pie(labels=cost_df['Mat'], values=cost_df['Cost'], hole=.4)])
        fig_pie.update_layout(height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("👈 กรุณากดปุ่มคำนวณเพื่อเริ่มใช้งาน")
