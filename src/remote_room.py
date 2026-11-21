"""GitHub Pages와 학급 투표 저장소 연결. 이름·학번은 기기 밖으로 보내지 않는다."""
import hashlib
import hmac
import json
import re

import streamlit as st

ENDPOINT = "https://script.google.com/macros/s/AKfycbyDVNOAm1B3nxS5LgY_vekucC4o1bLV72NZa4Y3S0-7C5AvRSUIj-J7Asi6be3vsOQe/exec"
ADMIN_ACTIONS = {"verify_admin", "new_round", "open_cup", "admit", "close_cup", "portion_summary", "remove_room"}


def _call(action, rid=None, **args):
    from js import XMLHttpRequest

    envelope = {"action": action, "args": args}
    if action != "create":
        envelope["room"] = st.session_state.get("class_room", "")
    if action in ADMIN_ACTIONS:
        envelope["admin"] = st.session_state.get("class_admin", "")
    if rid is not None:
        envelope["rid"] = rid
    try:
        xhr = XMLHttpRequest.new()
        xhr.open("POST", ENDPOINT, False)
        xhr.setRequestHeader("Content-Type", "text/plain;charset=UTF-8")
        xhr.send(json.dumps(envelope, ensure_ascii=False))
        if xhr.status != 200:
            raise OSError()
        result = json.loads(str(xhr.responseText))
    except Exception:
        raise ValueError("학급 투표 저장소에 연결하지 못했어요. 인터넷 연결을 확인한 뒤 다시 시도하세요.") from None
    if not result.get("ok"):
        raise ValueError(result.get("error", "학급 코드를 확인하세요."))
    return result["value"]


def create_room():
    return _call("create")


def verify_admin():
    return _call("verify_admin")


def remove_room():
    return _call("remove_room")


def snapshot():
    return _call("snapshot")


def new_round(rid, names, days, source):
    return _call("new_round", rid, names=list(names), days={n: days.get(n) for n in names}, source=source)


def add_heart(rid, name):
    return _call("add_heart", rid, name=name)


def open_cup(rid, observed, count):
    return _call("open_cup", rid, observed=observed, count=count)


def admit(rid, student_id, name):
    student_id = student_id.strip()
    if not re.fullmatch(r"[0-9]{3,12}", student_id) or not name.strip():
        raise ValueError("학번은 숫자 3~12자리로 쓰고, 이름은 명단과 대조하세요.")
    admin = st.session_state.get("class_admin", "")
    if not admin:
        raise ValueError("교사용 관리 코드를 입력하세요.")
    tag = hmac.new(admin.encode(), f"{rid}|{student_id}".encode(), hashlib.sha256).hexdigest()
    return _call("admit", rid, tag=tag)


def enter(rid, code):
    return _call("enter", rid, code=code.strip().upper())


def finish(rid, code, winner):
    return _call("finish", rid, code=code.strip().upper(), winner=winner)


def close_cup(rid):
    return _call("close_cup", rid)


def save_portion(rid, receipt, mode, choice):
    return _call("save_portion", rid, receipt=receipt, mode=mode, choice=choice)


def portion_summary(rid):
    return _call("portion_summary", rid)
