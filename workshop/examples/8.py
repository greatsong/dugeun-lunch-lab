import streamlit as st

st.title("우리 팀 급식 앱 시연")
with st.form("demo"):
    person = st.text_input("누구를 위해 만들었나요?")
    action = st.text_input("짝에게 부탁할 조작 한 가지")
    expected = st.text_input("어떤 결과가 나와야 하나요?")
    observed = st.text_input("짝이 실제로 본 결과")
    show = st.form_submit_button("시연 기록 보기")
if show:
    if all(part.strip() for part in [person, action, expected, observed]):
        st.subheader(person)
        st.write(f"부탁한 일 · {action}")
        st.write(f"예상 · {expected}")
        st.write(f"실제 · {observed}")
    else:
        st.info("비어 있는 칸을 확인해 주세요.")
