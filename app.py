import streamlit as st
import pandas as pd
import joblib

# -------------------------------------------
# 1. ตั้งค่าหน้าเว็บ (Page Config)
# -------------------------------------------
st.set_page_config(
    page_title="ระบบทำนายกำลังอัดคอนกรีต",
    page_icon="🏗️",
    layout="wide"
)

# โหลดโมเดล
try:
    model = joblib.load('concrete_model.pkl')
except:
    st.error("⚠️ ไม่พบไฟล์โมเดล (concrete_model.pkl) กรุณาตรวจสอบ")

# -------------------------------------------
# 2. ส่วนหัว (Header)
# -------------------------------------------
st.title("🏗️ ระบบทำนายกำลังอัดคอนกรีต (AI)")
st.markdown("""
ระบบช่วยออกแบบและตรวจสอบกำลังอัดคอนกรีต (Compressive Strength) ด้วยปัญญาประดิษฐ์
""")
st.markdown("---")

# -------------------------------------------
# 3. ส่วนรับค่า (Input) - เป็นภาษาไทย
# -------------------------------------------
with st.sidebar:
    st.header("🎛️ กำหนดส่วนผสม (Mix Design)")
    st.caption("กรอกปริมาณส่วนผสมหน่วยเป็น kg/m³")
    
    st.subheader("1. วัสดุประสาน (Binder)")
    cement = st.number_input("ปูนซีเมนต์ (Cement)", min_value=0.0, max_value=1000.0, value=350.0)
    slag = st.number_input("สแลก (Blast Furnace Slag)", min_value=0.0, max_value=1000.0, value=0.0)
    flyash = st.number_input("เถ้าลอย (Fly Ash)", min_value=0.0, max_value=1000.0, value=0.0)
    
    st.subheader("2. ของเหลว (Liquid)")
    water = st.number_input("น้ำ (Water)", min_value=0.0, max_value=500.0, value=180.0)
    superplastic = st.number_input("สารลดน้ำ (Superplasticizer)", min_value=0.0, max_value=100.0, value=0.0)
    
    st.subheader("3. มวลรวม (Aggregate)")
    coarse = st.number_input("หิน (Coarse Aggregate)", min_value=0.0, max_value=2000.0, value=1000.0)
    fine = st.number_input("ทราย (Fine Aggregate)", min_value=0.0, max_value=2000.0, value=800.0)
    
    st.subheader("4. เงื่อนไขอื่นๆ")
    age = st.slider("อายุบ่ม (วัน)", min_value=1, max_value=365, value=28)
    
    # คำนวณ w/c ratio ให้ดู
    total_binder = cement + slag + flyash
    if total_binder > 0:
        wc_ratio = water / total_binder
        st.info(f"💧 สัดส่วนน้ำต่อวัสดุประสาน (w/b): {wc_ratio:.2f}")

# -------------------------------------------
# 4. ส่วนแสดงผล (Main Dashboard)
# -------------------------------------------
col1, col2 = st.columns([1.5, 1])

if st.sidebar.button("🚀 คำนวณกำลังอัด", type="primary"):
    
    # เตรียมข้อมูล
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    
    # ทำนายผล
    prediction_mpa = model.predict(input_data)[0]
    prediction_ksc = prediction_mpa * 10.197
    
    with col1:
        st.subheader("🎯 ผลลัพธ์การทำนาย")
        
        # แสดงตัวเลขใหญ่ๆ
        st.metric(
            label=f"กำลังอัดคาดการณ์ที่อายุ {age} วัน",
            value=f"{prediction_ksc:.2f} ksc",
            delta=f"{prediction_mpa:.2f} MPa"
        )
        
        # แสดงเกณฑ์มาตรฐานแบบ Progress Bar
        st.write("ระดับความสามารถในการรับแรง:")
        
        # สมมติเกณฑ์ Max ที่ 800 ksc เพื่อทำหลอดสี
        progress_val = min(prediction_ksc / 800, 1.0) 
        
        if prediction_ksc < 180:
            st.error(f"กำลังต่ำ (Low Strength) - น้อยกว่า 180 ksc")
            st.progress(progress_val)
        elif prediction_ksc < 280:
            st.warning(f"กำลังปกติ (Normal Strength) - 180-280 ksc")
            st.progress(progress_val)
        elif prediction_ksc < 450:
            st.success(f"กำลังสูง (High Strength) - 280-450 ksc")
            st.progress(progress_val)
        else:
            st.info(f"กำลังสูงพิเศษ (Ultra High Strength) - มากกว่า 450 ksc")
            st.progress(progress_val)

    with col2:
        st.subheader("📊 สัดส่วนผสม (กก./ลบ.ม.)")
        
        # สร้างกราฟแท่งแสดงส่วนผสม (ไม่รวมอายุ)
        mix_data = {
            'ปูนซีเมนต์': cement,
            'สแลก': slag,
            'เถ้าลอย': flyash,
            'น้ำ': water,
            'หิน': coarse,
            'ทราย': fine
        }
        st.bar_chart(mix_data)

else:
    st.info("👈 กรุณากรอกข้อมูลส่วนผสมทางเมนูด้านซ้าย แล้วกดปุ่ม 'คำนวณกำลังอัด'")
