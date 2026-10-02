from __future__ import annotations

import base64
import io
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

import neo4j_service as db

APP_DIR = Path(__file__).parent
IMAGE_DIR = APP_DIR / "images"
DEFAULT_IMAGE = "images/default.png"

st.set_page_config(
    page_title="MattressGraph Recommender",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #1e1b4b 0%, #312e81 55%, #0e7490 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.1rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .pill {
        display:inline-block; padding:.18rem .6rem; border-radius:999px;
        background:#0e7490; color:white; font-size:.78rem; font-weight:700; margin-right:.3rem;
      }
      .pill.gray {background:#64748b;}
      .muted {opacity:.72; font-size:.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def flash(msg: str) -> None:
    """เก็บข้อความไว้แสดงหลัง st.rerun()"""
    st.session_state["_flash"] = msg


def show_flash() -> None:
    msg = st.session_state.pop("_flash", None)
    if msg:
        st.toast(msg, icon="✅")


def resolve_image(src: str | None):
    """คืนค่าที่ st.image ใช้ได้: path ในโปรเจกต์, URL หรือ bytes จาก data URI"""
    src = (src or "").strip()
    if src.startswith("data:image"):
        try:
            return base64.b64decode(src.split(",", 1)[1])
        except Exception:
            return str(APP_DIR / DEFAULT_IMAGE)
    if src.startswith(("http://", "https://")):
        return src
    if src and (APP_DIR / src).is_file():
        return str(APP_DIR / src)
    return str(APP_DIR / DEFAULT_IMAGE)


def upload_to_data_uri(file) -> str:
    """ย่อรูปที่อัปโหลดแล้วเก็บเป็น data URI ใน Neo4j
    (Streamlit Cloud ไม่เก็บไฟล์ที่เขียนลงดิสก์ถาวร จึงเก็บในฐานข้อมูลแทน)"""
    img = Image.open(file)
    img = img.convert("RGB")
    img.thumbnail((800, 600))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def bundled_images() -> list[str]:
    return sorted(f"images/{p.name}" for p in IMAGE_DIR.glob("*.png"))


def firmness_bar(value) -> str:
    try:
        v = max(0, min(10, int(value)))
    except (TypeError, ValueError):
        return "ไม่ระบุ"
    return "●" * v + "○" * (10 - v) + f"  {v}/10"


def mattress_card(m: dict, *, header_html: str = "", footer: str = "", key: str = "", like_user: str | None = None):
    with st.container(border=True):
        st.image(resolve_image(m.get("image")), width="stretch")
        if header_html:
            st.markdown(header_html, unsafe_allow_html=True)
        st.markdown(f"#### {m['name']}")
        if m.get("name_th"):
            st.caption(m["name_th"])
        st.markdown(f"**ความแน่น:** `{firmness_bar(m.get('firmness'))}`")
        if m.get("description"):
            st.write(m["description"])
        if m.get("best_for"):
            st.markdown(f"<span class='muted'>👍 เหมาะกับ: {m['best_for']}</span>", unsafe_allow_html=True)
        if footer:
            st.markdown(footer, unsafe_allow_html=True)
        if like_user:
            if st.button("❤️ เพิ่มเป็นที่นอนที่ชอบ", key=f"like_{key}_{m['name']}", width="stretch"):
                db.add_preference(like_user, m["name"])
                flash(f"{like_user} ชอบ {m['name']} แล้ว")
                st.rerun()


def card_grid(items: list[dict], cols: int = 3, **kwargs):
    for start in range(0, len(items), cols):
        columns = st.columns(cols)
        for col, item in zip(columns, items[start : start + cols]):
            with col:
                extra = kwargs.get("render_extra")
                if extra:
                    header, footer = extra(item)
                    mattress_card(item, header_html=header, footer=footer, key=kwargs.get("key", ""),
                                  like_user=kwargs.get("like_user"))
                else:
                    mattress_card(item, key=kwargs.get("key", ""), like_user=kwargs.get("like_user"))


def image_picker(prefix: str, current: str | None = None) -> str | None:
    """Widget เลือกรูป: คืนค่า string ที่จะเก็บใน property `image`"""
    options = ["รูปตัวอย่างในระบบ", "อัปโหลดรูป", "ลิงก์รูป (URL)"]
    if current:
        options.insert(0, "ใช้รูปเดิม")
    mode = st.radio("รูปภาพที่นอน", options, horizontal=True, key=f"{prefix}_img_mode")
    value = current
    if mode == "รูปตัวอย่างในระบบ":
        imgs = bundled_images()
        idx = imgs.index(current) if current in imgs else (imgs.index(DEFAULT_IMAGE) if DEFAULT_IMAGE in imgs else 0)
        value = st.selectbox("เลือกรูป", imgs, index=idx, key=f"{prefix}_img_bundled",
                             format_func=lambda p: Path(p).stem.replace("_", " ").title())
    elif mode == "อัปโหลดรูป":
        file = st.file_uploader("ไฟล์รูป (PNG/JPG/WEBP)", type=["png", "jpg", "jpeg", "webp"], key=f"{prefix}_img_file")
        value = upload_to_data_uri(file) if file else None
    elif mode == "ลิงก์รูป (URL)":
        url = st.text_input("URL รูปภาพ", value=current if (current or "").startswith("http") else "",
                            placeholder="https://...", key=f"{prefix}_img_url")
        value = url.strip() or None
    if value:
        st.image(resolve_image(value), caption="ตัวอย่างรูป", width=320)
    return value


def mattress_form(prefix: str, m: dict | None = None) -> dict:
    m = m or {}
    c1, c2 = st.columns(2)
    name = c1.text_input("ชื่อประเภทที่นอน (English, ห้ามซ้ำ) *", value=m.get("name", ""), key=f"{prefix}_name")
    name_th = c2.text_input("ชื่อภาษาไทย", value=m.get("name_th") or "", key=f"{prefix}_name_th")
    description = st.text_area("คำอธิบาย", value=m.get("description") or "", key=f"{prefix}_desc")
    c3, c4 = st.columns([1, 2])
    firmness = c3.slider("ความแน่น (1 = นุ่มมาก, 10 = แน่นมาก)", 1, 10, int(m.get("firmness") or 5), key=f"{prefix}_firm")
    best_for = c4.text_input("เหมาะกับใคร", value=m.get("best_for") or "", key=f"{prefix}_best")
    image = image_picker(prefix, m.get("image"))
    return {
        "name": name.strip(),
        "name_th": name_th.strip() or None,
        "description": description.strip() or None,
        "firmness": int(firmness),
        "best_for": best_for.strip() or None,
        "image": image or DEFAULT_IMAGE,
    }


def user_selector(key: str) -> str:
    users = [u["name"] for u in db.list_users()]
    if not users:
        st.info("ยังไม่มีผู้ใช้ กรุณาไปหน้า ⚙️ Setup เพื่อสร้างข้อมูลตัวอย่าง หรือเพิ่มผู้ใช้ในหน้า 👤 จัดการผู้ใช้")
        st.stop()
    return st.selectbox("เลือกผู้ใช้", users, key=key)


def require_connection() -> None:
    try:
        if not db.ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "YOUR_USERNAME"\npassword = "YOUR_PASSWORD"\n# database = "YOUR_DB"  # ไม่ใส่ก็ได้',
            language="toml",
        )
        st.caption("นำค่าด้านบนไปใส่ใน Streamlit Secrets (หรือ .streamlit/secrets.toml ในเครื่อง) ห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
require_connection()
show_flash()

with st.sidebar:
    st.markdown("## 🛏️ MattressGraph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["🏠 หน้าหลัก", "✨ แนะนำที่นอน", "🛏️ จัดการที่นอน", "👤 จัดการผู้ใช้", "🕸️ Graph Explorer", "⚙️ Setup"],
    )
    st.divider()
    st.caption("(User)-[:PREFERS]->(MattressType)")

st.markdown(
    """
    <div class="hero">
      <h1>🛏️ Mattress Type Recommender</h1>
      <p>ระบบแนะนำประเภทที่นอนด้วย Graph Database — ดูว่าคนที่ชอบที่นอนแบบเดียวกับคุณ ชอบที่นอนแบบไหนอีก</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
if page == "🏠 หน้าหลัก":
    m = db.get_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("👤 Users", m.get("users", 0))
    c2.metric("🛏️ Mattress Types", m.get("mattresses", 0))
    c3.metric("❤️ PREFERS", m.get("prefers", 0))

    pop = db.popular_mattresses()
    if pop:
        st.subheader("📊 ประเภทที่นอนยอดนิยม")
        st.bar_chart(pd.DataFrame(pop), x="mattress_type", y="total_users", horizontal=True,
                     sort="-total_users", x_label="ประเภทที่นอน", y_label="จำนวนผู้ใช้", height=360)

    st.subheader("🖼️ ประเภทที่นอนทั้งหมด")
    items = db.list_mattresses()
    if not items:
        st.info("ยังไม่มีข้อมูลที่นอน ไปที่ ⚙️ Setup เพื่อสร้างข้อมูลตัวอย่าง")
    else:
        keyword = st.text_input("ค้นหา", placeholder="เช่น foam, สปริง, ปวดหลัง")
        if keyword:
            k = keyword.lower()
            items = [x for x in items if any(k in str(x.get(f) or "").lower()
                                             for f in ("name", "name_th", "description", "best_for"))]
        card_grid(
            items,
            render_extra=lambda x: ("", f"<span class='pill gray'>❤️ {x['fans']} คนชอบ</span>"),
            key="home",
        )

# ---------------------------------------------------------------------------
elif page == "✨ แนะนำที่นอน":
    user = user_selector("rec_user")
  

    liked = [db.get_mattress(n) for n in db.user_preferences(user)]
    liked = [x for x in liked if x]
    st.subheader(f"❤️ ที่นอนที่ {user} ชอบ")
    if liked:
        card_grid(liked, cols=4, key="liked")
    else:
        st.info(f"{user} ยังไม่ได้เลือกที่นอนที่ชอบ — เพิ่มได้ที่หน้า 👤 จัดการผู้ใช้ หรือกด ❤️ จากคำแนะนำด้านล่าง")

    st.subheader(f"✨ ที่นอนที่แนะนำให้ {user}")
    recs = db.recommend_mattresses(user, top_n)
    st.caption("score = จำนวนเส้นทาง User → ที่นอนที่ชอบ ← ผู้ใช้อื่น → ที่นอนอื่น (ยิ่งมีเส้นทางมาก ยิ่งน่าสนใจ)")
    if recs:
        card_grid(
            recs,
            render_extra=lambda r: (
                f"<span class='pill'>#{recs.index(r) + 1} · score {r['score']}</span>",
                f"<p class='muted'>💡 เพราะคุณชอบ <b>{', '.join(r['because_of'])}</b> "
                f"เหมือนกับ <b>{', '.join(r['recommended_by'])}</b></p>",
            ),
            key="rec",
            like_user=user,
        )
    else:
        fallback = db.popular_not_preferred(user, top_n)
        st.warning("ยังหาผู้ใช้ที่ชอบที่นอนคล้ายกันไม่พบ จึงแสดงที่นอนยอดนิยมแทน (cold start)")
        card_grid(
            fallback,
            render_extra=lambda r: ("<span class='pill gray'>ยอดนิยม</span>", f"<p class='muted'>❤️ {r['fans']} คนชอบ</p>"),
            key="pop",
            like_user=user,
        )

# ---------------------------------------------------------------------------
elif page == "🛏️ จัดการที่นอน":
    tab_list, tab_add, tab_edit, tab_del = st.tabs(["📋 รายการ", "➕ เพิ่ม", "✏️ แก้ไข", "🗑️ ลบ"])
    items = db.list_mattresses()
    names = [x["name"] for x in items]

    with tab_list:
        if items:
            df = pd.DataFrame(items)
            df["image"] = df["image"].apply(lambda s: "(รูปที่อัปโหลด)" if str(s or "").startswith("data:") else s)
            st.dataframe(
                df[["name", "name_th", "firmness", "best_for", "fans", "image", "description"]],
                hide_index=True,
                column_config={
                    "name": "ชื่อ", "name_th": "ชื่อไทย", "best_for": "เหมาะกับ", "description": "คำอธิบาย",
                    "fans": st.column_config.NumberColumn("คนชอบ"),
                    "firmness": st.column_config.ProgressColumn("ความแน่น", min_value=0, max_value=10, format="%d"),
                    "image": "รูป",
                },
            )
        else:
            st.info("ยังไม่มีข้อมูลที่นอน")

    with tab_add:
        data = mattress_form("add")
        if st.button("➕ เพิ่มที่นอน", type="primary", width="stretch", key="add_btn"):
            if not data["name"]:
                st.error("กรุณากรอกชื่อประเภทที่นอน")
            else:
                try:
                    db.add_mattress(data)
                    flash(f"เพิ่ม {data['name']} แล้ว")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with tab_edit:
        if not names:
            st.info("ยังไม่มีที่นอนให้แก้ไข")
        else:
            if "_next_edit_sel" in st.session_state:
                st.session_state["edit_sel"] = st.session_state.pop("_next_edit_sel")
            sel = st.selectbox("เลือกที่นอนที่จะแก้ไข", names, key="edit_sel")
            current = db.get_mattress(sel)
            # key ผูกกับชื่อที่เลือก เพื่อให้ฟอร์มโหลดค่าใหม่เมื่อเปลี่ยนรายการ
            data = mattress_form(f"edit_{sel}", current)
            if st.button("💾 บันทึกการแก้ไข", type="primary", width="stretch", key="edit_btn"):
                if not data["name"]:
                    st.error("ชื่อห้ามว่าง")
                else:
                    try:
                        db.update_mattress(sel, data)
                        st.session_state["_next_edit_sel"] = data["name"]
                        flash(f"บันทึก {data['name']} แล้ว")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    with tab_del:
        if not names:
            st.info("ยังไม่มีที่นอนให้ลบ")
        else:
            sel = st.selectbox("เลือกที่นอนที่จะลบ", names, key="del_sel")
            target = next(x for x in items if x["name"] == sel)
            c1, c2 = st.columns([1, 2])
            c1.image(resolve_image(target.get("image")), width="stretch")
            c2.warning(f"การลบ **{sel}** จะลบความสัมพันธ์ PREFERS ทั้งหมด {target['fans']} เส้นด้วย (DETACH DELETE)")
            confirm = c2.checkbox("ยืนยันการลบ", key=f"del_confirm_{sel}")
            if c2.button("🗑️ ลบที่นอน", type="primary", disabled=not confirm, key="del_btn"):
                db.delete_mattress(sel)
                flash(f"ลบ {sel} แล้ว")
                st.rerun()

# ---------------------------------------------------------------------------
elif page == "👤 จัดการผู้ใช้":
    users = db.list_users()
    user_names = [u["name"] for u in users]
    all_mattresses = [x["name"] for x in db.list_mattresses()]
    tab_list, tab_add, tab_edit, tab_del = st.tabs(["📋 รายการ", "➕ เพิ่ม", "✏️ แก้ไข / ความชอบ", "🗑️ ลบ"])

    with tab_list:
        if users:
            df = pd.DataFrame(users)
            df["prefers"] = df["prefers"].apply(", ".join)
            st.dataframe(df, hide_index=True, column_config={"name": "ผู้ใช้", "prefers": "ที่นอนที่ชอบ (PREFERS)"})
        else:
            st.info("ยังไม่มีผู้ใช้")

    with tab_add:
        new_name = st.text_input("ชื่อผู้ใช้ (ห้ามซ้ำ) *", key="add_user_name")
        prefs = st.multiselect("ที่นอนที่ชอบ", all_mattresses, key="add_user_prefs")
        if st.button("➕ เพิ่มผู้ใช้", type="primary", width="stretch", key="add_user_btn"):
            if not new_name.strip():
                st.error("กรุณากรอกชื่อผู้ใช้")
            else:
                try:
                    db.add_user(new_name.strip(), prefs)
                    flash(f"เพิ่มผู้ใช้ {new_name.strip()} แล้ว")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with tab_edit:
        if not user_names:
            st.info("ยังไม่มีผู้ใช้")
        else:
            if "_next_edit_user_sel" in st.session_state:
                st.session_state["edit_user_sel"] = st.session_state.pop("_next_edit_user_sel")
            sel = st.selectbox("เลือกผู้ใช้", user_names, key="edit_user_sel")
            current_prefs = next(u["prefers"] for u in users if u["name"] == sel)
            renamed = st.text_input("ชื่อผู้ใช้", value=sel, key=f"edit_user_name_{sel}")
            prefs = st.multiselect("ที่นอนที่ชอบ", all_mattresses, default=current_prefs, key=f"edit_user_prefs_{sel}")
            if st.button("💾 บันทึก", type="primary", width="stretch", key="edit_user_btn"):
                new = renamed.strip()
                if not new:
                    st.error("ชื่อห้ามว่าง")
                else:
                    try:
                        db.rename_user(sel, new)
                        db.set_preferences(new, prefs)
                        st.session_state["_next_edit_user_sel"] = new
                        flash(f"บันทึกผู้ใช้ {new} แล้ว")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    with tab_del:
        if not user_names:
            st.info("ยังไม่มีผู้ใช้")
        else:
            sel = st.selectbox("เลือกผู้ใช้ที่จะลบ", user_names, key="del_user_sel")
            st.warning(f"การลบ **{sel}** จะลบความสัมพันธ์ PREFERS ของผู้ใช้นี้ทั้งหมดด้วย")
            confirm = st.checkbox("ยืนยันการลบ", key=f"del_user_confirm_{sel}")
            if st.button("🗑️ ลบผู้ใช้", type="primary", disabled=not confirm, key="del_user_btn"):
                db.delete_user(sel)
                flash(f"ลบผู้ใช้ {sel} แล้ว")
                st.rerun()

# ---------------------------------------------------------------------------
elif page == "🕸️ Graph Explorer":
    mode = st.radio("แสดง", ["ทั้งกราฟ", "เส้นทางแนะนำของผู้ใช้"], horizontal=True)
    focus = user_selector("graph_user") if mode == "เส้นทางแนะนำของผู้ใช้" else None
    edges = db.graph_edges(focus)
    if not edges:
        st.info("ยังไม่มีความสัมพันธ์ PREFERS")
    else:
        def q(s: str) -> str:
            return '"' + str(s).replace('"', "'") + '"'

        dot = ["graph G {", 'rankdir="LR";', "node [fontname=Helvetica, fontsize=11];"]
        users_in = sorted({e["user"] for e in edges})
        mats_in = sorted({e["mattress"] for e in edges})
        for u in users_in:
            color = "#f59e0b" if u == focus else "#bae6fd"
            dot.append(f'{q("U:" + u)} [label={q(u)}, shape=ellipse, style=filled, fillcolor="{color}"];')
        for m in mats_in:
            dot.append(f'{q("M:" + m)} [label={q(m)}, shape=box, style="rounded,filled", fillcolor="#bbf7d0"];')
        for e in edges:
            dot.append(f'{q("U:" + e["user"])} -- {q("M:" + e["mattress"])};')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), width="stretch")
        st.caption("🔵 User   🟢 MattressType" + ("   🟠 ผู้ใช้ที่เลือก" if focus else ""))
        with st.expander("ดูข้อมูล edge"):
            st.dataframe(pd.DataFrame(edges), hide_index=True)
        with st.expander("Cypher สำหรับดูใน Neo4j Aura"):
            st.code("MATCH (u:User)-[r:PREFERS]->(m:MattressType)\nRETURN u, r, m", language="cypher")

# ---------------------------------------------------------------------------
elif page == "⚙️ Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.markdown(
        """
        **Graph schema**
        - `(:User {name})`
        - `(:MattressType {name, name_th, description, firmness, best_for, image})`
        - `(:User)-[:PREFERS]->(:MattressType)`
        """
    )
    if st.button("🌱 สร้าง Constraint + ข้อมูลตัวอย่าง (MERGE — กดซ้ำได้)", type="primary", width="stretch"):
        with st.spinner("กำลังสร้างข้อมูล..."):
            db.seed_demo_data()
        flash("สร้างข้อมูลตัวอย่างแล้ว")
        st.rerun()

    st.divider()
    st.markdown("#### 🔄 รีเซ็ตข้อมูล")
    st.caption("ลบเฉพาะ Node `User` และ `MattressType` แล้วสร้างข้อมูลตัวอย่างใหม่ (ข้อมูล Label อื่นไม่ถูกลบ)")
    confirm = st.checkbox("ฉันเข้าใจว่าข้อมูลที่เพิ่ม/แก้ไขไว้จะหายทั้งหมด")
    if st.button("🔄 รีเซ็ต + สร้างใหม่", disabled=not confirm):
        with st.spinner("กำลังรีเซ็ต..."):
            db.reset_mattress_graph()
            db.seed_demo_data()
        flash("รีเซ็ตข้อมูลเรียบร้อย")
        st.rerun()
