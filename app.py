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
    
    /* กล่องข้อความสูตร */
    .formula-box {
        background-color: #f8f9fa;
        border-left: 5px solid #2c3e50;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

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
    
    fig.add_trace(go.Scatter(
        x=[strain[idx_elastic]], y=[stress[idx_elastic]],
        mode='markers+text', name='Elastic Limit', marker=dict(color='orange', size=10),
        text=['Elastic Limit'], textposition="bottom right"
    ))
    
    fig.add_trace(go.Scatter(
        x=[strain[idx_peak]], y=[stress[idx_peak]],
        mode='markers+text', name='Ultimate Strength', marker=dict(color='red', size=12),
        text=[f'Max: {fc_prime:.2f} ksc'], textposition="top center"
    ))
    
    fig.add_trace(go.Scatter(
        x=[strain[-1]], y=[stress[-1]],
        mode='markers', name='Failure', marker=dict(color='black', size=10, symbol='x')
    ))

    fig.update_layout(
        title="กราฟจำลองพฤติกรรม Stress-Strain (Simulation)",
        xaxis_title="Strain", yaxis_title="Stress (ksc)",
        template="plotly_white", hovermode="x unified", height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# -------------------------------------------
# 3. Sidebar Input
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดค่าพารามิเตอร์")
    st.caption("ระบุสัดส่วนผสม (กก./ลบ.ม.)")
    st.markdown("---")
    
    st.subheader("1. วัสดุประสาน")
    cement = st.number_input("ปูนซีเมนต์", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย", 0.0, 1000.0, 0.0)
    
    st.subheader("2. ของเหลว")
    water = st.number_input("น้ำ", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ", 0.0, 100.0, 0.0)
    
    st.subheader("3. มวลรวม")
    coarse = st.number_input("หิน", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย", 0.0, 2000.0, 800.0)
    
    st.subheader("4. อายุบ่ม")
    age = st.slider("อายุ (วัน)", 1, 365, 28)

# -------------------------------------------
# 4. Main Interface
# -------------------------------------------

st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

col_result, col_chart = st.columns([1.2, 1])

if st.sidebar.button("🚀 คำนวณกำลังอัด"):
    
    with st.spinner('กำลังประมวลผล...'):
        time.sleep(1)

    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    # === Gauge Chart ===
    with col_result:
        st.subheader("ผลการทำนาย")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = pred_ksc,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "กำลังอัด (ksc)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 1000]}, 'bar': {'color': "#2c3e50"},
                'steps': [
                    {'range': [0, 180], 'color': '#ff4b4b'},
                    {'range': [180, 280], 'color': '#ffa421'},
                    {'range': [280, 450], 'color': '#21c354'},
                    {'range': [450, 1000], 'color': '#00c0f2'}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pred_ksc}
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"เทียบเท่า: **{pred_mpa:.2f} MPa**")

    # === Analysis & Excel ===
    with col_chart:
        st.subheader("สัดส่วนผสม")
        df_summary = pd.DataFrame({
            "รายการ": ["ซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"],
            "ปริมาณ": [cement, slag, flyash, water, superplastic, coarse, fine]
        })
        st.bar_chart(df_summary.set_index("รายการ"))
        
        export_df = pd.DataFrame({
            'Parameter': ['Cement', 'Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Agg', 'Fine Agg', 'Age', 'Predicted Strength (ksc)', 'Predicted Strength (MPa)'],
            'Value': [cement, slag, flyash, water, superplastic, coarse, fine, age, pred_ksc, pred_mpa],
            'Unit': ['kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'kg/m3', 'Days', 'ksc', 'MPa']
        })
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Result')
        st.download_button(label="📥 ดาวน์โหลดผลลัพธ์ (Excel)", data=buffer, file_name=f"concrete_result_{int(time.time())}.xlsx", mime="application/vnd.ms-excel")

    # === Stress-Strain Graph ===
    st.markdown("---")
    st.subheader("📈 กราฟจำลองพฤติกรรม Stress-Strain")
    fig_stress = plot_stress_strain(pred_ksc)
    st.plotly_chart(fig_stress, use_container_width=True)
    
    # =========================================================
    # ส่วนที่เพิ่มใหม่: รายการคำนวณและสูตร (Calculation Sheet)
    # =========================================================
    st.markdown("---")
    st.header("📝 รายการคำนวณประกอบ (Calculation Sheet)")
    
    with st.expander("คลิกเพื่อดูที่มาและสูตรการคำนวณ (Click to expand)", expanded=False):
        
        # 1. การคำนวณอัตราส่วน (Ratios)
        st.markdown("#### 1. การตรวจสอบอัตราส่วนส่วนผสม (Mix Proportion Check)")
        total_binder = cement + slag + flyash
        if total_binder > 0:
            wb_ratio = water / total_binder
        else:
            wb_ratio = 0
            
        st.markdown(f"""
        <div class="formula-box">
            <b>1.1 ปริมาณวัสดุประสานรวม (Total Binder):</b><br>
            $$ Binder = Cement + Slag + FlyAsh $$ <br>
            $$ Binder = {cement} + {slag} + {flyash} = {total_binder} \ kg/m^3 $$
            <br><br>
            <b>1.2 อัตราส่วนน้ำต่อวัสดุประสาน (w/b ratio):</b><br>
            $$ w/b = \\frac{{Water}}{{Binder}} $$ <br>
            $$ w/b = \\frac{{{water}}}{{{total_binder}}} = \\mathbf{{{wb_ratio:.3f}}} $$
        </div>
        """, unsafe_allow_html=True)

        # 2. การแปลงหน่วย (Unit Conversion)
        st.markdown("#### 2. การแปลงหน่วยกำลังอัด (Unit Conversion)")
        st.markdown(f"""
        <div class="formula-box">
            สูตรการแปลงหน่วยจาก MPa เป็น ksc (kg/cm²):<br>
            $$ 1 \ MPa \\approx 10.197 \ ksc $$ <br>
            $$ Strength_{{ksc}} = {pred_mpa:.2f} \\times 10.197 = \\mathbf{{{pred_ksc:.2f} \ ksc}} $$
        </div>
        """, unsafe_allow_html=True)

        # 3. ที่มาของกราฟ Stress-Strain (Hognestad)
        st.markdown("#### 3. สมการจำลองพฤติกรรม (Simulation Model)")
        st.markdown("""
        กราฟความสัมพันธ์ Stress-Strain ถูกจำลองขึ้นโดยใช้สมการ **Hognestad's Parabola** ซึ่งเป็นแบบจำลองพฤติกรรมคอนกรีตมาตรฐาน:
        """)
        st.latex(r'''
        f_c = f'_c \left[ \frac{2\epsilon}{\epsilon_0} - \left( \frac{\epsilon}{\epsilon_0} \right)^2 \right]
        ''')
        st.markdown("""
        โดยที่:
        * $f_c$ = หน่วยแรงที่ความเครียด $\epsilon$
        * $f'_c$ = กำลังอัดสูงสุด (ค่าจาก AI Prediction)
        * $\epsilon_0$ = ความเครียดที่จุดรับแรงสูงสุด (ใช้ค่า 0.002)
        """)
        
        # 4. หมายเหตุเกี่ยวกับ AI
        st.info("""
        **หมายเหตุ:** ค่ากำลังอัด ($f'_c$) ได้จากการทำนายด้วยโมเดลปัญญาประดิษฐ์ (Random Forest Regressor) 
        ซึ่งประมวลผลจากรูปแบบข้อมูลสถิติกว่า 1,000 ตัวอย่าง ไม่ได้เกิดจากการคำนวณด้วยสูตรเส้นตรงเพียงสูตรเดียว
        """)

else:
    st.info("👈 กรุณากดปุ่ม '🚀 คำนวณกำลังอัด' เพื่อเริ่มใช้งาน")
