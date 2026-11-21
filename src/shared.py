import re
import streamlit as st
import remote_room
from downloads import download

BASE = "https://greatsong.github.io/dugeun-lunch-lab/lab/"

def create():
    with st.expander("여러 기기에서 함께 투표하기"):
        st.write("학급 투표방을 만들면 전자칠판과 학생 휴대폰에서 같은 표를 모을 수 있어요. 방은 7일 동안 사용할 수 있습니다.")
        if st.button("새 학급 투표방 만들기"):
            credentials = remote_room.create_room()
            st.session_state.class_room = credentials["room"]
            st.session_state.class_admin = credentials["admin"]
            st.rerun()
        with st.form("existing_room"):
            room = st.text_input("기존 방 코드", max_chars=20).strip().lower()
            if st.form_submit_button("기존 방 열기"):
                if not re.fullmatch(r"[0-9a-f]{20}", room):
                    st.warning("방 코드 20자리를 확인하세요.")
                else:
                    st.session_state.class_room = room
                    try:
                        remote_room.snapshot()
                    except ValueError:
                        del st.session_state.class_room
                        raise
                    st.rerun()
    return False

def manage():
    room = st.session_state.class_room
    if not st.session_state.get("class_admin"):
        with st.form("teacher_unlock", clear_on_submit=True):
            admin = st.text_input("교사용 관리 코드", type="password")
            if st.form_submit_button("접수대 열기"):
                st.session_state.class_admin = admin.strip()
                try:
                    remote_room.verify_admin()
                except ValueError:
                    st.session_state.pop("class_admin", None)
                    raise
                st.rerun()
        return False
    with st.expander("학급 주소 · 교사용 보관 파일", expanded=True):
        st.write("학생에게 아래 **참여 주소**를 보내세요. 전자칠판에서도 이 주소를 엽니다.")
        st.code(f"{BASE}?lesson=4&room={room}", language=None)
        st.caption("학생은 같은 주소에서 왼쪽 수업 메뉴로 월드컵과 결과 화면을 열 수 있어요.")
        admin = st.session_state.class_admin
        record = f"교사 전용 · 학생에게 보내지 마세요.\\n교사용 접수대 {BASE}?lesson=10&room={room}\\n방 코드 {room}\\n관리 코드 {admin}\\n"
        download(st,"교사용 보관 파일 받기",record.replace("\\n","\n"),"학급투표_교사전용.txt","text/plain")
        st.caption("새 창에서 접수대를 열 때 관리 코드가 필요합니다. 먼저 위 파일을 교사용 기기에 저장하세요.")
        if st.button("접수대 잠그기"):
            st.session_state.pop("class_admin",None)
            st.session_state.pop("slips",None)
            st.rerun()
    return True
