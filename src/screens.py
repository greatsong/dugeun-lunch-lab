import base64
from downloads import download
from pathlib import Path
import datetime as dt
import os
import pandas as pd
import streamlit as st
import classroom as db
import meals

ASSETS = Path(__file__).with_name("그림")
NAMES = {name: ASSETS / f"{i}.webp" for i, name in enumerate(db.DEFAULT)}



def dish(container, name):
    if name in NAMES:
        pic = base64.b64encode(NAMES[name].read_bytes()).decode("ascii")
        container.html(f'<img alt="" width="115" height="98" style="object-fit:contain;max-width:100%" src="data:image/webp;base64,{pic}">')
    else:
        container.write("🍽️")


def meal_screen(manage=False):
    st.header("우리 학교 점심 메뉴")
    selection = meals.choose_school()
    if st.session_state.get("meal_school") != selection:
        st.session_state.meal_school = selection
        st.session_state.pop("dataset", None)
    with st.form("query"):
        left, right = st.columns(2)
        start = left.date_input("시작일", dt.date.today())
        end = right.date_input("종료일", dt.date.today())
        key = st.text_input("나이스 인증키 (있을 때만)", type="password")
        live = st.form_submit_button("나이스 중식 조회", disabled=selection is None)
    if live and selection:
        label, office, school = selection
        try:
            with st.spinner("중식 식단을 불러오고 있어요."):
                rows = meals.fetch(office, school, start, end, (key.strip() or os.environ.get("NEIS_API_KEY", "")))
            st.session_state.dataset = (rows, f"{label} · {start} ~ {end}")
            if not rows:
                st.info("이 기간에는 중식 기록이 없어요.")
        except (ValueError, OSError) as exc:
            st.session_state.pop("dataset", None)
            st.warning(str(exc) if isinstance(exc, ValueError) else "나이스 연결이 끊겼어요. 다시 조회하거나 저장본을 여세요.")
    if st.button("저장된 중식 19일 열기"):
        st.session_state.dataset = (meals.saved(), "당곡고등학교 · 2025년 9월 중식 저장본")
    if "dataset" not in st.session_state:
        if selection is not None:
            return
        st.session_state.dataset = (meals.saved(), "당곡고등학교 · 2025년 9월 중식 저장본")
    rows, source = st.session_state.dataset
    if not rows:
        st.caption("다른 날짜를 고르거나 저장본을 열어 주세요.")
        return
    counts = meals.frequencies(rows)
    st.caption(f"{source} · 중식 {len(rows)}일")
    by_day = dict(rows)
    day = st.selectbox("식단 날짜", list(by_day), key="menu_date_" + source)
    with st.container(border=True):
        st.markdown("**" + day + " 점심**")
        st.write(" · ".join(by_day[day]))
    with st.expander("기간 전체 식단표"):
        st.dataframe(pd.DataFrame([(day, " · ".join(m)) for day, m in rows], columns=["날짜", "식단"]), hide_index=True)
    st.subheader("자주 나온 메뉴")
    ordered = sorted(counts, key=lambda n: (-counts[n], n))
    st.bar_chart(pd.DataFrame({"제공 일수": [counts[n] for n in ordered[:10]]}, index=ordered[:10]), horizontal=True)
    menu = st.selectbox("반찬별 제공 날짜", ordered)
    st.write(f"{menu} · {counts[menu]}일")
    st.write(" / ".join(day for day, menus in rows if menu in menus))
    if manage:
        initial = [n for n in db.DEFAULT if n in counts] or ordered[:8]
        names = st.multiselect("다음 투표에 올릴 메뉴 (2~8개)", ordered, default=initial, max_selections=8,
                               key="choices_" + source)
        current = db.snapshot()
        confirm = st.checkbox("이전 회차의 투표·배식 응답을 지우고 새로 시작합니다.", key="reset_"+current["round_id"])
        if st.button("고른 메뉴로 새 하트 투표 열기", disabled=not confirm):
            try:
                db.new_round(current["round_id"], names, counts, source)
                st.session_state.pop("slips", None)
                st.success("새 회차를 열었어요. 전자칠판에서 하트 투표를 여세요.")
            except ValueError as exc:
                st.warning(str(exc))
    else:
        st.info("조회한 메뉴로 학급 투표를 열 때는 교사용 접수대의 ‘회차 준비’에서 후보를 고릅니다.")


def score_table(snap):
    return pd.DataFrame([{"메뉴": r["name"], "하트": r["hearts"], "제공 일수": r["days"]} for r in snap["menus"]])


def hearts(snap):
    st.header("다시 먹고 싶은 반찬에 하트 하나")
    st.caption(f"이번 회차 · {snap['source']}")
    st.metric("하트를 누른 횟수", sum(r["hearts"] for r in snap["menus"]))
    if snap["phase"] != "heart":
        st.info("하트 투표가 끝났어요. 다음 실험은 개인 월드컵입니다.")
        st.dataframe(score_table(snap), hide_index=True)
        return
    rid = snap["round_id"]
    names = [r["name"] for r in snap["menus"]]
    cols = st.columns(4)
    for i, name in enumerate(names):
        box = cols[i % 4]
        dish(box, name)
        if box.button("♡ " + name, key=f"pick_{rid}_{i}", use_container_width=True):
            st.session_state.pending_heart = (rid, name)
    pending = st.session_state.get("pending_heart")
    if pending and pending[0] == rid:
        st.write(f"{pending[1]}에 하트 하나")
        if st.button("하트 보내기", type="primary"):
            try:
                db.add_heart(rid, pending[1])
            except ValueError as exc:
                st.warning(str(exc))
                st.session_state.pop("pending_heart", None)
                return
            del st.session_state.pending_heart
            st.session_state.heart_notice = "하트가 하나 늘었어요."
            st.rerun()
    if note := st.session_state.pop("heart_notice", ""):
        st.success(note)


def begin(snap, code=None):
    st.session_state.game = {"rid": snap["round_id"], "code": code, "round": [m["name"] for m in snap["menus"]],
                             "winners": [], "index": 0, "matches": 0}
    st.session_state.pop("champion", None)


def cup(snap):
    st.header("내 반찬 월드컵")
    rid = snap["round_id"]
    if st.session_state.get("game", {}).get("rid", rid) != rid:
        st.session_state.pop("game", None)
    game = st.session_state.get("game")
    if not game:
        if msg := st.session_state.pop("cup_error", None):
            st.warning(msg)
        last = st.session_state.get("champion")
        if last and last[0] == rid:
            st.success(last[1])
        if st.button("종이 대진표처럼 연습하기"):
            begin(snap)
            st.rerun()
        if snap["phase"] == "cup":
            with st.form("ticket", clear_on_submit=True):
                code = st.text_input("섞어 뽑은 참가권 8자리", type="password", max_chars=8)
                if st.form_submit_button("참가권으로 시작"):
                    try:
                        db.enter(rid, code)
                    except ValueError as exc:
                        st.warning(str(exc))
                        return
                    begin(snap, code.strip().upper())
                    st.rerun()
        else:
            st.caption("교사가 참가권을 준비하면 우승표를 낼 수 있어요. 연습 결과는 집계에 들어가지 않아요.")
        return
    if game["code"] and snap["phase"] != "cup":
        st.session_state.pop("game")
        st.info("회차가 마감됐어요.")
        return
    if "finalist" in game:
        winner = game["finalist"]
        st.subheader("내가 고른 반찬 · " + winner)
        dish(st, winner)
        if st.button("우승 반찬 확정", type="primary"):
            if game["code"]:
                try:
                    db.finish(rid, game["code"], winner)
                except ValueError as exc:
                    st.session_state.pop("game", None)
                    st.session_state.cup_error = str(exc)
                    st.rerun()
                result = f"{winner}에 우승표 한 장을 냈어요."
            else:
                result = f"연습 우승은 {winner}! {game['matches']}경기를 마쳤어요. 학급 집계에는 들어가지 않아요."
            st.session_state.pop("game", None)
            st.session_state.champion = (rid, result)
            st.rerun()
        return
    choices = game["round"][game["index"]:game["index"] + 2]
    st.caption(("연습 대진" if not game["code"] else "참가권 대진") + f" · {game['matches']+1}번째 경기")
    st.subheader("다시 먹고 싶은 반찬은?")
    for n, (col, menu) in enumerate(zip(st.columns(2), choices)):
        dish(col, menu)
        if col.button(menu, key=f"cup_{rid}_{game['matches']}_{n}", use_container_width=True):
            # 다음 경기로 넘어가기 전에 최종 저장이 실패하면 현재 대진으로 돌아온다.
            candidate = dict(game, winners=list(game["winners"]))
            winner = db.next_round(candidate, menu)
            if winner:
                candidate["finalist"] = winner
            st.session_state.game = candidate
            st.rerun()
    if st.button("대진을 처음부터 다시"):
        st.session_state.pop("game")
        st.rerun()


def results(snap):
    st.header("우리 반 투표 결과")
    st.caption(snap["source"])
    h = sum(m["hearts"] for m in snap["menus"])
    n = snap["finished"]
    values = [("하트 투표", "교사가 센 참여자", snap["observed"], "명"), ("하트 투표", "하트 합계", h, "회"),
              ("개인 월드컵", "완주자", n, "명"), ("개인 월드컵", "우승표", n, "표")]
    cols = st.columns(3)
    cols[0].metric("참여한 친구", "관찰 중" if snap["observed"] is None else f"{snap['observed']}명")
    cols[1].metric("하트", f"{h}회")
    cols[2].metric("완주", f"{n}명")
    st.subheader("첫 실험 · 하트")
    df = score_table(snap)
    st.bar_chart(df.set_index("메뉴")[["하트"]], horizontal=True)
    download(st, "하트와 제공 일수 CSV", df.to_csv(index=False).encode("utf-8-sig"), "하트집계.csv", "text/csv")
    st.subheader("두 번째 실험 · 개인 월드컵")
    if snap["public"]:
        winners = pd.DataFrame([(m["name"], m["wins"]) for m in snap["menus"]], columns=["메뉴", "우승표"])
        st.bar_chart(winners.set_index("메뉴"), horizontal=True)
        values.extend(("개인 월드컵", m["name"], m["wins"], "표") for m in snap["menus"])
    else:
        st.write(f"우승표 {n}장. 다섯 명 이상 완주하고 교사가 마감하면 메뉴별 결과를 공개합니다.")
    data = pd.DataFrame(values, columns=["구분", "항목", "건수", "단위"])
    download(st, "공개용 비교 결과 CSV", data.to_csv(index=False).encode("utf-8-sig"), "공개용_결과.csv", "text/csv")
    if st.button("새로 집계하기"):
        st.rerun()


def receipts():
    st.caption("가상 접수장입니다. 실제 월드컵 집계와 별도로 실험합니다.")
    rows = st.session_state.setdefault("receipts", [])
    with st.form("demo_receipt"):
        number = st.text_input("접수번호", "04")
        name = st.selectbox("메뉴", ["떡갈비", "버섯잡채", "부추해물전"])
        submit = st.form_submit_button("표 보내기")
    if submit and number.strip():
        rows.append((number.strip(), name))
    if st.button("여덟 장 예시 불러오기"):
        rows[:] = list(zip(["01","02","03","04","04","04","05","06"],["버섯잡채","떡갈비","버섯잡채","떡갈비","떡갈비","떡갈비","부추해물전","버섯잡채"]))
    if st.button("접수장 비우기"):
        rows.clear()
    accepted, log = {}, []
    for key, name in rows:
        status = "새 표" if key not in accepted else ("재전송" if accepted[key] == name else "내용 충돌")
        accepted.setdefault(key, name)
        log.append((key, name, status))
    st.write(f"도착 {len(rows)}건 · 집계 {len(accepted)}표")
    if log:
        st.dataframe(pd.DataFrame(log, columns=["접수번호", "메뉴", "처리"]), hide_index=True)
        st.bar_chart(pd.Series(list(accepted.values())).value_counts().rename("유효표"))
