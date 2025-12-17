import streamlit as st
import pandas as pd
import joblib

# โหลดโมเดล
try:
    model = joblib.load('concrete_model.pkl')
except:
    st.error("ไม่พบไฟล์โมเดล")

st.title("🏗️ Concrete Strength Prediction")
st.write("ทำนายค่ากำลังอัดคอนกรีตด้วย AI")

# Sidebar
st.sidebar.header("Mix Design Inputs")
cement = st.sidebar.number_input("Cement (kg/m3)", 0.0, 1000.0, 350.0)
slag = st.sidebar.number_input("Blast Furnace Slag", 0.0, 1000.0, 0.0)
flyash = st.sidebar.number_input("Fly Ash", 0.0, 1000.0, 0.0)
water = st.sidebar.number_input("Water", 0.0, 500.0, 180.0)
superplastic = st.sidebar.number_input("Superplasticizer", 0.0, 100.0, 0.0)
coarse = st.sidebar.number_input("Coarse Aggregate", 0.0, 2000.0, 1000.0)
fine = st.sidebar.number_input("Fine Aggregate", 0.0, 2000.0, 800.0)
age = st.sidebar.slider("Age (Days)", 1, 365, 28)

if st.button("Calculate Strength"):
    input_data = pd.DataFrame([[cement, slag, flyash, water, superplastic, coarse, fine, age]],
                              columns=['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                                       'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 'Age'])
    prediction = model.predict(input_data)[0]
    ksc = prediction * 10.197
    st.success(f"Estimated Strength: {ksc:.2f} ksc")
