import streamlit as st
import pandas as pd
import joblib
import time
import numpy as np # ต้องใช้สำหรับคำนวณเส้นกราฟ
import plotly.graph_objects as go

# -------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
# -------------------------------------------
st.set_page_config(
    page_title="ระบบทำนายกำลังอัดคอนกรีต",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# โหลดโมเดล
try:
    model = joblib.load('concrete_model.pkl')
    model_status = "ระบบพร้อมใช้งาน (System Ready)"
except:
    st.error("ข้อผิดพลาด: ไม่พบไฟล์โมเดล (concrete_model.pkl) กรุณาตรวจสอบ")
    model_status = "เกิดข้อผิดพลาด (System Error)"

# -------------------------------------------
# 2. ปรับแต่ง CSS
# -------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Sarabun', sans-serif;
    }
    
    div.stButton > button {
        background-color: #2c3e50;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #34495e;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------
# ฟังก์ชันสร้างกราฟ Stress-Strain (Simulated)
# -------------------------------------------
def plot_stress_strain(fc_prime):
    # สมมติพฤติกรรมคอนกรีตตาม Hognestad's Parabola
    epsilon_0 = 0.002 # ความเครียดที่จุดสูงสุด (ค่ามาตรฐานคอนกรีต)
    epsilon_ult = 0.0035 # ความเครียดที่จุดวิบัติ
    
    # สร้างข้อมูลแกน X (Strain)
    strain = np.linspace(0, epsilon_ult, 100)
    
    # คำนวณแกน Y (Stress)
    stress = []
    for eps in strain:
        if eps <= epsilon_0:
            # ช่วงขาขึ้น (Parabola)
            f = fc_prime * (2*(eps/epsilon_0) - (eps/epsilon_0)**2)
        else:
            # ช่วงขาลง (Linear softening) - สมมติให้ลดลงเส้นตรง
            slope = (fc_prime * 0.85 - fc_prime) / (0.0038 - epsilon_0)
            f = fc_prime + slope * (eps - epsilon_0)
            if f < 0: f = 0
        stress.append(f)
    
    stress = np.array(stress)

    # จุดสำคัญ
    elastic_limit = fc_prime * 0.45
    idx_elastic = np.abs(stress[:50] - elastic_limit).argmin() # หาจุดใกล้เคียง Elastic Limit
    
    idx_peak = np.argmax(stress) # จุดยอด (Ultimate)
    
    # สร้างกราฟ Plotly
    fig = go.Figure()
    
    # เส้นกราฟหลัก
    fig.add_trace(go.Scatter(x=strain, y=stress, mode='lines', name='Stress-Strain Curve', line=dict(color='#2c3e50', width=3)))
    
    # จุด Elastic Limit (สีส้ม)
    fig.add_trace(go.Scatter(
        x=[strain[idx_elastic]], y=[stress[idx_elastic]],
        mode='markers+text',
        name='Elastic Limit',
        marker=dict(color='orange', size=10),
        text=['จุดยืดหยุ่น (Elastic)'], textposition="bottom right"
    ))
    
    # จุด Ultimate Strength (สีแดง) - ค่าที่ AI ทำนาย
    fig.add_trace(go.Scatter(
        x=[strain[idx_peak]], y=[stress[idx_peak]],
        mode='markers+text',
        name='Ultimate Strength',
        marker=dict(color='red', size=12),
        text=[f'จุดรับแรงสูงสุด (Max Load)<br>{fc_prime:.2f} ksc'], textposition="top center"
    ))
    
    # จุด Failure (สีดำ)
    fig.add_trace(go.Scatter(
        x=[strain[-1]], y=[stress[-1]],
        mode='markers',
        name='Failure',
        marker=dict(color='black', size=10, symbol='x')
    ))

    fig.update_layout(
        title="จำลองกราฟความสัมพันธ์ Stress-Strain (Simulation)",
        xaxis_title="ความเครียด (Strain)",
        yaxis_title="หน่วยแรง (Stress - ksc)",
        hovermode="x unified",
        template="plotly_white",
        height=400
    )
    
    return fig

# -------------------------------------------
# 3. Sidebar Input
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดค่าพารามิเตอร์")
    st.markdown("ระบุสัดส่วนผสม (หน่วย กก./ลบ.ม.)")
    st.markdown("---")
    
    st.subheader("1. วัสดุประสาน (Binder)")
    cement = st.number_input("ปูนซีเมนต์ (Cement)", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก (Blast Furnace Slag)", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย (Fly Ash)", 0.0, 1000.0, 0.0)
    
    st.markdown("---")
    
    st.subheader("2. ของเหลวและสารผสมเพิ่ม")
    water = st.number_input("น้ำ (Water)", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ (Superplasticizer)", 0.0, 100.0, 0.0)
    
    total_binder = cement + slag + flyash
    if total_binder > 0:
        wb_ratio = water / total_binder
        st.info(f"w/b ratio: {wb_ratio:.3f}")
    
    st.markdown("---")
    
    st.subheader("3. มวลรวม (Aggregates)")
    coarse = st.number_input("หิน (Coarse Aggregate)", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย (Fine Aggregate)", 0.0, 2000.0, 800.0)
    
    st.markdown("---")
    
    st.subheader("4. อายุบ่ม")
    age = st.slider("อายุ (วัน)", 1, 365, 28)

# -------------------------------------------
# 4. Main Interface
# -------------------------------------------

st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

col_result, col_chart = st.columns([1.2, 1])

if st.sidebar.button(" คำนวณกำลังอัด"):
    
    # Animation
    with st.spinner('กำลังประมวลผลและจำลองกราฟ (Analyzing)...'):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        time.sleep(0.5)
        progress_bar.empty()

    # Prepare Data
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # Predict
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    # === ส่วนแสดงผล Gauge Chart ===
    with col_result:
        st.subheader("ผลการทำนาย (Prediction)")
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pred_ksc,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "กำลังอัด (ksc)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 1000], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#2c3e50"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 180], 'color': '#ff4b4b'},
                    {'range': [180, 280], 'color': '#ffa421'},
                    {'range': [280, 450], 'color': '#21c354'},
                    {'range': [450, 1000], 'color': '#00c0f2'}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pred_ksc}
            }
        ))
        fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"เทียบเท่ากับ **{pred_mpa:.2f} MPa**")

    # === ส่วนแสดงผล Mix Analysis ===
    with col_chart:
        st.subheader("สัดส่วนผสม (Mix Proportion)")
        input_summary = {
            "รายการ": ["ซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"],
            "ปริมาณ (กก.)": [cement, slag, flyash, water, superplastic, coarse, fine]
        }
        df_summary = pd.DataFrame(input_summary)
        st.bar_chart(df_summary.set_index("รายการ"))

    # === ส่วนแสดงผล Stress-Strain Graph (ใหม่) ===
    st.markdown("---")
    st.subheader("📈 กราฟจำลองพฤติกรรมรับแรง (Simulated Stress-Strain Curve)")
    
    # เรียกใช้ฟังก์ชันสร้างกราฟ
    fig_stress_strain = plot_stress_strain(pred_ksc)
    st.plotly_chart(fig_stress_strain, use_container_width=True)
    
    st.caption("""
    *หมายเหตุ: กราฟนี้เป็นการจำลองพฤติกรรม (Simulation) ตามสมการมาตรฐาน Hognestad's Parabola 
    โดยอ้างอิงจากค่ากำลังอัดสูงสุดที่ AI ทำนายได้ เพื่อแสดงแนวโน้มพฤติกรรมของวัสดุเท่านั้น
    """)

else:
    st.info("👈 กรุณากดปุ่ม ' คำนวณกำลังอัด' เพื่อเริ่มการวิเคราะห์")


