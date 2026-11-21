import streamlit as st

st.title("같은 표가 두 번 도착했다면?")
# 공개된 연습용 참가권입니다. 한 브라우저에서 중복 제출만 시험합니다.
tickets = {"연습01", "연습02"}
ballots = st.session_state.setdefault("submitted", set())
scores = st.session_state.setdefault("scores", {"버섯잡채": 0, "떡갈비": 0})
with st.form("ballot"):
    ticket = st.text_input("연습용 참가권", "연습01").strip()
    menu = st.radio("우승 반찬", list(scores))
    send = st.form_submit_button("확정")
if send:
    if ticket not in tickets:
        st.warning("참가권을 확인해 주세요.")
    elif ticket in ballots:
        st.info("이미 쓴 참가권이에요.")
    else:
        ballots.add(ticket)
        scores[menu] += 1
st.write(f"들어온 우승표 {sum(scores.values())}장")
