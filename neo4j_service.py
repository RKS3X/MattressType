"""Neo4j data layer for the Mattress Type Recommender.

Graph model (from 045_MattressType_Neo4jAura.ipynb):

    (:User {name})-[:PREFERS]->(:MattressType {name, name_th, description,
                                               firmness, best_for, image})
"""
from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl
from neo4j.exceptions import ConstraintError


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def _config() -> tuple[str, str, str, str | None]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database") or None,  # None = ใช้ home database ของ Aura
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """Create one thread-safe Neo4j Driver for the Streamlit process."""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """Execute parameterized Cypher and return rows as dictionaries."""
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


# ---------------------------------------------------------------------------
# Schema + demo data
# ---------------------------------------------------------------------------
def create_schema() -> None:
    query(
        "CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
        write=True,
    )
    query(
        "CREATE CONSTRAINT mattress_type_name_unique IF NOT EXISTS "
        "FOR (m:MattressType) REQUIRE m.name IS UNIQUE",
        write=True,
    )


DEMO_USERS = ["Ben", "Jeff", "Mike", "Emma", "Daniel", "Alice", "Chris", "Sophia", "Liam", "Olivia"]

DEMO_MATTRESSES = [
    {
        "name": "Spring Mattress",
        "name_th": "ที่นอนสปริง",
        "description": "สปริงแบบเชื่อมต่อกัน (Bonnell) รองรับน้ำหนักได้ดี ระบายอากาศดี ราคาประหยัด",
        "firmness": 6,
        "best_for": "คนที่ชอบที่นอนเด้ง ระบายความร้อนดี",
        "image": "images/spring.png",
    },
    {
        "name": "Memory Foam Mattress",
        "name_th": "ที่นอนเมมโมรี่โฟม",
        "description": "โฟมยุบตัวตามสรีระ ช่วยกระจายแรงกด ลดการส่งแรงสั่นสะเทือนเมื่อคนข้าง ๆ ขยับ",
        "firmness": 4,
        "best_for": "คนนอนตะแคง ปวดไหล่หรือสะโพก",
        "image": "images/memory_foam.png",
    },
    {
        "name": "Latex Mattress",
        "name_th": "ที่นอนยางพารา",
        "description": "ยางพาราธรรมชาติ ยืดหยุ่นคืนตัวเร็ว มีรูระบายอากาศ ทนทาน",
        "firmness": 5,
        "best_for": "คนที่อยากได้ความนุ่มแต่คืนตัวไว",
        "image": "images/latex.png",
    },
    {
        "name": "Foam Mattress",
        "name_th": "ที่นอนโฟม",
        "description": "โฟมทั่วไปน้ำหนักเบา เคลื่อนย้ายง่าย ราคาเริ่มต้นไม่สูง",
        "firmness": 5,
        "best_for": "หอพัก ห้องเช่า งบจำกัด",
        "image": "images/foam.png",
    },
    {
        "name": "Pocket Spring Mattress",
        "name_th": "ที่นอนพ็อกเก็ตสปริง",
        "description": "สปริงแต่ละตัวอยู่ในถุงผ้าแยกกัน รองรับแบบจุดต่อจุด ไม่กระเทือนถึงคนข้าง ๆ",
        "firmness": 6,
        "best_for": "คู่รักที่นอนด้วยกัน",
        "image": "images/pocket_spring.png",
    },
    {
        "name": "Hybrid Mattress",
        "name_th": "ที่นอนไฮบริด",
        "description": "ผสมชั้นโฟม/ยางพาราด้านบนกับพ็อกเก็ตสปริงด้านล่าง ได้ทั้งความนุ่มและการรองรับ",
        "firmness": 6,
        "best_for": "คนที่อยากได้สมดุลระหว่างนุ่มกับแน่น",
        "image": "images/hybrid.png",
    },
    {
        "name": "Air Mattress",
        "name_th": "ที่นอนลม",
        "description": "ปรับความแน่นได้ด้วยการเติม/ปล่อยลม พับเก็บง่าย",
        "firmness": 3,
        "best_for": "แคมป์ปิ้ง แขกค้างคืน",
        "image": "images/air.png",
    },
    {
        "name": "Waterbed Mattress",
        "name_th": "ที่นอนน้ำ",
        "description": "ถุงบรรจุน้ำ ให้ความรู้สึกลอยตัว กระจายแรงกดสม่ำเสมอ",
        "firmness": 2,
        "best_for": "คนที่ชอบความรู้สึกลอยตัว",
        "image": "images/waterbed.png",
    },
    {
        "name": "Pillow Top Mattress",
        "name_th": "ที่นอนพิลโลว์ท็อป",
        "description": "มีชั้นบุนุ่มเย็บติดด้านบนเหมือนหมอน เพิ่มความนุ่มสบายให้ผิวสัมผัส",
        "firmness": 3,
        "best_for": "คนที่ชอบสัมผัสนุ่มฟูแบบโรงแรม",
        "image": "images/pillow_top.png",
    },
    {
        "name": "Orthopedic Mattress",
        "name_th": "ที่นอนเพื่อสุขภาพ (ออร์โธปิดิกส์)",
        "description": "ชั้นโฟมความหนาแน่นสูง แน่นและเรียบ ช่วยให้กระดูกสันหลังอยู่ในแนวตรง",
        "firmness": 8,
        "best_for": "คนปวดหลัง ผู้สูงอายุ",
        "image": "images/orthopedic.png",
    },
]

DEMO_PREFERENCES = [
    ("Ben", "Spring Mattress"), ("Ben", "Memory Foam Mattress"),
    ("Jeff", "Spring Mattress"), ("Jeff", "Memory Foam Mattress"), ("Jeff", "Foam Mattress"),
    ("Mike", "Spring Mattress"), ("Mike", "Latex Mattress"),
    ("Emma", "Foam Mattress"), ("Emma", "Pocket Spring Mattress"),
    ("Daniel", "Memory Foam Mattress"), ("Daniel", "Pocket Spring Mattress"),
    ("Alice", "Hybrid Mattress"), ("Alice", "Memory Foam Mattress"),
    ("Chris", "Air Mattress"), ("Chris", "Foam Mattress"),
    ("Sophia", "Waterbed Mattress"), ("Sophia", "Latex Mattress"),
    ("Liam", "Pillow Top Mattress"), ("Liam", "Spring Mattress"),
    ("Olivia", "Orthopedic Mattress"), ("Olivia", "Hybrid Mattress"),
]


def reset_mattress_graph() -> None:
    """ลบเฉพาะ Node User และ MattressType (ข้อมูล Label อื่นไม่ถูกลบ)"""
    query("MATCH (n) WHERE n:User OR n:MattressType DETACH DELETE n", write=True)


def seed_demo_data() -> None:
    """Idempotent: ใช้ MERGE จึงกดซ้ำได้ ไม่ทับข้อมูลที่ผู้ใช้แก้ไขไว้แล้ว"""
    create_schema()
    query("UNWIND $users AS n MERGE (:User {name: n})", {"users": DEMO_USERS}, write=True)
    query(
        """
        UNWIND $rows AS row
        MERGE (m:MattressType {name: row.name})
        ON CREATE SET m.name_th = row.name_th,
                      m.description = row.description,
                      m.firmness = row.firmness,
                      m.best_for = row.best_for,
                      m.image = row.image
        // ถ้ามี Node อยู่แล้ว (เช่นสร้างจาก Colab) แต่ยังไม่มีรายละเอียด ให้เติมให้
        SET m.name_th = coalesce(m.name_th, row.name_th),
            m.description = coalesce(m.description, row.description),
            m.firmness = coalesce(m.firmness, row.firmness),
            m.best_for = coalesce(m.best_for, row.best_for),
            m.image = coalesce(m.image, row.image)
        """,
        {"rows": DEMO_MATTRESSES},
        write=True,
    )
    query(
        """
        UNWIND $prefs AS p
        MATCH (u:User {name: p[0]}), (m:MattressType {name: p[1]})
        MERGE (u)-[:PREFERS]->(m)
        """,
        {"prefs": [list(p) for p in DEMO_PREFERENCES]},
        write=True,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def get_metrics() -> dict[str, int]:
    rows = query(
        """
        RETURN COUNT { (:User) } AS users,
               COUNT { (:MattressType) } AS mattresses,
               COUNT { (:User)-[:PREFERS]->(:MattressType) } AS prefers
        """
    )
    return rows[0] if rows else {"users": 0, "mattresses": 0, "prefers": 0}


def popular_mattresses() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (m:MattressType)
        OPTIONAL MATCH (u:User)-[:PREFERS]->(m)
        RETURN m.name AS mattress_type, count(u) AS total_users
        ORDER BY total_users DESC, mattress_type
        """
    )


# ---------------------------------------------------------------------------
# MattressType CRUD
# ---------------------------------------------------------------------------
_MATTRESS_FIELDS = """
    m.name AS name, m.name_th AS name_th, m.description AS description,
    m.firmness AS firmness, m.best_for AS best_for, m.image AS image
"""


def list_mattresses() -> list[dict[str, Any]]:
    return query(
        f"""
        MATCH (m:MattressType)
        OPTIONAL MATCH (u:User)-[:PREFERS]->(m)
        RETURN {_MATTRESS_FIELDS}, count(u) AS fans
        ORDER BY name
        """
    )


def get_mattress(name: str) -> dict[str, Any] | None:
    rows = query(f"MATCH (m:MattressType {{name:$name}}) RETURN {_MATTRESS_FIELDS}", {"name": name})
    return rows[0] if rows else None


def mattress_exists(name: str) -> bool:
    return bool(query("MATCH (m:MattressType {name:$name}) RETURN m.name AS n", {"name": name}))


def add_mattress(data: dict[str, Any]) -> None:
    if mattress_exists(data["name"]):
        raise ValueError(f"มีที่นอนชื่อ '{data['name']}' อยู่แล้ว")
    try:
        query(
            """
            CREATE (m:MattressType {name:$name})
            SET m.name_th = $name_th, m.description = $description,
                m.firmness = $firmness, m.best_for = $best_for, m.image = $image
            """,
            data,
            write=True,
        )
    except ConstraintError as exc:
        raise ValueError(f"มีที่นอนชื่อ '{data['name']}' อยู่แล้ว") from exc


def update_mattress(old_name: str, data: dict[str, Any]) -> None:
    if data["name"] != old_name and mattress_exists(data["name"]):
        raise ValueError(f"มีที่นอนชื่อ '{data['name']}' อยู่แล้ว")
    try:
        rows = query(
            """
            MATCH (m:MattressType {name:$old_name})
            SET m.name = $name, m.name_th = $name_th, m.description = $description,
                m.firmness = $firmness, m.best_for = $best_for, m.image = $image
            RETURN m.name AS name
            """,
            {**data, "old_name": old_name},
            write=True,
        )
    except ConstraintError as exc:
        raise ValueError(f"มีที่นอนชื่อ '{data['name']}' อยู่แล้ว") from exc
    if not rows:
        raise ValueError(f"ไม่พบที่นอน '{old_name}'")


def delete_mattress(name: str) -> None:
    query("MATCH (m:MattressType {name:$name}) DETACH DELETE m", {"name": name}, write=True)


# ---------------------------------------------------------------------------
# User CRUD + preferences
# ---------------------------------------------------------------------------
def list_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)
        OPTIONAL MATCH (u)-[:PREFERS]->(m:MattressType)
        WITH u, m ORDER BY m.name
        RETURN u.name AS name, collect(m.name) AS prefers
        ORDER BY name
        """
    )


def user_exists(name: str) -> bool:
    return bool(query("MATCH (u:User {name:$name}) RETURN u.name AS n", {"name": name}))


def add_user(name: str, prefers: list[str] | None = None) -> None:
    if user_exists(name):
        raise ValueError(f"มีผู้ใช้ชื่อ '{name}' อยู่แล้ว")
    try:
        query("CREATE (:User {name:$name})", {"name": name}, write=True)
    except ConstraintError as exc:
        raise ValueError(f"มีผู้ใช้ชื่อ '{name}' อยู่แล้ว") from exc
    if prefers:
        set_preferences(name, prefers)


def rename_user(old_name: str, new_name: str) -> None:
    if old_name == new_name:
        return
    if user_exists(new_name):
        raise ValueError(f"มีผู้ใช้ชื่อ '{new_name}' อยู่แล้ว")
    try:
        query("MATCH (u:User {name:$old}) SET u.name = $new", {"old": old_name, "new": new_name}, write=True)
    except ConstraintError as exc:
        raise ValueError(f"มีผู้ใช้ชื่อ '{new_name}' อยู่แล้ว") from exc


def delete_user(name: str) -> None:
    query("MATCH (u:User {name:$name}) DETACH DELETE u", {"name": name}, write=True)


def user_preferences(name: str) -> list[str]:
    rows = query(
        "MATCH (:User {name:$name})-[:PREFERS]->(m:MattressType) RETURN m.name AS name ORDER BY name",
        {"name": name},
    )
    return [r["name"] for r in rows]


def set_preferences(user: str, mattress_names: list[str]) -> None:
    """แทนที่ความชอบทั้งหมดของผู้ใช้ด้วยรายการใหม่"""
    query(
        """
        MATCH (u:User {name:$user})
        OPTIONAL MATCH (u)-[r:PREFERS]->(m:MattressType)
        WHERE NOT m.name IN $names
        DELETE r
        WITH DISTINCT u
        UNWIND $names AS n
        MATCH (m:MattressType {name:n})
        MERGE (u)-[:PREFERS]->(m)
        """,
        {"user": user, "names": mattress_names},
        write=True,
    )


def add_preference(user: str, mattress: str) -> None:
    query(
        "MATCH (u:User {name:$u}), (m:MattressType {name:$m}) MERGE (u)-[:PREFERS]->(m)",
        {"u": user, "m": mattress},
        write=True,
    )


def remove_preference(user: str, mattress: str) -> None:
    query(
        "MATCH (:User {name:$u})-[r:PREFERS]->(:MattressType {name:$m}) DELETE r",
        {"u": user, "m": mattress},
        write=True,
    )


# ---------------------------------------------------------------------------
# Recommendation (Collaborative filtering บน Graph เหมือนใน notebook)
# ---------------------------------------------------------------------------
def recommend_mattresses(user: str, limit: int = 6) -> list[dict[str, Any]]:
    """
    me -PREFERS-> m <-PREFERS- other -PREFERS-> rec  (rec ที่ me ยังไม่ได้ชอบ)
    score = จำนวนเส้นทางที่พาไปถึง rec
    """
    return query(
        f"""
        MATCH (me:User {{name:$user}})-[:PREFERS]->(shared:MattressType)
              <-[:PREFERS]-(other:User)-[:PREFERS]->(m:MattressType)
        WHERE other <> me AND NOT EXISTS {{ MATCH (me)-[:PREFERS]->(m) }}
        WITH m, count(*) AS score,
             collect(DISTINCT other.name) AS recommended_by,
             collect(DISTINCT shared.name) AS because_of
        RETURN {_MATTRESS_FIELDS}, score, recommended_by, because_of
        ORDER BY score DESC, name
        LIMIT $limit
        """,
        {"user": user, "limit": limit},
    )


def popular_not_preferred(user: str, limit: int = 6) -> list[dict[str, Any]]:
    """Fallback (cold start): ที่นอนยอดนิยมที่ผู้ใช้ยังไม่ได้เลือก"""
    return query(
        f"""
        MATCH (m:MattressType)
        WHERE NOT EXISTS {{ MATCH (:User {{name:$user}})-[:PREFERS]->(m) }}
        OPTIONAL MATCH (u:User)-[:PREFERS]->(m)
        WITH m, count(u) AS fans
        RETURN {_MATTRESS_FIELDS}, fans
        ORDER BY fans DESC, name
        LIMIT $limit
        """,
        {"user": user, "limit": limit},
    )


def graph_edges(user: str | None = None) -> list[dict[str, str]]:
    """ดึง edge PREFERS ทั้งหมด หรือเฉพาะเส้นทางแนะนำ 3 hop ของผู้ใช้"""
    if not user:
        return query(
            "MATCH (u:User)-[:PREFERS]->(m:MattressType) RETURN u.name AS user, m.name AS mattress ORDER BY user, mattress"
        )
    return query(
        """
        MATCH (me:User {name:$user})
        OPTIONAL MATCH (me)-[:PREFERS]->(m1:MattressType)
        OPTIONAL MATCH (m1)<-[:PREFERS]-(o:User)
        OPTIONAL MATCH (o)-[:PREFERS]->(m2:MattressType)
        WITH collect(DISTINCT {user: me.name, mattress: m1.name})
           + collect(DISTINCT {user: o.name, mattress: m1.name})
           + collect(DISTINCT {user: o.name, mattress: m2.name}) AS edges
        UNWIND edges AS e
        WITH DISTINCT e WHERE e.user IS NOT NULL AND e.mattress IS NOT NULL
        RETURN e.user AS user, e.mattress AS mattress
        ORDER BY user, mattress
        """,
        {"user": user},
    )
