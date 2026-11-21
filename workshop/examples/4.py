import streamlit as st

st.title("다시 먹고 싶은 반찬")
hearts = st.session_state.setdefault("hearts", {"버섯잡채": 0, "배추김치": 0})
for menu in hearts:
    if st.button("♡ " + menu):
        hearts[menu] += 1
    st.write(f"{menu} · 누른 횟수 {hearts[menu]}회")
