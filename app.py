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
    page_title="ระบบทำนายกำลังอัดคอนกรีต",
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
# ฟังก์ชันสร้าง PDF Report (ภาษาไทย)
# -------------------------------------------
class PDF(FPDF):
    def header(self):
        try:
            self.image('image_19.png', 10, 8, 25)
        except: pass
        
        try:
            self.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
            self.set_font('THSarabunNew', '', 20)
        except:
            self.set_font('Arial', 'B', 15)
            
        self.cell(80)
        self.cell(30, 10, 'รายงานการออกแบบส่วนผสมคอนกรีต (Mix Design Report)', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('THSarabunNew', '', 14)
        except:
            self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'หน้า {self.page_no()}', 0, 0, 'C')

def create_pdf(inputs, results, cost_total):
    pdf = PDF()
    pdf.add_page()
    
    try:
        pdf.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)
        pdf.add_font('THSarabunNew', 'B', 'THSarabunNew.ttf', uni=True)
        font_name = 'THSarabunNew'
    except:
        font_name = 'Arial'
    
    # 1. ข้อมูลโครงการ
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(200, 10, txt="1. ข้อมูลทั่วไป (Project Information)", ln=True)
    pdf.set_font(font_name, '', 16)
    pdf.cell(200, 10, txt=f"วันที่ทำรายการ: {time.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.cell(200, 10, txt="ออกแบบโดย: ระบบปัญญาประดิษฐ์ (RMUTL Concrete AI)", ln=True)
    pdf.ln(5)
    
    # 2. ส่วนผสม
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(200, 10, txt="2. สัดส่วนผสมคอนกรีต (Mix Proportions - kg/m3)", ln=True)
    pdf.set_font(font_name, '', 16)
    
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(100, 10, "รายการวัสดุ (Material)", 1, 0, 'C', 1)
    pdf.cell(50, 10, "ปริมาณ (กก.)", 1, 1, 'C', 1)
    
    mix_items = {
        "ปูนซีเมนต์ (Cement)": inputs['Cement'], "สแลก (Slag)": inputs['Blast Furnace Slag'], 
        "เถ้าลอย (Fly Ash)": inputs['Fly Ash'], "น้ำ (Water)": inputs['Water'], 
        "สารลดน้ำ (Superplasticizer)": inputs['Superplasticizer'], 
        "หิน (Coarse Aggregate)": inputs['Coarse Aggregate'], "ทราย (Fine Aggregate)": inputs['Fine Aggregate']
    }
    
    for mat, qty in mix_items.items():
        pdf.cell(100, 10, mat, 1)
        pdf.cell(50, 10, f"{qty:.2f}", 1, 1, 'R')
        
    pdf.cell(100, 10, "ราคาประเมินรวม (Total Cost)", 1)
    pdf.cell(50, 10, f"{cost_total:,.2f} บาท", 1, 1, 'R')
    pdf.ln(5)

    # 3. ผลการคำนวณ
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(200, 10, txt="3. ผลการวิเคราะห์กำลังอัด (Prediction Results)", ln=True)
    pdf.set_font(font_name, '', 16)
    pdf.cell(200, 10, txt=f"อายุบ่มคอนกรีต: {int(inputs['Age'])} วัน", ln=True)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(200, 10, txt=f"กำลังอัดที่คาดการณ์: {results['ksc']:.2f} ksc ({results['mpa']:.2f} MPa)", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # 4. ตรวจสอบมาตรฐาน
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(200, 10, txt="4. ตรวจสอบตามมาตรฐาน (Standard Check - ACI)", ln=True)
    pdf.set_font(font_name, '', 14)
    
    total_binder = inputs['Cement'] + inputs['Blast Furnace Slag'] + inputs['Fly Ash']
    wb_ratio = inputs['Water'] / total_binder if total_binder > 0 else 0
    
    if wb_ratio > 0.50:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, txt=f"[คำเตือน] w/b ratio = {wb_ratio:.3f} (> 0.50) : ไม่เหมาะสำหรับงานโครงสร้างภายนอกอาคาร", ln=True)
    else:
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 10, txt=f"[ผ่านเกณฑ์] w/b ratio = {wb_ratio:.3f} (<= 0.50) : เหมาะสมสำหรับงานทั่วไป", ln=True)
            
    if inputs['Cement'] < 300:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, txt=f"[คำเตือน] ปริมาณปูน = {inputs['Cement']} กก./ลบ.ม. (< 300) : อาจมีปัญหาความทนทาน", ln=True)
    else:
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 10, txt=f"[ผ่านเกณฑ์] ปริมาณปูน = {inputs['Cement']} กก./ลบ.ม. (>= 300) : ปริมาณเหมาะสม", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)

    # 5. ลายเซ็น
    pdf.cell(0, 10, "__________________________", 0, 1, 'R')
    pdf.cell(0, 10, "วิศวกรผู้ออกแบบ (Engineer)        ", 0, 1, 'R')
    pdf.cell(0, 10, f"วันที่: {time.strftime('%d/%m/%Y')}", 0, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

# -------------------------------------------
# ฟังก์ชันสร้างกราฟ Stress-Strain
# -------------------------------------------
def plot_stress_strain(fc_prime):
    epsilon_0 = 0.002 
    epsilon_ult = 0.0035 
    strain = np.linspace(0, epsilon_ult, 100)
    stress = []
    
    for eps in strain:
        if eps <= epsilon_0:
            f = fc_prime * (2*(eps/epsilon_0) - (eps/epsilon_0)**2)
        else:
            slope = (fc_prime * 0.85 - fc_prime) / (0.0038 - epsilon_0)
            f = fc_prime + slope * (eps - epsilon_0)
            if f < 0: f = 0
        stress.append(f)
    stress = np.array(stress)
    
    elastic_limit = fc_prime * 0.45
    idx_elastic = np.abs(stress[:50] - elastic_limit).argmin()
    idx_peak = np.argmax(stress)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strain, y=stress, mode='lines', name='Stress-Strain', line=dict(color='#2c3e50', width=3)))
    fig.add_trace(go.Scatter(x=[strain[idx_elastic]], y=[stress[idx_elastic]], mode='markers+text', name='Elastic Limit', marker=dict(color='orange', size=10), text=['Elastic Limit'], textposition="bottom right"))
    fig.add_trace(go.Scatter(x=[strain[idx_peak]], y=[stress[idx_peak]], mode='markers+text', name='Ultimate Strength', marker=dict(color='red', size=12), text=[f'Max: {fc_prime:.2f} ksc'], textposition="top center"))
    fig.add_trace(go.Scatter(x=[strain[-1]], y=[stress[-1]], mode='markers', name='Failure Point', marker=dict(color='black', size=10, symbol='x')))

    fig.update_layout(title="กราฟจำลองพฤติกรรม Stress-Strain (Simulation)", xaxis_title="Strain", yaxis_title="Stress (ksc)", template="plotly_white", height=400, margin=dict(t=50, b=20, l=20, r=20), hovermode="x unified")
    return fig

# -------------------------------------------
# ฟังก์ชันสร้างกราฟ Sensitivity
# -------------------------------------------
def plot_sensitivity(model, current_inputs, target_col, col_name_th):
    try:
        current_val = current_inputs[target_col].values[0]
        x_values = np.linspace(0, 100, 20) if current_val == 0 else np.linspace(max(0, current_val * 0.5), current_val * 1.5, 20)
        temp_df = pd.concat([current_inputs] * len(x_values), ignore_index=True)
        temp_df[target_col] = x_values
        y_preds = model.predict(temp_df) * 10.197
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_values, y=y_preds, mode='lines', name='Trend', line=dict(color='#3498db', width=3)))
        current_pred = model.predict(current_inputs)[0] * 10.197
        fig.add_trace(go.Scatter(x=[current_val], y=[current_pred], mode='markers', name='Current Mix', marker=dict(color='red', size=12)))
        fig.update_layout(title=f"แนวโน้มเมื่อปรับ '{col_name_th}'", xaxis_title=f"ปริมาณ {col_name_th}", yaxis_title="กำลังอัด (ksc)", template="plotly_white", height=350)
        return fig
    except: return go.Figure()

# -------------------------------------------
# 4. Sidebar Input
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดค่าพารามิเตอร์")
    
    try:
        logo_image = Image.open("image_19.png")
        st.image(logo_image, width=150)
    except: pass

    st.markdown("---")
    cement = st.number_input("ปูนซีเมนต์ (Cement)", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก (Slag)", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย (Fly Ash)", 0.0, 1000.0, 0.0)
    water = st.number_input("น้ำ (Water)", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ (Superplasticizer)", 0.0, 100.0, 0.0)
    coarse = st.number_input("หิน (Coarse Aggregate)", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย (Fine Aggregate)", 0.0, 2000.0, 800.0)
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
    
    # เตรียมข้อมูล
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # ทำนายผล
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    col_result, col_chart = st.columns([1.2, 1])
    
    # === Gauge Chart & Standard Check ===
    with col_result:
        st.subheader("ผลการทำนาย")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = pred_ksc,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "กำลังอัด (ksc)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 1000]}, 'bar': {'color': "#2c3e50"},
                'steps': [{'range': [0, 180], 'color': '#ff4b4b'}, {'range': [180, 280], 'color': '#ffa421'}, {'range': [280, 450], 'color': '#21c354'}, {'range': [450, 1000], 'color': '#00c0f2'}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pred_ksc}
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"เทียบเท่า: **{pred_mpa:.2f} MPa**")

        st.markdown("### ✅ ตรวจสอบตามมาตรฐาน (ACI 318)")
        total_binder = cement + slag + flyash
        wb_ratio = water / total_binder if total_binder > 0 else 0
        
        if wb_ratio > 0.50:
            st.warning(f"⚠️ **w/b ratio = {wb_ratio:.3f}** (เกิน 0.50): ไม่แนะนำสำหรับโครงสร้างภายนอกอาคาร")
        else:
            st.success(f"✅ **w/b ratio = {wb_ratio:.3f}** (ผ่าน): เหมาะสมสำหรับงานทั่วไป")
            
        if cement < 300:
            st.warning(f"⚠️ **ปูนซีเมนต์ = {cement} kg/m³** (น้อยกว่า 300): อาจมีปัญหาความทนทาน")
        else:
            st.success(f"✅ **ปูนซีเมนต์ = {cement} kg/m³** (ผ่าน): ปริมาณเหมาะสม")

    # === Mix & Download ===
    with col_chart:
        st.subheader("สัดส่วนผสม")
        df_summary = pd.DataFrame({"รายการ": ["ซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"], "ปริมาณ": [cement, slag, flyash, water, superplastic, coarse, fine]})
        st.bar_chart(df_summary.set_index("รายการ"))
        
        # คำนวณราคาสำหรับ PDF และกราฟ
        with st.expander("💰 กำหนดราคาวัสดุ (สำหรับการประเมิน)", expanded=False):
             c1, c2, c3, c4 = st.columns(4)
             p_cement = c1.number_input("ราคาปูน", value=2.5)
             p_slag = c2.number_input("ราคาสแลก", value=1.5)
             p_flyash = c3.number_input("ราคาเถ้าลอย", value=1.0)
             p_water = c4.number_input("ราคาน้ำ", value=0.015)
             c5, c6, c7 = st.columns(3)
             p_super = c5.number_input("สารลดน้ำ", value=40.0)
             p_coarse = c6.number_input("ราคาหิน", value=0.35)
             p_fine = c7.number_input("ราคาทราย", value=0.30)
             
        total_cost = (cement*p_cement + slag*p_slag + flyash*p_flyash + water*p_water + superplastic*p_super + coarse*p_coarse + fine*p_fine)
        
        # Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pd.DataFrame({'Param': ['Result ksc'], 'Value': [pred_ksc]}).to_excel(writer)
        
        c_dl1, c_dl2 = st.columns(2)
        c_dl1.download_button("📥 โหลด Excel", data=buffer, file_name="result.xlsx")
        
        # PDF Button
        pdf_bytes = create_pdf(input_data.iloc[0], {'ksc': pred_ksc, 'mpa': pred_mpa}, total_cost)
        c_dl2.download_button("📄 โหลด PDF (ไทย)", data=pdf_bytes, file_name="Report_Thai.pdf", mime="application/pdf")

    # === Stress-Strain ===
    st.markdown("---")
    st.subheader("📈 กราฟจำลองพฤติกรรม Stress-Strain")
    st.plotly_chart(plot_stress_strain(pred_ksc), use_container_width=True)
    
    # === Calculation Sheet ===
    st.markdown("---")
    with st.expander("📝 รายการคำนวณประกอบ (Calculation Sheet)", expanded=False):
        st.latex(rf"Binder = {cement} + {slag} + {flyash} = {total_binder} \; \text{{kg}}/m^3")
        st.latex(rf"w/b = \frac{{{water}}}{{{total_binder}}} = \mathbf{{{wb_ratio:.3f}}}")
        st.latex(rf"\text{{Strength}} = {pred_mpa:.2f} \times 10.197 = \mathbf{{{pred_ksc:.2f} \; \text{{ksc}}}}")

    # === Sensitivity Analysis ===
    st.markdown("---")
    st.header("🔍 วิเคราะห์แนวโน้มผลกระทบ (Sensitivity Analysis)")
    target_var = st.selectbox("เลือกปัจจัยที่ต้องการวิเคราะห์:", ["ปูนซีเมนต์ (Cement)", "น้ำ (Water)", "เถ้าลอย (Fly Ash)", "อายุบ่ม (Age)"])
    map_dict = {"ปูนซีเมนต์ (Cement)": "Cement", "น้ำ (Water)": "Water", "เถ้าลอย (Fly Ash)": "Fly Ash", "อายุบ่ม (Age)": "Age"}
    fig_sens = plot_sensitivity(model, input_data, map_dict[target_var], target_var)
    st.plotly_chart(fig_sens, use_container_width=True)

    # === Cost Estimation Section (Fixed: Added Chart Back) ===
    st.markdown("---")
    st.header("💰 ประเมินราคาคอนกรีต (Cost Estimation)")
    
    st.metric(label="ราคาประเมินต่อลูกบาศก์เมตร", value=f"{total_cost:,.2f} บาท")
    
    # --- ส่วนที่หายไป กู้คืนกลับมาแล้วครับ ---
    cost_data = pd.DataFrame({
        'Material': ['Cement', 'Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Agg', 'Fine Agg'],
        'Cost': [cement*p_cement, slag*p_slag, flyash*p_flyash, water*p_water, superplastic*p_super, coarse*p_coarse, fine*p_fine]
    })
    cost_data = cost_data[cost_data['Cost'] > 0]
    
    if not cost_data.empty:
        fig_cost = go.Figure(data=[go.Pie(labels=cost_data['Material'], values=cost_data['Cost'], hole=.4)])
        fig_cost.update_layout(title="สัดส่วนต้นทุนแยกตามวัสดุ", height=350)
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลต้นทุน (อาจเป็นเพราะปริมาณวัสดุเป็น 0 หรือราคาเป็น 0)")

else:
    st.info("👈 กรุณากรอกข้อมูลด้านซ้าย แล้วกดปุ่ม '🚀 คำนวณกำลังอัด' เพื่อเริ่มใช้งาน")
