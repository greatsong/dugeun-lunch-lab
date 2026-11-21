import csv
import datetime as dt
import json
import sys
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

API = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def saved():
    with Path(__file__).with_name("중식19일.csv").open(encoding="utf-8-sig") as f:
        return [(dt.datetime.strptime(r["날짜"], "%Y%m%d").date().isoformat(),
                 r["메뉴"].split("|")) for r in csv.DictReader(f)]


def one_day(office, school, date, key=""):
    params = dict(Type="json", ATPT_OFCDC_SC_CODE=office, SD_SCHUL_CODE=school,
                  MMEAL_SC_CODE="2", MLSV_YMD=date.strftime("%Y%m%d"))
    if key:
        params["KEY"] = key
    url = API + "?" + urlencode(params)
    if sys.platform == "emscripten":
        from js import XMLHttpRequest
        try:
            request = XMLHttpRequest.new()
            request.open("GET", url, False)
            request.send()
            if request.status != 200:
                raise OSError("급식 자료를 불러오지 못했어요.")
            data = json.loads(request.responseText)
        except Exception as err:
            raise OSError("나이스 연결을 확인해 주세요.") from err
    else:
        with urlopen(url, timeout=10) as response:
            data = json.load(response)
    code = data.get("RESULT", {}).get("CODE")
    if code == "INFO-200":
        return []
    if "mealServiceDietInfo" not in data:
        raise ValueError("나이스가 식단을 보내지 않았어요. 학교 코드와 인증키를 확인하세요.")
    rows = [row for part in data["mealServiceDietInfo"] for row in part.get("row", [])]
    items = []
    for row in rows:
        if (row.get("SD_SCHUL_CODE"), row.get("MLSV_YMD"), row.get("MMEAL_SC_CODE")) != (school, params["MLSV_YMD"], "2"):
            raise ValueError("요청한 학교·날짜와 다른 자료가 왔어요. 인증키를 넣거나 저장본을 여세요.")
        for menu in re.split(r"<br\s*/?>", row["DDISH_NM"], flags=re.I):
            cleaned = re.sub(r"\s*\([\d.,\s]+\)", "", menu).strip().strip("*").strip()
            if cleaned and cleaned not in items:
                items.append(cleaned)
    return items


def fetch(office, school, start, end, key=""):
    span = (end - start).days + 1
    if not 1 <= span <= 31 or not re.fullmatch(r"[A-Z]\d{2}", office) or not re.fullmatch(r"\d{7}", school):
        raise ValueError("교육청 코드, 학교 코드 7자리, 조회 기간 1~31일을 확인하세요.")
    rows = []
    for n in range(span):
        day = start + dt.timedelta(days=n)
        items = one_day(office, school, day, key)
        if items:
            rows.append((day.isoformat(), items))
    return rows


def frequencies(rows):
    return Counter(menu for day, menus in rows for menu in dict.fromkeys(menus))


@lru_cache(maxsize=1)
def load_schools():
    path = Path(__file__).with_name("학교목록.csv")
    with path.open(encoding="utf-8", newline="") as file:
        return {
            f"{row['학교명']} · {row['지역']}": (row["교육청코드"], row["학교코드"])
            for row in csv.DictReader(file)
        }


def choose_school():
    import streamlit as st

    schools = load_schools()
    label = st.selectbox("학교 이름", schools.keys(), index=None,
                         placeholder="학교 이름을 입력하세요", help="이름이 같으면 지역을 확인하세요.")
    if label is None:
        return None
    office, code = schools[label]
    st.caption(f"교육청 코드 {office} · 학교 코드 {code}")
    return label, office, code
