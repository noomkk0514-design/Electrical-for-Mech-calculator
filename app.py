import streamlit as st
import pandas as st_pd
import json
import os

st.set_page_config(page_title="Electrical System Calculator", page_icon="⚡", layout="wide")

st.title("⚡ Electrical for Mechanical Calculator")
st.markdown("Calculation of motor current, circuit breaker ratings (AT/AF), wire and conduit size selection, and total main circuit breaker calculation อ้างอิงตามมาตรฐานการติดตั้งทางไฟฟ้า สำหรับประเทศไทย พ.ศ. 2564 ของ วสท.")

with st.expander("ℹ️ คำอธิบายความหมายตัวย่อ (คลิกเพื่อดูรายละเอียด)"):
    st.markdown("""
    - **kW**: Kilowatt (กำลังไฟฟ้า)
    - **DOL**: Direct On Line (การสตาร์ทมอเตอร์โดยตรง)
    - **YD**: Star-Delta (การสตาร์ทแบบสตาร์-เดลต้า)
    - **SS**: Soft Starter (การสตาร์ทแบบซอฟต์สตาร์ท)
    - **VSD**: Variable Speed Drive (เครื่องควบคุมความเร็วมอเตอร์)
    - **AT**: Ampere Trip (พิกัดกระแสตัดวงจรของเบรกเกอร์)
    - **AF**: Ampere Frame (ขนาดโครงสร้างของเบรกเกอร์)
    - **L Cable / G Cable**: Line Cable (สายไฟเส้นไฟ) / Ground Cable (สายดิน)
    - **R**: Raceway (ท่อร้อยสายไฟ เช่น IMC)
    - **PVC SC**: PVC Single core (IEC01,NYY)
    - **PVC MC**: PVC Multicore (IEC10, NYY)
    - **XLPE SC**: XLPE Single core (CV)
    - **XLPE MC**: XLPE Multicore (CV)
    """)

@st.cache_data
def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    dataCSV = data.get("dataCSV", [])
    cableCSV = data.get("cableCSV", [])
    
    starters = {
        "DOL": 2,
        "YD": 1.5,
        "SS": 1.5,
        "VSD": 1.25,
        "adjustable": 1.1
    }
    
    motors = []
    kw_list = []
    for i in range(4, min(34, len(dataCSV))):
        row = dataCSV[i]
        kw_str = row.get("C5")
        rc_str = row.get("C6")
        if kw_str:
            try:
                kw = float(kw_str)
                rc = float(rc_str)
                motors.append({"kw": kw, "rateCurrent": rc})
                kw_list.append(kw_str)
            except ValueError:
                pass
                
    breakers = []
    for i in range(10, min(36, len(dataCSV))):
        row = dataCSV[i]
        at_str = row.get("C1")
        af_str = row.get("C2")
        if at_str and af_str:
            try:
                at = float(at_str)
                af = float(af_str)
                breakers.append({"at": at, "af": af})
            except ValueError:
                pass
                
    cable_map = {}
    for i in range(2, len(cableCSV)):
        row = cableCSV[i]
        key = row.get("C1")
        if key:
            cable_map[key] = {
                "lCable": row.get("C5", ""),
                "lSize": row.get("C6", ""),
                "lType": row.get("C8", ""),
                "gCable": row.get("C9", ""),
                "gSize": row.get("C10", ""),
                "gType": row.get("C12", ""),
                "rIn": row.get("C13", ""),
                "rSize": row.get("C14", ""),
                "rType": row.get("C15", "")
            }
            
    return starters, motors, kw_list, breakers, cable_map

try:
    starters, motors, kw_list, breakers, cable_map = load_data()
except Exception as e:
    st.error(f"Failed to load data. Ensure `data.json` is in the same directory. Error: {e}")
    st.stop()

def get_rate_current(kw_val):
    try:
        val = float(kw_val)
        for m in motors:
            if m["kw"] == val:
                return m["rateCurrent"]
    except:
        pass
    return 0.0

def get_breaker(sum_in):
    if sum_in == 0:
        return "-", "-"
    for b in breakers:
        if b["at"] >= sum_in:
            return str(b["at"]), str(b["af"])
    return "-", "-"

def get_cable(kw, cable_type, starter):
    norm_starter = starter
    if starter in ["SS", "VSD"]:
        norm_starter = "DOL"
    key = f"{kw}|{cable_type}|{norm_starter}"
    return cable_map.get(key, {
        "lCable": "-", "lSize": "-", "lType": "-", 
        "gCable": "-", "gSize": "-", "gType": "-", 
        "rIn": "-", "rSize": "-", "rType": "-"
    })

if "feeders" not in st.session_state:
    st.session_state.feeders = [
        {"id": 1, "name": "F1", "kw": "11", "start": "YD", "cableType": "PVC SC"},
        {"id": 2, "name": "F2", "kw": "11", "start": "YD", "cableType": "PVC SC"},
        {"id": 3, "name": "F3", "kw": "2.2", "start": "DOL", "cableType": "PVC SC"}
    ]
if "next_id" not in st.session_state:
    st.session_state.next_id = 4

st.subheader("Manage Feeders")
col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1.5, 1.5, 1, 1])
with col1:
    new_name = st.text_input("Name", value=f"F{st.session_state.next_id}")
with col2:
    new_kw = st.selectbox("Power (kW)", kw_list)
with col3:
    new_start = st.selectbox("Start Type", ["DOL", "YD", "SS", "VSD", "adjustable"])
with col4:
    new_ctype = st.selectbox("Cable Type", ["PVC SC", "PVC MC", "XLPE SC", "XLPE MC"])
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Feeder", use_container_width=True):
        st.session_state.feeders.append({
            "id": st.session_state.next_id,
            "name": new_name,
            "kw": new_kw,
            "start": new_start,
            "cableType": new_ctype
        })
        st.session_state.next_id += 1
        st.rerun()

st.divider()
st.subheader("Feeder Calculations")

# Calculate data for display
display_data = []
max_in_cal = 0
max_feeder_id = None

for f in st.session_state.feeders:
    rc = get_rate_current(f["kw"])
    xin = starters.get(f["start"], 1)
    sum_in = rc * xin
    at, af = get_breaker(sum_in)
    
    in_cal = float(at) if at != "-" else 0.0
    if in_cal > max_in_cal:
        max_in_cal = in_cal
        max_feeder_id = f["id"]
        
    cab = get_cable(f["kw"], f["cableType"], f["start"])
    
    display_data.append({
        "id": f["id"],
        "Feeder": f["name"],
        "kW": f["kw"],
        "Start": f["start"],
        "Cable Type": f["cableType"],
        "Rate (A)": round(rc, 2),
        "x In": xin,
        "Start (A)": round(sum_in, 2),
        "AT": at,
        "AF": af,
        "L Cable": f"{cab['lCable']} {cab['lSize']}",
        "L Type": cab['lType'],
        "G Cable": f"{cab['gCable']} {cab['gSize']}",
        "G Type": cab['gType'],
        "Raceway Size": cab['rSize'],
        "Raceway Type": cab['rType']
    })

# Main calculation logic
total_rate_current = 0.0
calculated_main = 0.0

for i, f in enumerate(st.session_state.feeders):
    f_disp = display_data[i]
    rc = f_disp["Rate (A)"]
    in_cal = float(f_disp["AT"]) if f_disp["AT"] != "-" else 0.0
    
    total_rate_current += rc
    if f["id"] == max_feeder_id:
        calculated_main += in_cal
    else:
        calculated_main += rc

main_at, main_af = get_breaker(calculated_main)

# Output Table
if len(display_data) > 0:
    for idx, d in enumerate(display_data):
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 8, 1])
            with c1: st.write(f"**{d['Feeder']}** ({d['kW']}kW, {d['Start']})")
            with c2: st.write(f"Rate: {d['Rate (A)']} A")
            with c3: 
                if d["id"] == max_feeder_id:
                    st.success(f"**AT: {d['AT']}**")
                else:
                    st.write(f"AT: {d['AT']}")
            with c4: st.write(f"Cable: {d['L Cable']} ({d['L Type']}) | G: {d['G Cable']} | R: {d['Raceway Size']} {d['Raceway Type']}")
            with c5:
                if st.button("🗑️", key=f"del_{d['id']}"):
                    st.session_state.feeders = [x for x in st.session_state.feeders if x["id"] != d["id"]]
                    st.rerun()
            st.divider()

st.subheader("Main Breaker Summary")
colA, colB, colC, colD = st.columns(4)
colA.metric("Total Rate Current", f"{total_rate_current:.2f} A")
colB.metric("Calculated Main Current", f"{calculated_main:.2f} A")
colC.metric("Main Breaker AT", f"{main_at} AT")
colD.metric("Main Breaker AF", f"{main_af} AF")
