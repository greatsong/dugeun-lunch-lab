from downloads import download
import base64
import io
import json
import secrets
import zipfile
from pathlib import Path

import streamlit as st

import classroom as db
from desk import classroom_page
from journey import journey_activity
from screens import cup, hearts, meal_screen, receipts, results

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="두근두근 급식실", page_icon="🍚", layout="wide")
PROMPTS = json.loads((ROOT / "프롬프트.json").read_text())
style = """
<style>
.stApp {font-family:Pretendard,-apple-system,BlinkMacSystemFont,sans-serif}
[data-testid="stMainBlockContainer"]{max-width:1150px;padding-top:4.6rem}
[data-testid="stMain"] {scroll-padding-top:4.6rem}
h1,h2,h3 {letter-spacing:-.045em;word-break:keep-all}
.lunch-cover{position:relative;overflow:hidden;background:#164b35;color:#fff9df;border-radius:24px;min-height:230px;padding:33px 38px;margin-bottom:8px;isolation:isolate}
.lunch-cover h1{font-size:clamp(2.6rem,5.0vw,4.25rem);line-height:1.08;color:#fff7c4;padding:0;margin:12px 0 14px;font-weight:850}
.lunch-cover p{font-size:1.07rem;margin:0;max-width:62%;line-height:1.6;word-break:keep-all}
.lunch-cover .dish{position:absolute;right:5%;top:5%;width:26%;height:92%;object-fit:contain;filter:drop-shadow(0 12px 10px #082f2180);z-index:-1}
button, [data-testid="stPageLink"]{font-family:inherit}
@media(max-width:650px){.lunch-cover{min-height:192px;padding:24px 19px}.lunch-cover p{font-size:.94rem;max-width:68%}.lunch-cover .dish{width:27%;right:2%;top:11%}}
</style>
"""
st.html(style)


def prompts(unit):
    st.link_button("이 차시 예제 코드를 고쳐서 실행하기",f"https://greatsong.github.io/dugeun-lunch-lab/workshop/?unit={unit}")
    with st.expander("수업에서 쓰는 프롬프트"):
        for row in PROMPTS:
            if row["unit"] == unit:
                st.markdown("**" + row["label"] + "**")
                st.code(row["text"], language=None, wrap_lines=True)


def team_form(key, title, fields):
    stored = st.session_state.setdefault("notebook", {})
    with st.form(key):
        st.subheader(title)
        values = {label: st.text_input(label, value=stored.get(label, ""), max_chars=350)
                  for label in fields}
        if st.form_submit_button("팀 기록에 저장"):
            stored.update(values)
            st.success("팀 기록에 저장했어요. 8차시에서 파일로 받을 수 있어요.")


def home():
    dish = base64.b64encode((ROOT / "그림/0.webp").read_bytes()).decode()
    st.html(f'<section class="lunch-cover"><p>우리 학교 급식 앱 만들기</p><h1>두근두근 급식실</h1><p>급식표에서 반찬을 고르고, 우리 반이 다시 먹고 싶은 메뉴를 물어보세요.</p><img class="dish" alt="버섯잡채" src="data:image/webp;base64,{dish}"></section>')
    left, right = st.columns(2)
    with left.container(border=True):
        st.subheader("첫 수업이라면")
        st.write("파이썬 세 줄에서 제목 한 줄을 바꿔 보세요.")
        st.button("첫 앱 만들기 →", on_click=go, args=(1,))
    with right.container(border=True):
        st.subheader("전자칠판으로 투표한다면")
        st.write("같은 사람이 두 번 누르면 숫자는 어떻게 될까요?")
        st.button("하트 투표 열기 →", on_click=go, args=(4,))
    st.subheader("오늘 수업")
    cols = st.columns(2)
    for i,(label, _) in enumerate(sections[1:9], 1):
        cols[(i-1)//4].button(label, on_click=go, args=(i,))
    st.button("투표 결과 보기 →", on_click=go, args=(9,))
    download(st, "프롬프트 모음 받기", (ROOT / "프롬프트 모음.html").read_bytes(), "급식앱_프롬프트.html", "text/html")


def first():
    st.title("파이썬 세 줄로 만드는 첫 화면")
    st.write("아래 두 칸에 쓴 말이 앱에 어떻게 보이는지 확인하세요. 둘째 칸의 문장을 바꾸고 Enter를 눌러 보세요.")
    with st.container(border=True):
        left, right = st.columns(2)
        title = left.text_input("앱 제목", "두근두근 급식실", max_chars=80)
        intro = right.text_input("제목 아래에 쓸 문장", "오늘 우리 학교 점심", max_chars=160)
    code = 'import streamlit as st\n' + f'st.title({json.dumps(title, ensure_ascii=False)})\n' + f'st.write({json.dumps(intro, ensure_ascii=False)})\n'
    a,b = st.columns(2)
    a.subheader("app.py"); a.code(code, language="python", wrap_lines=True)
    with b.container(border=True):
        st.caption("실행 화면")
        st.title(title); st.write(intro)
    st.subheader("내 문장으로 앱 공개하기")
    st.write("코드 작업대에서는 셋째 줄을 직접 고쳐 실행할 수 있어요. 그 파일을 GitHub에 올리고 Streamlit Community Cloud에서 열면 짝에게 보낼 앱 주소가 생깁니다.")
    st.link_button("1차시 예제부터 가입·공개까지", "https://greatsong.github.io/dugeun-lunch-lab/#signup")
    with st.expander("이 화면에서 만든 두 파일 받기"):
        st.write("지금 보이는 제목과 문구를 쓰려면 아래 두 파일을 받으세요. 코드 작업대에서 고친 문구를 쓰려면 작업대의 ‘코드 받기 ↓’를 누르세요.")
        a, b = st.columns(2)
        download(a, "① app.py 받기", code, "app.py", "text/plain")
        download(b, "② requirements.txt 받기", "streamlit\n", "requirements.txt", "text/plain")
    prompts(1)


def meals_page():
    meal_screen()
    with st.expander("내 저장소에 급식 조회 앱 올리기"):
        st.write("압축을 풀고 안에 든 파일을 GitHub 저장소에 올리세요. Streamlit에서 실행 파일을 급식조회.py로 지정하세요.")
        download(st, "급식 조회 시작 파일 받기", starter_zip(), "급식조회_시작파일.zip", "application/zip")

    prompts(2)


@st.cache_data
def starter_zip():
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w",zipfile.ZIP_DEFLATED) as z:
        for name in ("급식조회.py","meals.py","학교목록.csv","중식19일.csv","requirements.txt"):
            z.write(ROOT/name,name)
    return data.getvalue()


def question_page():
    journey_activity()
    prompts(3)


def mvp_page():
    tab, sketch = st.tabs(["전자칠판 하트 투표", "우리 팀의 첫 기능"])
    with tab:
        hearts(db.snapshot())
    with sketch:
        team_form("mvp","버튼을 누르기 전과 누른 뒤",["첫 화면에 보일 것","누를 버튼","누른 뒤 보일 것"])
        prompts(4)


def portion(snap):
    st.subheader("오늘은 얼마나 담을까?")
    mode = st.radio("이 반찬은 어떻게 담나요?",["직접 담기","배식받기"],horizontal=True)
    st.write("집게로 한 번 집었을 때의 양을 떠올려 보세요." if mode=="직접 담기" else "배식받을 때 원하는 양을 골라 보세요.")
    with st.form("portion"):
        choice=st.radio("원하는 양",["조금","보통","건너뛰기"],index=None,horizontal=True)
        submit=st.form_submit_button("선택 마치기")
    if submit:
        if choice is None:
            st.info("원하는 양을 고르거나 ‘건너뛰기’를 눌러 주세요.")
        else:
            receipt=st.session_state.setdefault("portion_receipt",secrets.token_hex(16))
            try:
                added=db.save_portion(snap["round_id"],receipt,mode,choice)
                if added:st.success("선택을 기록했어요.")
                else:st.info("이 창에서 이미 제출했어요.")
            except ValueError as exc:st.warning(str(exc))
    st.caption("이 창에서는 회차당 한 번 제출할 수 있어요. 실제로 담은 양이나 남긴 양은 기록하지 않아요.")


def cup_page():
    tab, serving = st.tabs(["개인 월드컵","배식 안내"])
    with tab:
        cup(db.snapshot())
    with serving:
        portion(db.snapshot())
    prompts(5)


def ethics():
    st.title("같은 표를 두 번 내면?")
    st.caption("교사용 접수대에서는 가상 학번과 이름을 확인한 뒤 섞은 참가권을 나눠 줍니다. 학생 화면에서는 참가권만 씁니다.")
    receipts()
    prompts(6)


def test_page():
    st.title("고친 뒤 같은 값으로 다시 실행하기")
    st.write("급식이 없는 날짜, 이미 쓴 참가권, 아무것도 고르지 않은 화면 중 우리 팀에 맞는 경우를 시험하세요.")
    team_form("testing","기능 점검 기록",["시험한 입력","예상한 결과","실제로 나온 결과","고친 뒤 달라진 점"])
    prompts(7)


def demo():
    st.title("우리 팀 앱 시연")
    entries=st.session_state.get("notebook",{})
    if entries:
        for label,val in entries.items():
            if val:
                st.markdown("**"+label+"**");st.text(val)
    else:
        st.info("3차시의 팀 질문, 4차시의 첫 기능, 7차시의 점검 기록을 저장하면 여기에 모입니다.")
    team_form("demo","발표 메모",["시연에 쓸 입력","화면에서 확인한 것","더 알아보고 싶은 것"])
    entries=st.session_state.get("notebook",{})
    export="두근두근 급식실 · 팀 실습 기록\n\n"+"\n\n".join(f"{k}\n{v}" for k,v in entries.items() if v)
    download(st, "팀 실습 기록 받기",export.encode("utf-8-sig"),"우리팀_급식앱.txt","text/plain",disabled=not any(entries.values()))
    st.caption("정규수업은 여기서 마칩니다. 더 알아볼 팀만 참여에 동의한 학생들의 응답을 모아 보세요.")
    prompts(8)


sections = [
    ("첫 화면",home),("1차시 · 첫 앱",first),("2차시 · 우리 학교 급식표",meals_page),
    ("3차시 · 우리 팀의 질문",question_page),("4차시 · 하트 투표",mvp_page),
    ("5차시 · 월드컵과 배식 안내",cup_page),("6차시 · 이름 없는 투표함",ethics),
    ("7차시 · 기능 점검",test_page),("8차시 · 팀별 시연",demo),
    ("투표 결과",lambda: results(db.snapshot())),("교사용 접수대",classroom_page),
]

def go(n):
    st.session_state.nav = sections[n][0]

launch = json.loads((ROOT/"launch.json").read_text())
if "nav" not in st.session_state:
    st.session_state.nav = sections[launch["lesson"]][0]
if "class_room" not in st.session_state and launch["room"]:
    st.session_state.class_room = launch["room"]
names = [name for name, _ in sections]
place = st.sidebar.radio("수업 메뉴", names, key="nav")
if place == names[10] and st.session_state.get("class_room"):
    st.sidebar.text("학급 투표에 연결됨")
elif st.session_state.get("class_room"):
    st.sidebar.caption("학급 투표에 연결됨")
else:
    st.sidebar.caption("개별 연습 중 · 이 브라우저에 기록합니다.")
st.sidebar.link_button("수업 첫 페이지", "https://greatsong.github.io/dugeun-lunch-lab/")
try:
    sections[names.index(place)][1]()
except (ValueError, OSError) as exc:
    st.warning(str(exc))
    if st.button("다시 불러오기"): st.rerun()
