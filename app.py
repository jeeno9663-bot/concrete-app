import streamlit as st
import pandas as pd
import joblib
import time # สำหรับทำแอนิเมชั่นหน่วงเวลา
import plotly.graph_objects as go # สำหรับทำกราฟเข็มวัด (Gauge)

# -------------------------------------------
# 1. ตั้งค่าหน้าเว็บ (System Configuration)
# -------------------------------------------
st.set_page_config(
    page_title="ระบบทำนายกำลังอัดคอนกรีต",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# โหลดโมเดลทำนายผล
try:
    model = joblib.load('concrete_model.pkl')
    model_status = "ระบบพร้อมใช้งาน (System Ready)"
except:
    st.error("ข้อผิดพลาด: ไม่พบไฟล์โมเดล (concrete_model.pkl) กรุณาตรวจสอบ")
    model_status = "เกิดข้อผิดพลาด (System Error)"

# -------------------------------------------
# 2. ปรับแต่ง CSS (Engineering Theme)
# -------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Sarabun', sans-serif;
    }
    
    /* ปรับแต่งปุ่มกดให้ดูเรียบง่าย */
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
# 3. แถบเมนูด้านซ้าย (Sidebar Input)
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
    
    # คำนวณ w/b ratio ให้ดูสดๆ
    total_binder = cement + slag + flyash
    if total_binder > 0:
        wb_ratio = water / total_binder
        st.info(f"คำนวณอัตราส่วนน้ำต่อวัสดุประสาน (w/b): {wb_ratio:.3f}")
    
    st.markdown("---")
    
    st.subheader("3. มวลรวม (Aggregates)")
    coarse = st.number_input("หิน (Coarse Aggregate)", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย (Fine Aggregate)", 0.0, 2000.0, 800.0)
    
    st.markdown("---")
    
    st.subheader("4. อายุบ่ม")
    age = st.slider("อายุ (วัน)", 1, 365, 28)

# -------------------------------------------
# 4. หน้าจอแสดงผลหลัก (Main Interface)
# -------------------------------------------

st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status} | **ประเภทโมเดล:** Random Forest Regressor")
st.markdown("---")

col_result, col_chart = st.columns([1.2, 1])

# เริ่มการคำนวณเมื่อกดปุ่ม
if st.sidebar.button("🚀 คำนวณกำลังอัด"):
    
    # --- ANIMATION PART 1: Loading Bar ---
    # สร้างแอนิเมชั่นหลอกๆ ว่ากำลังคำนวณ
    with st.spinner('กำลังวิเคราะห์ส่วนผสม (Analyzing)...'):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01) # หน่วงเวลา
            progress_bar.progress(i + 1)
        time.sleep(0.5)
        progress_bar.empty()

    # เตรียมข้อมูลสำหรับทำนาย
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # ทำนายผล
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    # --- ANIMATION PART 2: Gauge Chart (เข็มวัด) ---
    with col_result:
        st.subheader("ผลการทำนาย (Prediction Results)")
        
        # สร้างกราฟเข็มวัด (Gauge Chart) ด้วย Plotly
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pred_ksc,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "กำลังอัด (ksc)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 1000], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#2c3e50"}, # สีเข็ม
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 180], 'color': '#ff4b4b'},   # แดง (ต่ำ)
                    {'range': [180, 280], 'color': '#ffa421'}, # ส้ม (ปกติ)
                    {'range': [280, 450], 'color': '#21c354'}, # เขียว (สูง)
                    {'range': [450, 1000], 'color': '#00c0f2'} # ฟ้า (สูงมาก)
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': pred_ksc
                }
            }
        ))
        
        # ปรับขนาดกราฟ
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # สรุปผลเป็นตัวหนังสือ
        st.info(f"เทียบเท่ากับ **{pred_mpa:.2f} MPa**")

    # --- Right Column: Mix Analysis ---
    with col_chart:
        st.subheader("วิเคราะห์สัดส่วนผสม")
        
        # สร้างตารางข้อมูล
        input_summary = {
            "รายการวัสดุ": ["ปูนซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"],
            "ปริมาณ (กก./ลบ.ม.)": [cement, slag, flyash, water, superplastic, coarse, fine]
        }
        df_summary = pd.DataFrame(input_summary)
        st.dataframe(df_summary, hide_index=True, use_container_width=True)
        
        # กราฟแท่ง
        st.bar_chart(df_summary.set_index("รายการวัสดุ"))

else:
    # สถานะเริ่มต้น (ยังไม่กดปุ่ม)
    st.info("👈 กรุณากำหนดค่าส่วนผสมทางเมนูด้านซ้าย แล้วกดปุ่ม '🚀 คำนวณกำลังอัด'")

