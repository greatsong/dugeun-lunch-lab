from downloads import download
import streamlit as st
import pandas as pd
import classroom as db
from screens import meal_screen

def classroom_page():
    st.title("교사용 접수대")
    if not db.desk_access():
        return
    st.caption("접수 연습에는 가상 학번과 이름을 쓰세요. 표를 섞은 다음 학생이 직접 한 장을 뽑습니다.")
    snap = db.snapshot()
    rid = snap["round_id"]
    section = st.radio("교사 메뉴", ["회차 준비", "참가권과 접수", "배식 응답"], horizontal=True,
                       index=0)
    if section == "회차 준비":
        meal_screen(manage=True)
    elif section == "참가권과 접수":
        st.caption("이번 회차 · " + snap["source"])
        if snap["phase"] == "heart":
            st.subheader("하트 투표를 마치고 참가권 준비")
            st.write(f"하트를 누른 횟수 {sum(m['hearts'] for m in snap['menus'])}회")
            with st.form("new_tickets"):
                observed = st.number_input("직접 센 하트 참여자 수", 0, 200, 0)
                count = st.number_input("무기명 참가권 수", 1, 200, 8)
                if st.form_submit_button("하트 마감 · 무기명 참가권 만들기"):
                    try:
                        st.session_state.slips = (rid, db.open_cup(rid, observed, count))
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))
        elif snap["phase"] == "cup":
            slips = st.session_state.get("slips")
            if slips and slips[0] == rid:
                printable = "\n\n".join(f"개인 월드컵　{c}\n────────────────" for c in slips[1])
                download(st, "인쇄할 참가권 저장", printable.encode("utf-8-sig"), "잘라서_섞을_참가권.txt", "text/plain")
            st.write("참가권 파일을 먼저 저장하세요. 인쇄한 표를 잘라 섞고, 확인을 마친 학생이 직접 한 장을 뽑습니다.")
            with st.form("checkin", clear_on_submit=True):
                number = st.text_input("학번", max_chars=12)
                name = st.text_input("이름", max_chars=40)
                if st.form_submit_button("명단 대조 완료 · 참가 확인"):
                    try:
                        db.admit(rid, number, name)
                        st.success("확인했어요. 섞어 둔 표를 한 장 뽑아 주세요.")
                    except ValueError as exc:
                        st.warning(str(exc))
            st.caption("접수 기록에는 회차 안에서 같은 학번인지 확인하는 값만 남깁니다. 누가 어떤 참가권을 뽑았는지는 기록하지 않습니다.")
            st.write(f"현재 완주 {snap['finished']}명")
            confirm = st.checkbox("완주 인원을 확인했습니다. 이 회차 투표를 마감합니다.")
            if st.button("월드컵 마감", disabled=not confirm):
                try:
                    db.close_cup(rid)
                    st.session_state.pop("slips", None)
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
        else:
            st.success(f"회차가 끝났어요. 완주 {snap['finished']}명. 공개 화면에서 결과를 확인하세요.")
    else:
        records = db.portion_summary(rid)
        st.header("이번 회차의 배식 응답")
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df, hide_index=True)
            download(st, "배식 응답 합계 저장", df.to_csv(index=False).encode("utf-8-sig"), "배식응답.csv", "text/csv")
        else:
            st.info("아직 제출된 배식 응답이 없습니다.")
        st.caption("학생이 화면에서 선택한 양입니다. 실제 배식량이나 잔반 무게는 기록하지 않습니다.")
