# การแบ่งกลุ่มลูกค้าร้านเครื่องดื่ม (Streamlit App)

เว็บแอปสำหรับสอน/สาธิตการทำ Customer Segmentation ด้วย K-Means
พัฒนาต่อจากไฟล์ `Customer Clustering.ipynb` (Google Colab)

## โครงสร้างโฟลเดอร์

```
customer-clustering-app/
├── app.py                  # หน้าเว็บ Streamlit (UI ทั้ง 3 ขั้นตอน)
├── customer_clustering.py  # โมดูลประมวลผล: โหลดข้อมูล / เตรียมข้อมูล / KMeans / วาดกราฟ
├── requirements.txt        # รายการไลบรารีที่ต้องติดตั้ง
└── README.md               # ไฟล์นี้
```

> ไฟล์ `app.py` และ `customer_clustering.py` ต้องอยู่ในโฟลเดอร์เดียวกัน
> เพราะ `app.py` ใช้คำสั่ง `import customer_clustering as cc`

## การติดตั้ง

```bash
# 1) เข้าไปที่โฟลเดอร์โปรเจกต์
cd customer-clustering-app

# 2) (แนะนำ) สร้าง virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3) ติดตั้งไลบรารี
pip install -r requirements.txt
```

## การรัน

```bash
streamlit run app.py
```

เบราว์เซอร์จะเปิดที่ `http://localhost:8501` โดยอัตโนมัติ
(ถ้าไม่เปิดเอง ให้พิมพ์ URL นี้ในเบราว์เซอร์)

## วิธีใช้งานหน้าเว็บ

| ขั้นตอน | การทำงาน |
|--------|----------|
| 1 | เลื่อน slider เลือกจำนวนแถว (หรือติ๊ก "แสดงข้อมูลทั้งหมด") แล้วกดปุ่ม **แสดงข้อมูล** |
| 2 | เลือกคอลัมน์แกน X, Y จาก dropdown แล้วกดปุ่ม **แสดงกราฟ Scatter Plot (Before Clustering)** |
| 3 | เลือกคอลัมน์แกน X, Y และเลื่อน slider เลือก **จำนวนกลุ่ม** แล้วกดปุ่ม **แสดงกราฟ Scatter Plot (After Clustering)** |

- ข้อมูลอ่านจาก URL บน Google Drive ที่กำหนดไว้ใน `customer_clustering.py`
  (ตัวแปร `DEFAULT_DATA_URL`) เท่านั้น — ไม่มีการอัปโหลดไฟล์เอง จึงต้องต่ออินเทอร์เน็ตขณะรัน
- คอลัมน์เวลาแบบ `HH:MM` จะถูกแปลงเป็นคอลัมน์ตัวเลขชื่อ `<ชื่อคอลัมน์>_minutes` ให้อัตโนมัติ
  และแกนกราฟจะแสดงกลับเป็นรูปแบบ `HH:MM` ให้อ่านง่าย

## หมายเหตุทางเทคนิค

- การแบ่งกลุ่มใช้ **Agglomerative Clustering แบบ single linkage** ซึ่งแบ่งกลุ่มตาม
  ความหนาแน่น/ช่องว่างของข้อมูล (ให้ผลใกล้เคียง DBSCAN ในตัวอย่างที่ทำมือ)
  แต่ยังรับ "จำนวนกลุ่ม" จาก slider ได้ตามโจทย์
  (ฟังก์ชัน `run_dbscan()` ยังคงอยู่ในโมดูล หากต้องการเปรียบเทียบผลในห้องเรียน)
- ไม่มีการวาดจุด centroid บนกราฟ
- การแบ่งกลุ่มใช้ **เฉพาะ 2 คอลัมน์ที่เลือกจาก dropdown** และผ่าน `StandardScaler`
  ก่อนเข้าโมเดลเสมอ ผลลัพธ์บนกราฟจึงสอดคล้องกับแกนที่ผู้ใช้เลือกจริง