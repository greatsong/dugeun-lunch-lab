import streamlit as st
import classroom_local as local

DEFAULT = local.DEFAULT
next_round = local.next_round

def backend():
    if st.session_state.get("class_room"):
        import remote_room
        return remote_room
    return local

def __getattr__(name):
    if name in {"snapshot", "new_round", "add_heart", "open_cup", "admit", "enter", "finish", "close_cup", "save_portion", "portion_summary"}:
        return getattr(backend(), name)
    raise AttributeError(name)

def desk_access():
    if st.session_state.get("class_room"):
        from shared import manage
        return manage()
    st.caption("개별 연습용 접수대입니다. 여기서 만든 참가권과 투표는 이 브라우저 안에서만 사용합니다.")
    from shared import create
    if create():
        return False
    return True
