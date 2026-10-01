# 🛏️ Mattress Type Recommender (Neo4j Aura + Streamlit)

ระบบแนะนำประเภทที่นอนด้วย Graph Database ต่อยอดจาก `notebooks/045_MattressType_Neo4jAura.ipynb`
พร้อมฟังก์ชัน **เพิ่ม / แก้ไข / ลบ** ข้อมูล และ **รูปภาพที่นอน** ประกอบทุกประเภท
deploy ผ่าน **GitHub → Streamlit Community Cloud** ได้ทันที

## 1. แนวคิด

```text
(User)-[:PREFERS]->(MattressType)

Ben ─PREFERS→ Spring Mattress ←PREFERS─ Jeff ─PREFERS→ Foam Mattress  ⇒ แนะนำ Foam ให้ Ben
score = จำนวนเส้นทาง (path) ที่พาไปถึงที่นอนนั้น
```

ถ้าผู้ใช้ยังไม่มีความชอบเลย (cold start) ระบบจะแสดงที่นอนยอดนิยมแทน

Property ของ `MattressType`: `name` (unique), `name_th`, `description`, `firmness` (1–10), `best_for`, `image`

## 2. หน้าในเว็บ

| หน้า | ทำอะไรได้ |
|---|---|
| 🏠 หน้าหลัก | สถิติ, กราฟความนิยม, แกลเลอรีที่นอนพร้อมรูป + ค้นหา |
| ✨ แนะนำที่นอน | เลือกผู้ใช้ → ดูที่นอนที่ชอบ + คำแนะนำพร้อมเหตุผล, กด ❤️ เพื่อเพิ่มความชอบ |
| 🛏️ จัดการที่นอน | รายการ / เพิ่ม / แก้ไข / ลบ ประเภทที่นอน + เลือกรูป (รูปในระบบ, อัปโหลด, URL) |
| 👤 จัดการผู้ใช้ | เพิ่ม / แก้ชื่อ / แก้ความชอบ (PREFERS) / ลบผู้ใช้ |
| 🕸️ Graph Explorer | วาดกราฟทั้งหมด หรือเฉพาะเส้นทางแนะนำของผู้ใช้ |
| ⚙️ Setup | สร้าง constraint + ข้อมูลตัวอย่าง, รีเซ็ตข้อมูล |

**เรื่องรูปภาพ:** รูปตัวอย่างอยู่ในโฟลเดอร์ `images/` (เก็บใน DB เป็น path เช่น `images/latex.png`)
รูปที่อัปโหลดจะถูกย่อแล้วเก็บเป็น data URI ใน Neo4j โดยตรง เพราะ Streamlit Cloud ไม่เก็บไฟล์ที่เขียนลงดิสก์ถาวร

## 3. โครงสร้างไฟล์

```text
├── app.py                  # หน้าเว็บ Streamlit
├── neo4j_service.py        # Cypher ทั้งหมด (CRUD + recommendation)
├── requirements.txt
├── images/                 # รูปที่นอน 10 ประเภท + default.png
├── cypher/                 # schema.cypher, recommendation.cypher
├── notebooks/              # notebook ต้นฉบับ
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## 4. รันในเครื่อง

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # แล้วใส่ค่าจริง
streamlit run app.py
```

เปิดเว็บแล้วไปหน้า **⚙️ Setup → สร้าง Constraint + ข้อมูลตัวอย่าง** หนึ่งครั้ง
(ถ้าเคยรัน notebook ไว้แล้ว ปุ่มนี้จะเติมรายละเอียดและรูปให้ Node ที่มีอยู่ ไม่สร้างซ้ำ)

## 5. Push ขึ้น GitHub

```bash
git init
git add .
git commit -m "Mattress recommender with Neo4j + Streamlit"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

ตรวจให้แน่ใจว่า `.streamlit/secrets.toml` **ไม่ถูก push** (อยู่ใน `.gitignore` แล้ว)

## 6. Deploy บน Streamlit Community Cloud

1. ไปที่ https://share.streamlit.io → **Create app** → เลือก repo, branch `main`, main file `app.py`
2. **Advanced settings → Secrets** วางค่า:
   ```toml
   [neo4j]
   uri = "neo4j+s://xxxxxxxx.databases.neo4j.io"
   username = "xxxxxxxx"
   password = "รหัสผ่านจริง"
   ```
3. กด Deploy แล้วไปหน้า ⚙️ Setup เพื่อสร้างข้อมูลตัวอย่าง

> Aura Free จะ pause อัตโนมัติถ้าไม่มีการใช้งานนาน ถ้าเว็บต่อไม่ติดให้เข้า console.neo4j.io แล้วกด Resume

## 7. Cypher ดูกราฟใน Neo4j Aura

```cypher
MATCH (u:User)-[r:PREFERS]->(m:MattressType) RETURN u, r, m
```
