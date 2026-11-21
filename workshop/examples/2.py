from datetime import date
import streamlit as st
from meals import choose_school, one_day, saved

st.title("그날 점심은 뭐였지?")
day = st.date_input("날짜", date(2025, 9, 1))
source = st.radio("급식표", ["수업용 저장본", "나이스에서 조회"])
if source == "수업용 저장본":
    menus = dict(saved()).get(day.isoformat(), [])
    st.caption("당곡고 · 2025년 9월 중식 19일")
else:
    selection = choose_school()
    if not st.button("이 날짜 조회", disabled=selection is None):
        st.stop()
    try:
        _, office, school = selection
        menus = one_day(office, school, day)
    except (ValueError, OSError):
        st.warning("조회에 실패했어요. 저장본으로 바꾸거나 다시 시도하세요.")
        st.stop()
if menus:
    for menu in menus:
        st.write(menu)
else:
    st.info("이 자료에는 그날 중식 기록이 없어요.")
