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
    fig.add_trace(go.Scatter(x=[strain[idx_elastic]], y=[stress[idx_elastic]], mode='markers+text', name='Elastic Limit', marker=dict(color='orange', size=10), text=['Elastic Limit'], textposition="bottom right"))
    fig.add_trace(go.Scatter(x=[strain[idx_peak]], y=[stress[idx_peak]], mode='markers+text', name='Ultimate Strength', marker=dict(color='red', size=12), text=[f'Max: {fc_prime:.2f} ksc'], textposition="top center"))
    fig.add_trace(go.Scatter(x=[strain[-1]], y=[stress[-1]], mode='markers', name='Failure', marker=dict(color='black', size=10, symbol='x')))

    fig.update_layout(title="กราฟจำลองพฤติกรรม Stress-Strain (Simulation)", xaxis_title="Strain", yaxis_title="Stress (ksc)", template="plotly_white", hovermode="x unified", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# -------------------------------------------
# ฟังก์ชันสร้างกราฟ Sensitivity (ฉบับแก้ไข: ป้องกันเด้ง)
# -------------------------------------------
def plot_sensitivity(model, current_inputs, target_col, col_name_th):
    try:
        # 1. สร้างช่วงข้อมูลที่จะทดสอบ (20 จุด)
        current_val = current_inputs[target_col].values[0]
        if current_val == 0:
            x_values = np.linspace(0, 100, 20)
        else:
            x_values = np.linspace(max(0, current_val * 0.5), current_val * 1.5, 20)
        
        # 2. สร้างชุดข้อมูลจำลองแบบรวดเดียว (Batch Processing) แทนการวนลูป
        # วิธีนี้เร็วกว่าและเสถียรกว่ามาก
        temp_df = pd.concat([current_inputs] * len(x_values), ignore_index=True)
        temp_df[target_col] = x_values
        
        # 3. ทำนายผลรวดเดียว 20 ค่า
        pred_mpa = model.predict(temp_df)
        y_preds = pred_mpa * 10.197 # แปลงเป็น ksc
            
        # 4. สร้างกราฟ
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_values, y=y_preds, mode='lines', name='Trend', line=dict(color='#3498db', width=3)))
        
        # จุดปัจจุบัน
        current_pred = model.predict(current_inputs)[0] * 10.197
        fig.add_trace(go.Scatter(x=[current_val], y=[current_pred], mode='markers', name='Current Mix', marker=dict(color='red', size=12, symbol='circle')))
        
        fig.update_layout(
            title=f"แนวโน้มกำลังอัด เมื่อปรับเปลี่ยนปริมาณ '{col_name_th}'",
            xaxis_title=f"ปริมาณ {col_name_th} (กก./ลบ.ม.)",
            yaxis_title="กำลังอัด (ksc)",
            template="plotly_white",
            height=350
        )
        return fig
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการสร้างกราฟ: {e}")
        return go.Figure()

# -------------------------------------------
# 3. Sidebar Input
# -------------------------------------------
with st.sidebar:
    st.title("กำหนดค่าพารามิเตอร์")
    st.caption("ระบุสัดส่วนผสม (กก./ลบ.ม.)")
    st.markdown("---")
    cement = st.number_input("ปูนซีเมนต์", 0.0, 1000.0, 350.0)
    slag = st.number_input("สแลก", 0.0, 1000.0, 0.0)
    flyash = st.number_input("เถ้าลอย", 0.0, 1000.0, 0.0)
    water = st.number_input("น้ำ", 0.0, 500.0, 180.0)
    superplastic = st.number_input("สารลดน้ำ", 0.0, 100.0, 0.0)
    coarse = st.number_input("หิน", 0.0, 2000.0, 1000.0)
    fine = st.number_input("ทราย", 0.0, 2000.0, 800.0)
    age = st.slider("อายุบ่ม (วัน)", 1, 365, 28)

# -------------------------------------------
# 4. Main Interface
# -------------------------------------------
st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown(f"**สถานะ:** {model_status}")
st.markdown("---")

col_result, col_chart = st.columns([1.2, 1])

if st.sidebar.button("🚀 คำนวณกำลังอัด"):
    with st.spinner('กำลังประมวลผล...'):
        time.sleep(0.5)

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
                'steps': [{'range': [0, 180], 'color': '#ff4b4b'}, {'range': [180, 280], 'color': '#ffa421'}, {'range': [280, 450], 'color': '#21c354'}, {'range': [450, 1000], 'color': '#00c0f2'}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pred_ksc}
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"เทียบเท่า: **{pred_mpa:.2f} MPa**")

    # === Analysis & Excel ===
    with col_chart:
        st.subheader("สัดส่วนผสม")
        df_summary = pd.DataFrame({"รายการ": ["ซีเมนต์", "สแลก", "เถ้าลอย", "น้ำ", "สารลดน้ำ", "หิน", "ทราย"], "ปริมาณ": [cement, slag, flyash, water, superplastic, coarse, fine]})
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
    
    # === Calculation Sheet ===
    st.markdown("---")
    st.header("📝 รายการคำนวณประกอบ (Calculation Sheet)")
    total_binder = cement + slag + flyash
    wb_ratio = water / total_binder if total_binder > 0 else 0
    with st.expander("แสดงรายละเอียดการคำนวณ (Click to expand)", expanded=False):
        st.markdown("#### 1. การตรวจสอบส่วนผสม (Mix Proportion Check)")
        with st.container(border=True):
            st.markdown("**1.1 ปริมาณวัสดุประสานรวม (Total Binder)**")
            st.latex(rf"Binder = {cement} + {slag} + {flyash} = {total_binder} \; \text{{kg}}/m^3")
            st.markdown("**1.2 อัตราส่วนน้ำต่อวัสดุประสาน (w/b ratio)**")
            st.latex(rf"w/b = \frac{{{water}}}{{{total_binder}}} = \mathbf{{{wb_ratio:.3f}}}")
        st.markdown("#### 2. การแปลงหน่วยกำลังอัด (Unit Conversion)")
        with st.container(border=True):
            st.latex(rf"\text{{Strength}}_{{ksc}} = {pred_mpa:.2f} \times 10.197 = \mathbf{{{pred_ksc:.2f} \; \text{{ksc}}}}")

    # =========================================================
    # ส่วนที่แก้ไข: เพิ่ม Try-Except ป้องกันแอปเด้ง
    # =========================================================
    st.markdown("---")
    st.header("🔍 วิเคราะห์แนวโน้มผลกระทบ (Sensitivity Analysis)")
    
    target_var = st.selectbox("เลือกปัจจัยที่ต้องการวิเคราะห์:", 
                 ["ปูนซีเมนต์ (Cement)", "น้ำ (Water)", "เถ้าลอย (Fly Ash)", "อายุบ่ม (Age)"])
    
    map_dict = {
        "ปูนซีเมนต์ (Cement)": "Cement",
        "น้ำ (Water)": "Water",
        "เถ้าลอย (Fly Ash)": "Fly Ash",
        "อายุบ่ม (Age)": "Age"
    }
    
    selected_col = map_dict[target_var]
    
    # เรียกฟังก์ชันที่แก้บั๊กแล้ว
    fig_sens = plot_sensitivity(model, input_data, selected_col, target_var)
    st.plotly_chart(fig_sens, use_container_width=True)

else:
    st.info("👈 กรุณากดปุ่ม '🚀 คำนวณกำลังอัด' เพื่อเริ่มใช้งาน")

