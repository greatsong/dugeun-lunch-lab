import streamlit as st

st.title("어느 순간에 망설였을까?")
person = st.radio("누구의 경험을 그릴까요?", ["자율 배식하는 학생", "식단을 짜는 영양 선생님"])
if person == "자율 배식하는 학생":
    stages = ["식단표", "배식대", "첫입", "식사 뒤"]
    feelings = ["궁금함", "망설임", "안도", "기대"]
    levels = [0, -1, 1, 1]
else:
    stages = ["후보 찾기", "식단 편성", "배식", "다음 편성"]
    feelings = ["기대", "집중", "반가움", "막막함"]
    levels = [1, 0, 1, -1]

st.caption("가상의 여정입니다. 마음 곡선에서 -1은 불편함, 0은 보통, 1은 편안함을 나타내요.")
st.line_chart({"장면": [1, 2, 3, 4], "마음": levels}, x="장면", y="마음")
for number, (stage, feeling) in enumerate(zip(stages, feelings), start=1):
    st.write(f"{number}. {stage} · {feeling}")
scene = st.selectbox("다시 물어볼 장면", stages)
st.text_input(f"‘{scene}’에서 한 일을 떠올리게 하려면 어떻게 물을까요?")
