"""한 회차의 메뉴와 집계. 이름, 학번, 개인 대진 결과는 보관하지 않는다."""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT = ("버섯잡채", "떡갈비", "오이상추무침", "만두탕수", "시금치나물", "가자미순살튀김", "온두부김치볶음", "부추해물전")
DATA = Path.home() / "lunch-record"
SCHEMA = """
CREATE TABLE IF NOT EXISTS room(id INTEGER PRIMARY KEY CHECK(id=1), round_id TEXT, phase TEXT, salt BLOB, observed INTEGER, source TEXT);
CREATE TABLE IF NOT EXISTS menus(name TEXT PRIMARY KEY, pos INTEGER UNIQUE, days INTEGER, hearts INTEGER DEFAULT 0, wins INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS admissions(digest TEXT PRIMARY KEY) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS portions(receipt TEXT PRIMARY KEY, mode TEXT NOT NULL, choice TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS tickets(digest TEXT PRIMARY KEY, used INTEGER DEFAULT 0) WITHOUT ROWID;
"""


@contextmanager
def connection():
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    conn = sqlite3.connect(DATA / "classroom.sqlite3", timeout=8)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA secure_delete=ON")
        conn.executescript(SCHEMA)
        conn.execute("BEGIN IMMEDIATE")
        if not conn.execute("SELECT 1 FROM room").fetchone():
            initialize(conn, DEFAULT, {}, "수업 예시 후보")
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize(db, names, days, source):
    if not 2 <= len(names) <= 8 or len(set(names)) != len(names):
        raise ValueError("서로 다른 메뉴를 2~8개 골라 주세요.")
    for table in ("admissions", "tickets", "portions", "menus", "room"):
        db.execute(f"DELETE FROM {table}")
    db.execute("INSERT INTO room VALUES(1,?,'heart',?,NULL,?)",
               (secrets.token_hex(12), secrets.token_bytes(32), source))
    db.executemany("INSERT INTO menus(name,pos,days) VALUES(?,?,?)",
                   [(name, i, days.get(name)) for i, name in enumerate(names)])


def check(db, rid, phases=None):
    row = db.execute("SELECT * FROM room").fetchone()
    if rid != row["round_id"]:
        raise ValueError("새 회차가 시작됐어요. 화면을 새로 열어 주세요.")
    if phases and row["phase"] not in phases:
        raise ValueError("지금은 이 투표를 받지 않아요. 회차 상태를 확인해 주세요.")
    return row


def new_round(rid, names, days, source):
    with connection() as db:
        check(db, rid)
        initialize(db, names, days, source)


def snapshot():
    with connection() as db:
        r = db.execute("SELECT round_id,phase,observed,source FROM room").fetchone()
        rows = [dict(m) for m in db.execute("SELECT name,days,hearts,wins FROM menus ORDER BY pos")]
        finished = sum(m["wins"] for m in rows)
        public = r["phase"] == "closed" and finished >= 5
        if not public:
            for m in rows:
                m["wins"] = None
        return dict(r) | {"menus": rows, "finished": finished, "public": public}


def add_heart(rid, name):
    with connection() as db:
        check(db, rid, {"heart"})
        if not db.execute("UPDATE menus SET hearts=hearts+1 WHERE name=?", (name,)).rowcount:
            raise ValueError("이번 회차의 메뉴를 다시 고르세요.")


def digest(salt, prefix, value):
    return hmac.new(salt, (prefix + value).encode(), hashlib.sha256).hexdigest()


def open_cup(rid, observed, count):
    if not 1 <= count <= 200 or not 0 <= observed <= 200:
        raise ValueError("관찰 인원은 0~200명, 참가권은 1~200장까지 준비할 수 있어요.")
    with connection() as db:
        room = check(db, rid, {"heart"})
        codes = set()
        while len(codes) < count:
            codes.add(secrets.token_hex(4).upper())
        db.executemany("INSERT INTO tickets(digest) VALUES(?)",
                       [(digest(room["salt"], "ticket", c),) for c in codes])
        db.execute("UPDATE room SET observed=?,phase='cup'", (observed,))
        return sorted(codes)


def admit(rid, student_id, name):
    student_id = student_id.strip()
    if not re.fullmatch(r"[0-9]{3,12}", student_id) or not name.strip():
        raise ValueError("학번은 숫자 3~12자리로 쓰고 이름도 입력하세요.")
    with connection() as db:
        room = check(db, rid, {"cup"})
        used = db.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
        if used >= db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]:
            raise ValueError("준비한 참가권이 모두 배부됐어요.")
        key = digest(room["salt"], "student", student_id)
        if not db.execute("INSERT OR IGNORE INTO admissions VALUES(?)", (key,)).rowcount:
            raise ValueError("이미 접수한 학번이에요. 두 번째 참가권은 건네지 마세요.")


def ticket_key(db, rid, raw):
    room = check(db, rid, {"cup"})
    key = digest(room["salt"], "ticket", raw.strip().upper())
    row = db.execute("SELECT used FROM tickets WHERE digest=?", (key,)).fetchone()
    if not row or row[0]:
        raise ValueError("참가권을 확인하세요. 이미 완주한 표는 다시 쓸 수 없어요.")
    return key


def enter(rid, code):
    with connection() as db:
        ticket_key(db, rid, code)


def finish(rid, code, winner):
    with connection() as db:
        key = ticket_key(db, rid, code)
        if not db.execute("UPDATE menus SET wins=wins+1 WHERE name=?", (winner,)).rowcount:
            raise ValueError("이번 회차의 후보가 아니에요.")
        db.execute("UPDATE tickets SET used=1 WHERE digest=?", (key,))


def close_cup(rid):
    with connection() as db:
        check(db, rid, {"cup"})
        db.execute("UPDATE room SET phase='closed'")


def next_round(game, menu):
    pair = game["round"][game["index"]:game["index"] + 2]
    if menu not in pair or len(pair) != 2:
        raise ValueError("화면에 보이는 두 메뉴 중 하나를 고르세요.")
    winners = game["winners"]
    winners.append(menu)
    game["index"] += 2
    game["matches"] += 1
    if game["index"] == len(game["round"]) - 1:
        winners.append(game["round"][-1])
        game["index"] += 1
    if game["index"] == len(game["round"]):
        if len(winners) == 1:
            return winners[0]
        game.update(round=winners, winners=[], index=0)
    return None


def save_portion(rid, receipt, mode, choice):
    if mode not in ("직접 담기", "배식받기") or choice not in ("조금", "보통", "건너뛰기"):
        raise ValueError("배식 방식과 원하는 양을 골라 주세요.")
    with connection() as db:
        check(db, rid)
        result = db.execute(
            "INSERT OR IGNORE INTO portions(receipt, mode, choice) VALUES (?, ?, ?)",
            (receipt, mode, choice),
        )
        return result.rowcount == 1


def portion_summary(rid):
    with connection() as db:
        check(db, rid)
        return [dict(r) for r in db.execute(
            "SELECT mode AS '배식 방식', choice AS '선택', COUNT(*) AS '응답 수' "
            "FROM portions GROUP BY mode, choice ORDER BY mode, choice"
        )]
