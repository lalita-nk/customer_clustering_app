# -*- coding: utf-8 -*-
"""
app.py
======
หน้าเว็บ Streamlit สำหรับ "การแบ่งกลุ่มลูกค้าร้านเครื่องดื่ม"

โครงหน้าเว็บ
  ขั้นตอนที่ 1 : ปุ่ม "แสดงข้อมูล" / "ย่อข้อมูล" + slider เลือกจำนวนแถว / checkbox ดูทั้งหมด
  ขั้นตอนที่ 2 : ปุ่ม "แสดงกราฟ Scatter Plot (Before Clustering)" + dropdown แกน x, y
  ขั้นตอนที่ 3 : ปุ่ม "แสดงกราฟ Scatter Plot (After Clustering)"  + dropdown แกน x, y
                 + slider เลือก "จำนวนกลุ่ม"

ข้อมูล: อ่านจาก URL บน Google Drive ที่กำหนดไว้ใน customer_clustering.py เท่านั้น

วิธีรัน:  streamlit run app.py
"""

import streamlit as st

# เรียกใช้ฟังก์ชันทั้งหมดจากโมดูลที่ปรับปรุงไว้
import customer_clustering as cc

# ---------------------------------------------------------------------------
# 1) ตั้งค่าหน้าเพจ (ต้องเป็นคำสั่ง Streamlit คำสั่งแรก)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="การแบ่งกลุ่มลูกค้าร้านเครื่องดื่ม",
    page_icon="🥤",
    layout="wide",  # ใช้ wide ก่อน แล้วค่อยบีบด้วย CSS ให้เหลือ 70% ตรงกลาง
)

# ---------------------------------------------------------------------------
# 2) CSS: กำหนดพื้นที่แสดงผลกลางจอ 70% และขนาดฟอนต์ของ Title / h1 / h2
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* --- พื้นที่แสดงผลตรงกลาง กว้าง 70% ของหน้าจอ --- */
    .block-container {
        max-width: 70% !important;   /* ความกว้างสูงสุด 70% ของจอ */
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* --- ขนาดฟอนต์ของ Title (หัวข้อหลักของเว็บ) --- */
    .app-title {
        font-size: 44px !important;
        font-weight: 800;
        text-align: center;
        color: #0E7C86;
        margin-bottom: 0.2em;
    }
    .app-subtitle {
        font-size: 18px !important;
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.5em;
    }

    /* --- ขนาดฟอนต์ของ h1 --- */
    h1, .custom-h1 {
        font-size: 36px !important;
        font-weight: 700 !important;
    }

    /* --- ขนาดฟอนต์ของ h2 (ใช้เป็นหัวข้อของแต่ละขั้นตอน) --- */
    h2, .custom-h2 {
        font-size: 28px !important;
        font-weight: 700 !important;
        padding-left: 12px;
        margin-top: 1.2em;
    }

    /* --- เส้นคั่นระหว่างแต่ละขั้นตอน --- */
    hr.step-divider {
        border: none;
        border-top: 2px dashed #b8c4c9;
        margin: 2.5rem 0 1.5rem 0;
    }

    /* ขนาดฟอนต์ของข้อความทั่วไปและปุ่ม */
    .stButton > button {
        font-size: 18px;
        font-weight: 600;
        padding: 0.5em 1.5em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 3) Title ของหน้าเว็บ
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="app-title">การแบ่งกลุ่มลูกค้าร้านเครื่องดื่ม</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Customer Segmentation — จัดกลุ่มลูกค้าตามพฤติกรรมการสั่งเครื่องดื่ม</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 4) โหลดข้อมูล (ใส่ cache ไว้ เพื่อไม่ให้ดาวน์โหลดใหม่ทุกครั้งที่กดปุ่ม)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="กำลังโหลดข้อมูล...")
def load_dataset(source):
    """หุ้ม cc.load_data ด้วย cache ของ Streamlit"""
    return cc.load_data(source)


# บังคับใช้ข้อมูลจาก URL บน Google Drive เท่านั้น (ไม่มีการอัปโหลดไฟล์เอง)
source = cc.DEFAULT_DATA_URL

try:
    df = load_dataset(source)
except Exception as error:  # อ่านข้อมูลไม่สำเร็จ เช่น ไม่มีอินเทอร์เน็ต
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {error}")
    st.info("กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต และสิทธิ์การเข้าถึงไฟล์บน Google Drive")
    st.stop()

# รายชื่อคอลัมน์ตัวเลข สำหรับใช้เป็นตัวเลือกแกน x / y
numeric_cols = cc.get_numeric_columns(df)
if len(numeric_cols) < 2:
    st.error("ข้อมูลมีคอลัมน์ตัวเลขน้อยกว่า 2 คอลัมน์ จึงวาด scatter plot ไม่ได้")
    st.stop()

# ---------------------------------------------------------------------------
# 5) เตรียม session_state
#    เพราะปุ่มใน Streamlit จะเป็น True แค่รอบเดียวที่กด ถ้าไม่เก็บสถานะไว้
#    กราฟจะหายทันทีเมื่อผู้ใช้ไปแตะ widget อื่น
# ---------------------------------------------------------------------------
for key in ("show_data", "show_before", "show_after"):
    st.session_state.setdefault(key, False)

# ===========================================================================
# ขั้นตอนที่ 1 : แสดงข้อมูล
# ===========================================================================
st.markdown('<h2 class="custom-h2">ขั้นตอนที่ 1 : แสดงข้อมูล</h2>', unsafe_allow_html=True)

total_rows = len(df)

col1, col2 = st.columns([2, 1])
with col1:
    # slider เลือกจำนวนแถวที่ต้องการแสดง
    n_rows = st.slider(
        "เลือกจำนวนแถวที่ต้องการแสดง",
        min_value=1,
        max_value=total_rows,
        value=min(10, total_rows),
        step=1,
    )
with col2:
    # ทางเลือก: แสดงข้อมูลทั้งหมด
    show_all = st.checkbox("แสดงข้อมูลทั้งหมด", value=False)

# ปุ่มแสดงข้อมูล และ ปุ่มย่อข้อมูล วางเรียงกันในแถวเดียว
btn_show, btn_hide, _ = st.columns([1, 1, 3])

with btn_show:
    # กดแล้วเก็บสถานะไว้ใน session_state ว่าให้แสดงตาราง
    if st.button("📄 แสดงข้อมูล", key="btn_data"):
        st.session_state.show_data = True

with btn_hide:
    # กดแล้วย่อ (ซ่อน) ตารางข้อมูลที่แสดงอยู่
    if st.button("🔽 ย่อข้อมูล", key="btn_hide_data"):
        st.session_state.show_data = False

if st.session_state.show_data:
    data_to_show = df if show_all else df.head(n_rows)
    st.write(
        f"จำนวนข้อมูลทั้งหมด **{total_rows}** แถว "
        f"| กำลังแสดง **{len(data_to_show)}** แถว "
        f"| จำนวนคอลัมน์ **{df.shape[1]}** คอลัมน์"
    )
    st.dataframe(data_to_show)

    # สรุปค่าสถิติเบื้องต้นของคอลัมน์ตัวเลข
    with st.expander("ดูค่าสถิติเบื้องต้น (describe)"):
        st.dataframe(df[numeric_cols].describe())


# เส้นคั่นระหว่างขั้นตอน
st.markdown('<hr class="step-divider">', unsafe_allow_html=True)

# ===========================================================================
# ขั้นตอนที่ 2 : Scatter Plot ก่อนแบ่งกลุ่ม
# ===========================================================================
st.markdown(
    '<h2 class="custom-h2">ขั้นตอนที่ 2 : Scatter Plot (Before Clustering)</h2>',
    unsafe_allow_html=True,
)

col_x, col_y = st.columns(2)
with col_x:
    # dropdown เลือกคอลัมน์แกน x
    x_before = st.selectbox(
        "เลือกคอลัมน์สำหรับแกน X",
        numeric_cols,
        index=0,
        key="x_before",
    )
with col_y:
    # dropdown เลือกคอลัมน์แกน y (ค่าเริ่มต้นเป็นคอลัมน์ที่ 2)
    y_before = st.selectbox(
        "เลือกคอลัมน์สำหรับแกน Y",
        numeric_cols,
        index=1,
        key="y_before",
    )

if st.button("📈 แสดงกราฟ Scatter Plot (Before Clustering)", key="btn_before"):
    st.session_state.show_before = True

if st.session_state.show_before:
    if x_before == y_before:
        st.warning("กรุณาเลือกคอลัมน์แกน X และแกน Y ให้ต่างกัน")
    else:
        # วาดกราฟจากเฉพาะ 2 คอลัมน์ที่เลือกเท่านั้น
        fig_before = cc.plot_scatter_before(df, x_before, y_before)
        st.pyplot(fig_before)


# เส้นคั่นระหว่างขั้นตอน
st.markdown('<hr class="step-divider">', unsafe_allow_html=True)

# ===========================================================================
# ขั้นตอนที่ 3 : Scatter Plot หลังแบ่งกลุ่ม (After Clustering)
# ===========================================================================
st.markdown(
    '<h2 class="custom-h2">ขั้นตอนที่ 3 : Scatter Plot (After Clustering)</h2>',
    unsafe_allow_html=True,
)

col_x2, col_y2 = st.columns(2)
with col_x2:
    # dropdown เลือกคอลัมน์แกน x สำหรับการแบ่งกลุ่ม
    x_after = st.selectbox(
        "เลือกคอลัมน์สำหรับแกน X (ใช้ในการแบ่งกลุ่ม)",
        numeric_cols,
        index=0,
        key="x_after",
    )
with col_y2:
    # dropdown เลือกคอลัมน์แกน y สำหรับการแบ่งกลุ่ม
    y_after = st.selectbox(
        "เลือกคอลัมน์สำหรับแกน Y (ใช้ในการแบ่งกลุ่ม)",
        numeric_cols,
        index=1,
        key="y_after",
    )

# slider เลือกจำนวนกลุ่มที่ต้องการแบ่ง
max_k = int(min(10, max(2, total_rows)))
n_clusters = st.slider(
    "เลือกจำนวนกลุ่ม (Number of Clusters)",
    min_value=2,
    max_value=max_k,
    value=min(3, max_k),
    step=1,
)

if st.button("🎯 แสดงกราฟ Scatter Plot (After Clustering)", key="btn_after"):
    st.session_state.show_after = True

if st.session_state.show_after:
    if x_after == y_after:
        st.warning("กรุณาเลือกคอลัมน์แกน X และแกน Y ให้ต่างกัน")
    else:
        # แบ่งกลุ่มโดยใช้เฉพาะ 2 คอลัมน์ที่ผู้ใช้เลือก
        clustered, model = cc.run_clustering(
            df, x_after, y_after, n_clusters=n_clusters
        )

        # วาดกราฟผลลัพธ์ (ระบายสีตามกลุ่ม ไม่มีจุด centroid)
        fig_after = cc.plot_scatter_after(clustered, x_after, y_after)
        st.pyplot(fig_after)

        st.success(
            f"แบ่งลูกค้าออกเป็น {n_clusters} กลุ่ม "
            f"โดยใช้คอลัมน์ '{x_after}' และ '{y_after}'"
        )

        # ตารางสรุปลักษณะของแต่ละกลุ่ม
        st.markdown("**สรุปลักษณะของแต่ละกลุ่ม**")
        st.dataframe(cc.summarize_clusters(clustered, x_after, y_after))

        # ให้ดาวน์โหลดผลลัพธ์เป็นไฟล์ CSV
        st.download_button(
            "⬇️ ดาวน์โหลดผลการแบ่งกลุ่ม (CSV)",
            data=clustered.to_csv(index=False).encode("utf-8-sig"),
            file_name="clustered_customers.csv",
            mime="text/csv",
        )