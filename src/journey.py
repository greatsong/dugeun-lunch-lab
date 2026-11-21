import base64
from copy import deepcopy
from html import escape

import streamlit as st

from downloads import download

# Each scene follows a single person. The level describes a hypothesis about
# this moment, never a measured satisfaction score.
def scene(stage, touch, action, thought, feeling, level):
    return dict(stage=stage, touch=touch, action=action, thought=thought,
                feeling=feeling, level=level, source="수업 예시")


PERSONAS = {
    "자율 배식하는 학생": {
        "title": "처음 보는 나물, 얼마나 담을까?",
        "goal": "먹고 싶은 만큼 반찬을 담고 싶다.",
        "scenes": [
            scene("식단표", "교실의 급식표", "오늘 나오는 반찬 이름을 읽는다.", "방풍나물은 어떤 맛일까?", "궁금함", "보통"),
            scene("배식대", "나물통 앞 집게", "집게를 들었다가 반찬을 조금만 담는다.", "써서 못 먹으면 어쩌지?", "망설임", "불편함"),
            scene("첫입", "식판 위 나물", "한 줄기를 먼저 맛본다.", "생각보다 향이 약하네.", "안도", "편안함"),
            scene("식사 뒤", "빈 나물 칸", "다 먹고 반찬 이름을 다시 본다.", "다음에는 조금 더 담아야지.", "기대", "편안함"),
        ],
        "focus": 1, "hypothesis": "반찬 맛을 짐작하기 어려우면 처음 담을 양을 정하기도 어려울 것이다.",
        "question": "지난번 처음 본 반찬은 얼마나 담았나요? 그 양을 고른 이유가 있었나요?",
    },
    "식단을 짜는 영양 선생님": {
        "title": "이 반찬을 다음 달에 또 넣을까?",
        "goal": "학생 의견을 살펴 다음 달 반찬을 정하고 싶다.",
        "scenes": [
            scene("후보 찾기", "지난달 식단표", "다시 올릴 만한 반찬을 추린다.", "오랜만에 잡채를 넣어 볼까?", "기대", "편안함"),
            scene("식단 편성", "다음 달 식단 초안", "다른 반찬과 재료가 겹치는지 살핀다.", "이날 곁들여도 괜찮겠네.", "집중", "보통"),
            scene("배식", "오늘의 배식대", "배식 중 들은 몇 마디를 기억해 둔다.", "잡채를 또 달라는 학생이 있네.", "반가움", "편안함"),
            scene("다음 편성", "다음 회의의 메뉴 후보", "잡채를 다시 올릴지 결정하려다 멈춘다.", "말이 없던 학생들은 어땠을까?", "막막함", "불편함"),
        ],
        "focus": 3, "hypothesis": "배식 중 들은 몇 마디만으로는 다음에 다시 넣을 반찬을 정하기 어려울 것이다.",
        "question": "지난번에 다시 넣을지 고민한 반찬은 무엇이었나요? 그때 어떤 의견을 살펴보셨나요?",
    },
}

LEVELS = {"편안함": 16, "보통": 51, "불편함": 86, "아직 모름": None}
SOURCES = ["수업 예시", "내 기억", "직접 들은 말", "우리 팀의 짐작", "아직 모름"]


def feeling_line(scenes, focus):
    segments = []
    labels = []
    for i, step in enumerate(scenes):
        x = 100 + 200 * i
        y = LEVELS[step["level"]]
        if y is None:
            labels.append(f'<span class="jr-missing" style="left:{x/8}%">?</span>')
            continue
        if i and LEVELS[scenes[i-1]["level"]] is not None:
            last_y = LEVELS[scenes[i-1]["level"]]
            segments.append(f'<path vector-effect="non-scaling-stroke" d="M{x-200} {last_y} C{x-126} {last_y} {x-74} {y} {x} {y}" />')
        name = escape(step["feeling"])
        labels.append(f'<span class="jr-node {"jr-hot" if i==focus else ""}" style="left:{x/8}%;top:{y}%" title="{name}"></span>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 100" preserveAspectRatio="none">'
           '<g fill="none" stroke="#3c7859" stroke-width="3">' + "".join(segments) + "</g></svg>")
    drawing = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return ('<div class="jr-plot" aria-hidden="true">'
            f'<img alt="" src="data:image/svg+xml;base64,{drawing}">' + "".join(labels) + "</div>")



def draw_map(person, journey):
    steps = journey["scenes"]
    focus = journey["focus"]
    headers, cards, emotions = [], [], []
    for i, step in enumerate(steps):
        hot = " jr-focus" if i == focus else ""
        circle = f'<b class="jr-num">{i+1}</b>'
        headers.append(f'<div class="jr-stage{hot}">{circle}<strong>{escape(step["stage"])}</strong></div>')
        level = step["level"]
        label = "아직 모름" if level == "아직 모름" else escape(step["feeling"])
        emotions.append(f'<div class="jr-emotion{hot}">{label}<span class="jr-sr"> · {escape(level)}</span></div>')
        cards.append(f'''<div class="jr-scene{hot}">
            <b class="jr-mobile-stage">{i+1} · {escape(step["stage"])}</b>
            <small>마주친 것</small><strong>{escape(step["touch"])}</strong>
            <small>한 일</small><p>{escape(step["action"])}</p>
            <small>그때 든 생각 · {escape(step["source"])}</small><p>“{escape(step["thought"])}”</p>
            <span class="jr-mobile-level">마음 · {label} ({escape(level)})</span></div>''')
    focal = escape(steps[focus]["stage"])
    return f'''<section class="jr"><div class="jr-board">
        <div class="jr-head"><div><span>{escape(person)}의 고객 여정 지도</span><h3>{escape(journey["title"])}</h3>
        <p>{escape(journey["goal"])}</p></div></div>
        <div class="jr-row jr-stages"><div class="jr-label">장면</div><div class="jr-four">{"".join(headers)}</div></div>
        <div class="jr-row jr-chart"><div class="jr-label">마음의 변화<div class="jr-scale"><span>편안함</span><span>보통</span><span>불편함</span></div></div>
        <div>{feeling_line(steps,focus)}<div class="jr-four">{"".join(emotions)}</div></div></div>
        <div class="jr-row"><div class="jr-label jr-record">장면 기록</div><div class="jr-four jr-cards">{"".join(cards)}</div></div>
        <div class="jr-ask"><span>{focal}에서 물을 말</span><p>{escape(journey["question"])}</p></div>
        </div></section>'''


STYLE = """
<style>
.jr{container-type:inline-size;color:#193c30;line-height:1.4;word-break:keep-all;overflow-wrap:anywhere}
.jr-board{background:#f9f8ef;border:1px solid #c3d1bc;border-radius:15px;overflow:hidden}
.jr-head{padding:17px 23px 18px;background:#205740;color:#fff8dc}.jr-head span{font-size:.82rem;font-weight:650;color:#e6edc4}.jr .jr-head h3{font-size:clamp(1.4rem,2.2vw,2rem);color:#fff9e7;margin:3px 0 5px!important;padding:3px 0!important;line-height:1.22;letter-spacing:-.045em}.jr .jr-head p{font-size:.94rem;color:white;margin:1px 0 0}
.jr-row{display:grid;grid-template-columns:99px minmax(0,1fr);border-bottom:1px solid #ccd5c5}
.jr-label{padding:12px 8px 10px 14px;color:#48614e;font-size:.82rem;font-weight:750;align-self:stretch;background:#f2f2e8}.jr-stages .jr-label{align-content:center}.jr-four{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}.jr-stage,.jr-emotion{text-align:center}
.jr-stage{padding:10px 5px;display:flex;gap:5px;align-items:center;justify-content:center;background:#ecf1df}.jr-stage strong{font-size:.94rem}.jr-stage.jr-focus{background:#f9e5bd}.jr-num{border-radius:50%;height:22px;min-width:22px;display:inline-grid;place-items:center;color:white;background:#3e6f52;font-size:.78rem}.jr-focus .jr-num{background:#9a5115}
.jr-chart{background:#fffef7}.jr-chart .jr-label{position:relative;display:flex;align-items:center;flex-direction:column;justify-content:flex-end;padding:0 2px 2px}.jr-scale{position:absolute;top:7px;left:14px;height:89px;font-size:.68rem;font-weight:520;color:#637665}.jr-scale span{position:absolute;display:block;white-space:nowrap;transform:translateY(-50%)}.jr-scale span:nth-child(1){top:16%}.jr-scale span:nth-child(2){top:51%}.jr-scale span:nth-child(3){top:86%}.jr-sr{position:absolute;width:1px;height:1px;clip-path:inset(100%);overflow:hidden;white-space:nowrap}.jr-plot{position:relative;height:89px;margin-top:7px;background:repeating-linear-gradient(0deg,transparent 0,transparent calc(35% - 1px),#dce1d6 calc(35% - 1px),#dce1d6 35%);background-position:0 15px}.jr-plot img{width:100%;height:100%;display:block;position:absolute;inset:0;object-fit:fill}.jr-node,.jr-missing{position:absolute;transform:translate(-50%,-50%);border:2px solid #fff;border-radius:100%;width:13px;height:13px;background:#366b4f;box-shadow:0 0 0 1px #366b4f}.jr-hot{background:#b46321;box-shadow:0 0 0 2px #b46321}.jr-missing{height:20px;width:20px;background:#e2e5de;box-shadow:none;top:51%;font-size:13px;text-align:center}.jr-emotion{font-size:.83rem;font-weight:700;padding:4px;line-height:1.25}.jr-emotion.jr-focus{color:#934710}
.jr-record{padding-top:16px}.jr-scene{padding:10px 12px 14px;border-left:1px solid #d6ddcd;background:#fffdf6}.jr-scene.jr-focus{background:#fff3dc;border-top:3px solid #c88235;padding-top:7px}.jr-scene small{display:block;font-size:.69rem;font-weight:650;color:#596c5f;margin-top:9px}.jr-scene strong,.jr .jr-scene p{font-size:.91rem;margin:2px 0 0;line-height:1.38}.jr-mobile-stage,.jr-mobile-level{display:none}
.jr-ask{background:#f7e4bd;padding:12px 17px 14px}.jr-ask span{font-weight:750;color:#865015;font-size:.79rem}.jr .jr-ask p{font-size:1rem;font-weight:700;line-height:1.45;margin:3px 0 0}
@container (max-width:640px){.jr-row{display:block}.jr-head{padding:13px}.jr-stages>.jr-label,.jr-record{display:none}.jr-stage{display:block;padding:8px 2px}.jr-stage strong{display:block;font-size:.78rem;margin-top:3px}.jr-chart>.jr-label{display:block;padding:5px 10px 0;background:#fffef7}.jr-chart .jr-scale{display:none}.jr-chart>.jr-label:after{content:"　위로 갈수록 편안함";font-weight:500;font-size:.74rem}.jr-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.jr-scene{padding:9px;border-top:1px solid #d6ddcd}.jr-scene.jr-focus{padding-top:7px}.jr-scene small{margin-top:6px}.jr-scene strong,.jr .jr-scene p{font-size:.84rem}.jr-mobile-stage{display:block;font-size:.88rem;color:#2f5b40}.jr-mobile-level{display:block;font-size:.73rem;color:#58685b;margin-top:7px}.jr-plot{height:65px}.jr-ask{padding:10px 12px}}
</style>
"""


def notebook_record(person, journey):
    focus = journey["scenes"][journey["focus"]]
    report = []
    for n, s in enumerate(journey["scenes"], 1):
        report.append(f'{n}. {s["stage"]} · {s["touch"]}\n{s["action"]}\n'
                      f'생각과 감정 ({s["source"]}) · {s["thought"]} / {s["feeling"]} ({s["level"]})')
    return {"이 앱을 쓸 사람": person, "기억나는 장면": f'{focus["stage"]} · {focus["action"]}',
            "고객 여정 지도": "\n\n".join(report), "우리 팀의 가설": journey["hypothesis"],
            "그 사람에게 물어볼 질문": journey["question"]}


def journey_activity():
    st.title("어느 순간에 망설였을까?")
    st.write("한 사람을 정하고 그 사람이 거친 장면을 순서대로 짚어 보세요.")
    maps = st.session_state.setdefault("lunch_journeys", deepcopy(PERSONAS))
    person = st.radio("누구의 경험을 그릴까요?", list(maps), horizontal=True)
    journey = maps[person]
    if message := st.session_state.pop("journey_notice", ""):
        st.success(message)
    st.html(STYLE + draw_map(person, journey))
    st.caption("처음 열리는 지도는 수업용 예시입니다. 생각과 감정은 당사자에게 물어보기 전까지 짐작으로 남겨 두세요.")
    st.subheader("우리 팀의 지도로 고치기")
    stages = [s["stage"] for s in journey["scenes"]]
    selected = st.selectbox("고칠 장면", range(len(stages)), index=journey["focus"],
                            format_func=lambda i: stages[i], key=f"scene_{person}")
    current = journey["scenes"][selected]
    with st.form(f"journey_edit_{person}_{selected}"):
        touch = st.text_input("무엇을 보고 누구를 만났나요?", current["touch"], max_chars=45)
        action = st.text_input("그때 한 일", current["action"], max_chars=90)
        thought = st.text_input("그때 든 생각", current["thought"], max_chars=90)
        feeling = st.text_input("그 마음을 한 단어로 쓴다면?", current["feeling"], max_chars=18)
        col1, col2 = st.columns(2)
        level = col1.selectbox("마음 곡선의 높이", list(LEVELS), index=list(LEVELS).index(current["level"]))
        source = col2.selectbox("생각과 감정을 어디서 알았나요?", SOURCES, index=SOURCES.index(current["source"]))
        if st.form_submit_button("지도에 반영"):
            if all(s.strip() for s in (touch, action, thought, feeling)):
                current.update(touch=touch.strip(), action=action.strip(), thought=thought.strip(), feeling=feeling.strip(), level=level, source=source)
                st.session_state.journey_notice = f"{stages[selected]} 장면을 고쳤어요."
                st.rerun()
            else:
                st.warning("아직 알 수 없는 내용은 ‘아직 모름’으로 적어 주세요.")

    with st.form(f"journey_record_{person}"):
        st.subheader("어떤 장면을 더 물어볼까?")
        focus = st.selectbox("다시 물어볼 장면", range(len(stages)), index=journey["focus"], format_func=lambda i: stages[i])
        hypothesis = st.text_input("우리 팀의 가설", journey["hypothesis"], max_chars=180)
        question = st.text_input("그 사람에게 물어볼 질문", journey["question"], max_chars=180)
        if st.form_submit_button("팀 기록에 저장"):
            if not hypothesis.strip() or not question.strip():
                st.warning("우리 팀의 짐작과 그걸 확인할 질문을 한 줄씩 적어 주세요.")
            else:
                journey.update(focus=focus, hypothesis=hypothesis.strip(), question=question.strip())
                st.session_state.setdefault("notebook", {}).update(notebook_record(person,journey))
                st.session_state.journey_notice = "팀 기록에 저장했어요. 8차시에서도 열어 볼 수 있어요."
                st.rerun()
    record = notebook_record(person,journey)
    text = "\n\n".join(f"{k}\n{v}" for k, v in record.items())
    download(st,"이 여정 지도 받기",text.encode("utf-8-sig"),"우리팀_고객여정지도.txt","text/plain")
    st.caption("지도는 현재 브라우저 세션에 보관합니다. 새로고침하기 전에 파일로 받아 두세요.")
