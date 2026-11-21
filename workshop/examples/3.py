import streamlit as st

st.title("점심시간에 누구를 만날까?")
person = st.radio("이야기를 듣고 싶은 사람", ["식단을 짜는 영양 선생님", "반찬을 직접 담는 학생"])
if person == "식단을 짜는 영양 선생님":
    question = "지난달 식단을 짤 때 다시 넣을지 고민했던 반찬이 있었나요?"
else:
    question = "지난번 자율 배식 때 어떤 반찬을 얼마나 담았나요?"
st.write(question)
st.text_area("이 질문으로 떠올릴 수 있는 장면")
