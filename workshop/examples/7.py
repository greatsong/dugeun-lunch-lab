import streamlit as st

def describe(record):
    if record is None:
        return "응답 없음"
    return f"{record}회"

st.title("빈칸과 0은 같은 뜻일까?")
for label, value, expected in [
    ("아직 묻지 않은 반", None, "응답 없음"),
    ("투표를 열었지만 누른 사람이 없는 반", 0, "0회"),
    ("하트가 두 번 눌린 반", 2, "2회"),
]:
    actual = describe(value)
    mark = "일치" if actual == expected else "다시 확인"
    st.write(f"{label} · 예상 {expected} / 실제 {actual} / {mark}")
