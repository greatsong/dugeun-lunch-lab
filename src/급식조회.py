import streamlit as st
from meals import choose_school, one_day, saved

st.title("날짜별 우리 학교 중식")
source = st.radio("식단 출처", ["나이스", "19일 저장본"])
day = st.date_input("급식 날짜")
if source == "19일 저장본":
    items = dict(saved()).get(day.isoformat(), [])
    st.caption("당곡고등학교 수업용 저장본 · 달력에서 저장된 날짜를 골라 주세요.")
    st.write([d for d, _ in saved()])
else:
    selection = choose_school()
    key = st.text_input("나이스 인증키", type="password")
    if not st.button("중식 조회", disabled=selection is None):
        st.stop()
    try:
        _, office, school = selection
        items = one_day(office, school, day, key.strip())
    except (OSError, ValueError) as exc:
        st.info("조회를 마치지 못했어요. 학교 설정을 확인하거나 저장본을 열어 주세요.")
        st.stop()
if items:
    for item in items:
        st.write(item)
else:
    st.write("이 날짜의 중식 기록이 없습니다.")
