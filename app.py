    # ... (ต่อจากส่วน Sensitivity Analysis เดิม) ...

    # =========================================================
    # ส่วนที่เพิ่มใหม่: 💰 วิเคราะห์ต้นทุน (Cost Analysis)
    # =========================================================
    st.markdown("---")
    st.header("💰 ประเมินราคาคอนกรีต (Cost Estimation)")
    
    with st.expander("กำหนดราคาวัสดุต่อหน่วย (คลิกเพื่อแก้ไขราคา)", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        p_cement = c1.number_input("ราคาปูน (บาท/กก.)", value=2.5)
        p_slag = c2.number_input("ราคาสแลก (บาท/กก.)", value=1.5)
        p_flyash = c3.number_input("ราคาเถ้าลอย (บาท/กก.)", value=1.0)
        p_water = c4.number_input("ราคาน้ำ (บาท/กก.)", value=0.015)
        
        c5, c6, c7 = st.columns(3)
        p_super = c5.number_input("สารลดน้ำ (บาท/กก.)", value=40.0)
        p_coarse = c6.number_input("ราคาหิน (บาท/กก.)", value=0.35)
        p_fine = c7.number_input("ราคาทราย (บาท/กก.)", value=0.30)

    # คำนวณราคา
    cost_cement = cement * p_cement
    cost_slag = slag * p_slag
    cost_flyash = flyash * p_flyash
    cost_water = water * p_water
    cost_super = superplastic * p_super
    cost_coarse = coarse * p_coarse
    cost_fine = fine * p_fine
    
    total_cost = cost_cement + cost_slag + cost_flyash + cost_water + cost_super + cost_coarse + cost_fine
    
    # แสดงผลราคา
    st.metric(label="ราคาประเมินต่อลูกบาศก์เมตร (Baht/m³)", value=f"{total_cost:,.2f} บาท")
    
    # กราฟโดนัทแสดงสัดส่วนต้นทุน
    cost_data = pd.DataFrame({
        'Material': ['Cement', 'Slag', 'Fly Ash', 'Water', 'Superplasticizer', 'Coarse Agg', 'Fine Agg'],
        'Cost': [cost_cement, cost_slag, cost_flyash, cost_water, cost_super, cost_coarse, cost_fine]
    })
    
    # กรองเอาเฉพาะตัวที่มีราคา > 0
    cost_data = cost_data[cost_data['Cost'] > 0]
    
    fig_cost = go.Figure(data=[go.Pie(labels=cost_data['Material'], values=cost_data['Cost'], hole=.4)])
    fig_cost.update_layout(title="สัดส่วนต้นทุนแยกตามวัสดุ", height=350)
    st.plotly_chart(fig_cost, use_container_width=True)
    
    st.info(f"💡 **Insight:** ราคาคอนกรีตสูตรนี้ส่วนใหญ่มาจาก **{cost_data.sort_values('Cost', ascending=False).iloc[0]['Material']}** ลองปรับลดส่วนนี้ลงหากต้องการประหยัดงบ")

# ... (จบส่วนที่เพิ่มใหม่) ...
