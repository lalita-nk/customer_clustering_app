# -*- coding: utf-8 -*-
"""
customer_clustering.py
======================
โมดูลหลักสำหรับ "การแบ่งกลุ่มลูกค้าร้านเครื่องดื่ม"

ปรับปรุงจากไฟล์ Colab เดิม (Customer Clustering.ipynb) โดยแปลงสคริปต์
ที่รันทีเดียวจากบนลงล่าง ให้กลายเป็น "ฟังก์ชัน" ที่ app.py (Streamlit)
เรียกใช้ซ้ำได้ตามที่ผู้ใช้กดปุ่ม

สิ่งที่แก้ไขจากโค้ดเดิม
----------------------
1) เพิ่ม `import numpy as np` (โค้ดเดิมเรียก np.unique / np.sum แต่ไม่ได้ import -> error)
2) แปลงคอลัมน์เวลา HH:MM เป็นตัวเลข (นาที) แบบอัตโนมัติ ไม่ผูกกับชื่อ 'Time' อย่างเดียว
3) การ scale และการ fit โมเดล ใช้ "เฉพาะ 2 คอลัมน์ที่ผู้ใช้เลือกจาก dropdown" เท่านั้น
4) แยกส่วนวาดกราฟเป็นฟังก์ชันที่ "คืนค่า fig" แทน plt.show() เพราะ Streamlit ใช้ st.pyplot(fig)

การเลือกวิธีแบ่งกลุ่ม (สำคัญ)
-----------------------------
โจทย์ต้องการผลลัพธ์แบบเดียวกับที่ทำมือด้วย DBSCAN คือ "แบ่งตามความหนาแน่นของข้อมูล"
(ลูกค้าเกาะกันเป็นช่วงเวลา เช้า / กลางวัน / เย็น) แต่หน้าเว็บต้องให้ผู้ใช้เลือก
"จำนวนกลุ่ม" ได้ ซึ่ง DBSCAN ไม่รับจำนวนกลุ่มเป็นพารามิเตอร์

จึงใช้ Agglomerative Clustering แบบ single linkage (nearest-neighbour linkage) เพราะ
  - รับจำนวนกลุ่ม (n_clusters) ได้ตรงตามโจทย์
  - เกณฑ์การรวมกลุ่มคือ "ระยะห่างระหว่างจุดที่ใกล้ที่สุดของสองกลุ่ม" จุดที่เกาะกัน
    หนาแน่นจะถูกต่อกันเป็นสายเดียว และจะถูก "ตัด" ตรงช่องว่างที่กว้างที่สุดก่อนเสมอ
    ผลลัพธ์จึงแบ่งตามความหนาแน่น/ช่องว่างของข้อมูล เหมือนแนวคิดของ DBSCAN
  - ต่างจาก KMeans ที่บังคับให้กลุ่มมีรูปทรงกลมและขนาดใกล้เคียงกัน ซึ่งจะตัดกลาง
    ช่วงเวลาที่ข้อมูลเกาะกันอยู่ ทำให้ไม่ตรงกับตัวอย่างที่ทำมือ

ยังคงฟังก์ชัน run_dbscan() ไว้ สำหรับเทียบผลกับวิธีเดิมในห้องเรียน
"""

import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

# ใช้ backend แบบไม่มีหน้าต่าง (สำคัญเวลารันบนเซิร์ฟเวอร์/Streamlit)
matplotlib.use("Agg")

# URL ของไฟล์ข้อมูลตั้งต้น (ไฟล์เดียวกับใน Colab เดิม)
DEFAULT_DATA_URL = "https://drive.google.com/uc?id=1ssmPU63mIKtgworDbsQTIZ0dVvjP-5rI"

# รูปแบบข้อความที่ถือว่าเป็น "เวลา" เช่น 9:05, 09:05, 09:05:30
_TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


# ---------------------------------------------------------------------------
# 1) ส่วนโหลดและเตรียมข้อมูล
# ---------------------------------------------------------------------------
def load_data(source=DEFAULT_DATA_URL):
    """อ่านไฟล์ CSV จาก URL หรือ path หรือไฟล์ที่อัปโหลดผ่าน Streamlit

    Parameters
    ----------
    source : str | file-like
        URL, path ของไฟล์ในเครื่อง หรืออ็อบเจ็กต์ไฟล์จาก st.file_uploader

    Returns
    -------
    pandas.DataFrame  ข้อมูลดิบที่ผ่านการเตรียมคอลัมน์เวลาแล้ว
    """
    df = pd.read_csv(source)
    df = add_time_features(df)
    return df


def add_time_features(df):
    """แปลงคอลัมน์ข้อความที่เป็นเวลา (HH:MM) ให้เป็นตัวเลข "นาทีนับจากเที่ยงคืน"

    โค้ดเดิมทำเฉพาะคอลัมน์ชื่อ 'Time' แบบ hard-code
    เวอร์ชันนี้ตรวจทุกคอลัมน์ที่เป็นข้อความ ถ้าเข้ารูปแบบเวลาทั้งคอลัมน์
    จะสร้างคอลัมน์ใหม่ชื่อ '<ชื่อเดิม>_minutes' ให้อัตโนมัติ
    เพื่อให้นำไปใช้เป็นแกน x/y และใช้คำนวณ clustering ได้
    """
    df = df.copy()

    for col in df.columns:
        # ข้ามคอลัมน์ที่เป็นตัวเลข/วันที่อยู่แล้ว สนใจเฉพาะคอลัมน์ข้อความ
        # (ใช้ API ของ pandas แทนการเทียบ dtype == object เพื่อให้รองรับ
        #  ทั้ง pandas 2.x และ 3.x ที่ข้อความเป็น StringDtype)
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(
            df[col]
        ):
            continue

        sample = df[col].dropna().astype(str)
        if sample.empty:
            continue

        # ทุกค่าต้องอยู่ในรูปแบบเวลา จึงจะถือว่าเป็นคอลัมน์เวลา
        if not sample.map(lambda v: bool(_TIME_PATTERN.match(v.strip()))).all():
            continue

        parts = df[col].astype(str).str.strip().str.split(":", expand=True)
        df[f"{col}_minutes"] = parts[0].astype(int) * 60 + parts[1].astype(int)

    return df


def get_numeric_columns(df):
    """คืนรายชื่อคอลัมน์ตัวเลข สำหรับใช้เป็นตัวเลือกใน dropdown แกน x และ y"""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def _is_time_column(col_name):
    """เช็กว่าคอลัมน์นี้เป็นคอลัมน์เวลาที่แปลงเป็นนาทีไว้หรือไม่"""
    return str(col_name).endswith("_minutes")


def _apply_time_axis_format(ax, x_col, y_col):
    """ถ้าแกนไหนเป็นคอลัมน์เวลา (หน่วยนาที) ให้แสดง label กลับเป็น HH:MM"""
    formatter = FuncFormatter(lambda v, pos: f"{int(v) // 60:02d}:{int(v) % 60:02d}")

    if _is_time_column(x_col):
        ax.xaxis.set_major_formatter(formatter)
    if _is_time_column(y_col):
        ax.yaxis.set_major_formatter(formatter)


# ---------------------------------------------------------------------------
# 2) กราฟก่อนแบ่งกลุ่ม (Before Clustering)
# ---------------------------------------------------------------------------
def plot_scatter_before(df, x_col, y_col, figsize=(10, 5)):
    """วาด scatter plot ของข้อมูลดิบ โดยใช้เฉพาะคอลัมน์ x, y ที่ผู้ใช้เลือก

    Returns
    -------
    matplotlib.figure.Figure  เพื่อให้ Streamlit นำไปแสดงด้วย st.pyplot(fig)
    """
    # เลือกเฉพาะ 2 คอลัมน์ที่สนใจ และตัดแถวที่มีค่าว่างทิ้ง
    data = df[[x_col, y_col]].dropna()

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(data[x_col], data[y_col], color="teal", alpha=0.8)

    ax.set_title(f"{x_col} vs {y_col} (Original Data)")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(alpha=0.3)

    _apply_time_axis_format(ax, x_col, y_col)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 3) ส่วนแบ่งกลุ่มลูกค้า (รองรับการเลือก "จำนวนกลุ่ม")
# ---------------------------------------------------------------------------
def run_clustering(df, x_col, y_col, n_clusters=3):
    """แบ่งกลุ่มลูกค้าตามความหนาแน่นของข้อมูล โดยใช้เฉพาะคอลัมน์ x, y ที่เลือก

    วิธีที่ใช้: Agglomerative Clustering แบบ single linkage
    ทำงานโดยเริ่มจากให้ทุกจุดเป็นกลุ่มของตัวเอง แล้วรวมสองกลุ่มที่ "จุดใกล้ที่สุด
    ของแต่ละกลุ่มอยู่ใกล้กันที่สุด" ไปเรื่อย ๆ จนเหลือตามจำนวนกลุ่มที่กำหนด
    ผลคือกลุ่มจะถูกแบ่งตรงช่องว่าง (gap) ที่กว้างที่สุดของข้อมูลก่อนเสมอ
    เช่น ช่วงที่ไม่มีลูกค้าเข้าร้านเลยระหว่าง 08:00-11:00 และ 12:30-15:00

    ขั้นตอน
    1) ดึงเฉพาะ 2 คอลัมน์ที่เลือก แล้วตัดค่าว่างออก
    2) ทำ StandardScaler เพื่อให้ทั้งสองแกนมีสเกลเทียบเท่ากัน
       (เวลา 0-1440 นาที กับความหวาน 0-125 ต่างกันมาก ถ้าไม่ scale
        การวัดระยะทางจะเอนเอียงไปตามคอลัมน์ที่ค่ามาก)
    3) แบ่งกลุ่มตามจำนวนกลุ่มที่ผู้ใช้เลือกจาก slider

    Returns
    -------
    data  : DataFrame ที่มีคอลัมน์ x, y และ 'Cluster'
    model : อ็อบเจ็กต์โมเดลที่ fit แล้ว (เผื่อต้องการดูรายละเอียดเพิ่ม)
    """
    data = df[[x_col, y_col]].dropna().copy()

    # ป้องกันกรณีจำนวนกลุ่มมากกว่าจำนวนข้อมูล
    n_clusters = int(min(n_clusters, len(data)))

    scaler = StandardScaler()
    scaled = scaler.fit_transform(data[[x_col, y_col]])

    model = AgglomerativeClustering(n_clusters=n_clusters, linkage="single")
    data["Cluster"] = model.fit_predict(scaled)

    # เรียงหมายเลขกลุ่มใหม่ตามค่าเฉลี่ยของแกน x (กลุ่ม 0 = ช่วงแรกสุด)
    # เพื่อให้สีและลำดับในตารางสรุปอ่านง่าย ไม่สลับไปมาทุกครั้งที่รัน
    order = data.groupby("Cluster")[x_col].mean().sort_values().index
    remap = {old: new for new, old in enumerate(order)}
    data["Cluster"] = data["Cluster"].map(remap)

    return data, model


def run_dbscan(df, x_col, y_col, eps=0.7, min_samples=5):
    """(ทางเลือก) แบ่งกลุ่มด้วย DBSCAN ตามโค้ดเดิม

    เก็บไว้เผื่อต้องการเปรียบเทียบผลกับวิธีที่ใช้ใน run_clustering()
    หมายเหตุ: จุดที่ถูกจัดเป็น noise จะได้ label = -1
    """
    data = df[[x_col, y_col]].dropna().copy()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(data[[x_col, y_col]])

    model = DBSCAN(eps=eps, min_samples=min_samples)
    data["Cluster"] = model.fit_predict(scaled)

    labels = model.labels_
    n_clusters = len(np.unique(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))

    return data, n_clusters, n_noise


# ---------------------------------------------------------------------------
# 4) กราฟหลังแบ่งกลุ่ม (After Clustering)
# ---------------------------------------------------------------------------
def plot_scatter_after(data, x_col, y_col, figsize=(10, 5)):
    """วาด scatter plot ที่ระบายสีตามกลุ่มที่แบ่งได้

    Parameters
    ----------
    data : DataFrame ที่ได้จาก run_clustering (ต้องมีคอลัมน์ 'Cluster')
    """
    fig, ax = plt.subplots(figsize=figsize)

    # ระบายสีจุดตามหมายเลขกลุ่ม โดยใช้เฉพาะคอลัมน์ x, y ที่ผู้ใช้เลือก
    scatter = ax.scatter(
        data[x_col],
        data[y_col],
        c=data["Cluster"],
        cmap="viridis",
        alpha=0.85,
    )

    ax.set_title(f"Customer Clusters: {x_col} vs {y_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(alpha=0.3)

    _apply_time_axis_format(ax, x_col, y_col)

    # legend แสดงหมายเลขกลุ่ม
    legend = ax.legend(*scatter.legend_elements(), title="Cluster", loc="best")
    ax.add_artist(legend)

    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


def summarize_clusters(data, x_col, y_col):
    """สรุปผลแต่ละกลุ่ม: จำนวนสมาชิก และค่าเฉลี่ยของแกน x, y

    ใช้แสดงเป็นตารางใต้กราฟ เพื่ออธิบายว่าลูกค้าแต่ละกลุ่มมีลักษณะอย่างไร
    """
    summary = (
        data.groupby("Cluster")
        .agg(
            จำนวนลูกค้า=(x_col, "size"),
            **{
                f"ค่าเฉลี่ย {x_col}": (x_col, "mean"),
                f"ค่าเฉลี่ย {y_col}": (y_col, "mean"),
            },
        )
        .reset_index()
        .round(2)
    )

    # ถ้าแกนไหนเป็นเวลา ให้เพิ่มคอลัมน์ที่อ่านง่ายเป็น HH:MM
    for col in (x_col, y_col):
        if _is_time_column(col):
            summary[f"ค่าเฉลี่ย {col} (HH:MM)"] = summary[f"ค่าเฉลี่ย {col}"].map(
                lambda v: f"{int(v) // 60:02d}:{int(v) % 60:02d}"
            )

    return summary


# ---------------------------------------------------------------------------
# ส่วนทดสอบเมื่อรันไฟล์นี้ตรง ๆ (python customer_clustering.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo = load_data()
    print(demo.head())
    print("คอลัมน์ตัวเลขที่ใช้ได้:", get_numeric_columns(demo))

    # ทดลองแบ่งกลุ่มด้วยคอลัมน์เวลาและความหวาน
    if "Time_minutes" in demo.columns and "Sweetness" in demo.columns:
        result, _ = run_clustering(demo, "Time_minutes", "Sweetness", n_clusters=3)
        print(summarize_clusters(result, "Time_minutes", "Sweetness"))