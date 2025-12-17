import streamlit as st
import pandas as pd
import joblib
import time # สำหรับทำแอนิเมชั่นหน่วงเวลา
import plotly.graph_objects as go # สำหรับทำกราฟเข็มวัด (Gauge)

# -------------------------------------------
# 1. System Configuration
# -------------------------------------------
st.set_page_config(
    page_title="Concrete Compressive Strength Prediction",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Prediction Model
try:
    model = joblib.load('concrete_model.pkl')
    model_status = "System Ready"
except:
    st.error("Error: Model file (concrete_model.pkl) not found.")
    model_status = "System Error"

# -------------------------------------------
# 2. Custom CSS (Engineering Theme)
# -------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Sarabun', sans-serif;
    }
    
    /* Minimal Button Style */
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
# 3. Sidebar: Input Parameters
# -------------------------------------------
with st.sidebar:
    st.title("Input Parameters")
    st.markdown("Specify mix design proportions (kg/m³)")
    st.markdown("---")
    
    st.subheader("1. Binder Materials")
    cement = st.number_input("Cement Content", 0.0, 1000.0, 350.0)
    slag = st.number_input("Blast Furnace Slag", 0.0, 1000.0, 0.0)
    flyash = st.number_input("Fly Ash", 0.0, 1000.0, 0.0)
    
    st.markdown("---")
    
    st.subheader("2. Liquid & Admixtures")
    water = st.number_input("Water Content", 0.0, 500.0, 180.0)
    superplastic = st.number_input("Superplasticizer", 0.0, 100.0, 0.0)
    
    # Calculate w/b ratio
    total_binder = cement + slag + flyash
    if total_binder > 0:
        wb_ratio = water / total_binder
        st.info(f"Calculated w/b ratio: {wb_ratio:.3f}")
    
    st.markdown("---")
    
    st.subheader("3. Aggregates")
    coarse = st.number_input("Coarse Aggregate", 0.0, 2000.0, 1000.0)
    fine = st.number_input("Fine Aggregate", 0.0, 2000.0, 800.0)
    
    st.markdown("---")
    
    st.subheader("4. Curing Age")
    age = st.slider("Age (Days)", 1, 365, 28)

# -------------------------------------------
# 4. Main Interface
# -------------------------------------------

st.title("Concrete Strength Prediction System")
st.markdown(f"**Status:** {model_status} | **Model Type:** Random Forest Regressor")
st.markdown("---")

col_result, col_chart = st.columns([1.2, 1])

# Process Calculation
if st.sidebar.button("Calculate Strength"):
    
    # --- ANIMATION PART 1: Loading Bar ---
    # สร้างแอนิเมชั่นหลอกๆ ว่ากำลังคำนวณ (ให้ดูขลังขึ้น)
    with st.spinner('Analyzing Mix Design...'):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01) # หน่วงเวลา 0.01 วินาทีต่อรอบ
            progress_bar.progress(i + 1)
        time.sleep(0.5) # หน่วงเพิ่มนิดนึง
        progress_bar.empty() # ลบแถบโหลดออกเมื่อเสร็จ

    # Prepare Data
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # Prediction
    pred_mpa = model.predict(input_data)[0]
    pred_ksc = pred_mpa * 10.197
    
    # --- ANIMATION PART 2: Gauge Chart (เข็มวัด) ---
    with col_result:
        st.subheader("Prediction Results")
        
        # สร้างกราฟเข็มวัด (Gauge Chart) ด้วย Plotly
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pred_ksc,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Strength (ksc)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 1000], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#2c3e50"}, # สีเข็ม
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 180], 'color': '#ff4b4b'},   # Red Zone (Low)
                    {'range': [180, 280], 'color': '#ffa421'}, # Orange Zone (Normal)
                    {'range': [280, 450], 'color': '#21c354'}, # Green Zone (High)
                    {'range': [450, 1000], 'color': '#00c0f2'} # Blue Zone (Ultra)
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
        
        # Text Summary
        st.info(f"Equivalent to **{pred_mpa:.2f} MPa**")

    # --- Right Column: Mix Analysis ---
    with col_chart:
        st.subheader("Mix Proportion Analysis")
        
        # Data Table
        input_summary = {
            "Material": ["Cement", "Slag", "Fly Ash", "Water", "Superplasticizer", "Coarse Agg.", "Fine Agg."],
            "Qty (kg/m³)": [cement, slag, flyash, water, superplastic, coarse, fine]
        }
        df_summary = pd.DataFrame(input_summary)
        st.dataframe(df_summary, hide_index=True, use_container_width=True)
        
        # Bar Chart
        st.bar_chart(df_summary.set_index("Material"))

else:
    # Default State
    st.info("Please define the mix parameters and click 'Calculate Strength'.")
