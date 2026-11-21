import streamlit as st

st.title("오늘 반찬은 얼마나 담을까?")
mode = st.radio("배식 방식", ["내가 직접 담는다", "배식해 주신다"])
if mode == "내가 직접 담는다":
    question = "첫 접시에 얼마나 담고 싶나요?"
else:
    question = "배식받을 때 뭐라고 부탁하고 싶나요?"
choice = st.radio(question, ["조금", "보통", "건너뛰기"], index=None)
if st.button("선택 마치기"):
    if choice is None:
        st.info("먼저 하나를 골라 주세요.")
    else:
        st.write(f"내가 고른 답 · {choice}")
