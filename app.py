import streamlit as st
import pandas as pd
import joblib
import time
import numpy as np
import plotly.graph_objects as go
import io

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
# 2. ระบบจำค่า (Session State) - กันหน้าเด้ง
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
# ฟังก์ชันสร้างกราฟ Stress-Strain (ฉบับละเอียด - คืนค่า Elastic/Failure)
# -------------------------------------------
def plot_stress_strain(fc_prime):
    # สมการ Hognestad's Parabola
    epsilon_0 = 0.002 
    epsilon_ult = 0.0035 
    strain = np.linspace(0, epsilon_ult, 100)
    stress = []
    
    for eps in strain:
        if eps <= epsilon_0:
            # ช่วงพาราโบลา
            f = fc_prime * (2*(eps/epsilon_0) - (eps/epsilon_0)**2)
        else:
            # ช่วง Softening
            slope = (fc_prime * 0.85 - fc_prime) / (0.0038 - epsilon_0)
            f = fc_prime + slope * (eps - epsilon_0)
            if f < 0: f = 0
        stress.append(f)
    
    stress = np.array(stress)
    
    # --- คืนค่าจุดสำคัญ ---
    # 1. Elastic Limit (45% ของกำลังสูงสุด)
    elastic_limit = fc_prime * 0.45
    idx_elastic = np.abs(stress[:50] - elastic_limit).argmin()
    
    # 2. Ultimate Strength (จุดสูงสุด)
    idx_peak = np.argmax(stress)
    
    # สร้างกราฟ
    fig = go.Figure()
    
    # เส้นกราฟหลัก
    fig.add_trace(go.Scatter(x=strain, y=stress, mode='lines', name='Stress-Strain', line=dict(color='#2c3e50', width=3)))
    
    # จุด Elastic Limit (สีส้ม) - กลับมาแล้ว!
    fig.add_trace(go.Scatter(
        x=[strain[idx_elastic]], y=[stress[idx_elastic]],
        mode='markers+text', name='Elastic Limit', 
        marker=dict(color='orange', size=10),
        text=['Elastic Limit'], textposition="bottom right"
    ))
    
    # จุด Ultimate Strength (สีแดง)
    fig.add_trace(go.Scatter(
        x=[strain[idx_peak]], y=[stress[idx_peak]],
        mode='markers+text', name='Ultimate Strength', 
        marker=dict(color='red', size=12),
        text=[f'Max: {fc_prime:.2f} ksc'], textposition="top center"
    ))
    
    # จุด Failure (สีดำ) - กลับมาแล้ว!
    fig.add_trace(go.Scatter(
        x=[strain[-1]], y=[stress[-1]],
        mode='markers', name='Failure Point', 
        marker=dict(color='black', size=10, symbol='x')
    ))

    fig.update_layout(
        title="กราฟจำลองพฤติกรรม Stress-Strain (Simulation)", 
        xaxis_title="Strain", yaxis_title="Stress (ksc)", 
        template="plotly_white", height=400, margin=dict(t=50, b=20, l=20, r=20),
        hovermode="x unified"
    )
    return fig

# -------------------------------------------
# ฟังก์ชันสร้างกราฟ Sensitivity (เสถียร ไม่เด้ง)
# -------------------------------------------
def plot_sensitivity(model, current_inputs, target_col, col_name_th):
    try:
        current_val = current_inputs[target_col].values[0]
        if current_val == 0:
            x_values = np.linspace(0, 100, 20)
        else:
            x_values = np.linspace(max(0, current_val * 0.5), current_val * 1.5, 20)
        
        # Vectorized Prediction (เร็วและไม่หลุด)
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
    st.markdown("---")
    cement = st.number_input("ปูนซีเมนต์", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย", 0.0, 1000.0, 0.0)
    water = st.number_input("น้ำ", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ", 0.0, 100.0, 0.0)
    coarse = st.number_input("หิน", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย", 0.0, 2000.0, 800.0)
    age = st.slider("อายุบ่ม (วัน)", 1, 365, 28)
    
    # ปุ่มคำนวณ (ใช้ Session State)
    if st.button("🚀 คำนวณกำลังอัด", type="primary"):
        st.session_state['calculated'] = True

# -------------------------------------------
# 5. Main Content
# -------------------------------------------
st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

# ตรวจสอบว่าเคยกดปุ่มคำนวณหรือยัง?
if st.session_state['calculated']:
    
    # เตรียมข้อมูล
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # ทำนายผล
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    col_result, col_chart = st.columns([1.2, 1])
    
    # === Gauge Chart ===
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

    # === Mix & Excel ===
    with col_chart:
        st.subheader("สัดส่วนผสม")
        df_summary = pd.DataFrame({"รายการ": ["ซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"], "ปริมาณ": [cement, slag, flyash, water, superplastic, coarse, fine]})
        st.bar_chart(df_summary.set_index("รายการ"))
        
        # Excel Export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Sheet 1: Result
            pd.DataFrame({
                'Parameter': ['Cement', 'Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Agg', 'Fine Agg', 'Age', 'Predicted Strength (ksc)', 'Predicted Strength (MPa)'],
                'Value': [cement, slag, flyash, water, superplastic, coarse, fine, age, pred_ksc, pred_mpa],
                'Unit': ['kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'Days', 'ksc', 'MPa']
            }).to_excel(writer, index=False, sheet_name='Result')
        st.download_button("📥 ดาวน์โหลด Excel", data=buffer, file_name="concrete_result.xlsx")

    # === Stress-Strain (Full Version) ===
    st.markdown("---")
    st.subheader("📈 กราฟจำลองพฤติกรรม Stress-Strain")
    st.plotly_chart(plot_stress_strain(pred_ksc), use_container_width=True)
    st.caption("*กราฟแสดงจุด Elastic Limit (45%), Ultimate Strength, และ Failure Point ตามทฤษฎี Hognestad")
    
    # === Calculation Sheet ===
    st.markdown("---")
    with st.expander("📝 รายการคำนวณประกอบ (Calculation Sheet)", expanded=False):
        total_binder = cement + slag + flyash
        wb_ratio = water / total_binder if total_binder > 0 else 0
        st.latex(rf"Binder = {cement} + {slag} + {flyash} = {total_binder} \; \text{{kg}}/m^3")
        st.latex(rf"w/b = \frac{{{water}}}{{{total_binder}}} = \mathbf{{{wb_ratio:.3f}}}")
        st.latex(rf"\text{{Strength}} = {pred_mpa:.2f} \times 10.197 = \mathbf{{{pred_ksc:.2f} \; \text{{ksc}}}}")

    # === Sensitivity Analysis ===
    st.markdown("---")
    st.header("🔍 วิเคราะห์แนวโน้มผลกระทบ (Sensitivity Analysis)")
    
    target_var = st.selectbox("เลือกปัจจัยที่ต้องการวิเคราะห์:", 
                 ["ปูนซีเมนต์ (Cement)", "น้ำ (Water)", "เถ้าลอย (Fly Ash)", "อายุบ่ม (Age)"])
    
    map_dict = {"ปูนซีเมนต์ (Cement)": "Cement", "น้ำ (Water)": "Water", "เถ้าลอย (Fly Ash)": "Fly Ash", "อายุบ่ม (Age)": "Age"}
    fig_sens = plot_sensitivity(model, input_data, map_dict[target_var], target_var)
    st.plotly_chart(fig_sens, use_container_width=True)

else:
    st.info("👈 กรุณากรอกข้อมูลด้านซ้าย แล้วกดปุ่ม '🚀 คำนวณกำลังอัด' เพื่อเริ่มใช้งาน")


