import streamlit as st

st.title("내 반찬 월드컵")
menus = ["버섯잡채", "떡갈비", "오이상추무침", "만두탕수",
         "시금치나물", "가자미순살튀김", "온두부김치볶음", "부추해물전"]
state = st.session_state
if "round_menus" not in state:
    state.round_menus = menus.copy()
    state.next_round = []
    state.matches = 0

if len(state.round_menus) == 1:
    st.success(f"{state.matches}경기 끝! 내가 고른 반찬은 {state.round_menus[0]}")
else:
    for menu in state.round_menus[:2]:
        if st.button(menu):
            state.next_round.append(menu)
            state.matches += 1
            state.round_menus = state.round_menus[2:]
            if not state.round_menus:
                state.round_menus = state.next_round
                state.next_round = []
            st.rerun()
