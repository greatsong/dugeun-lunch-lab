const assetBase = new URL("../src/", location.href);
const params = new URLSearchParams(location.search);
const room = params.get("room") || "";
const n = Number(params.get("lesson"));
const inputs = {
  lesson: Number.isInteger(n) && n >= 0 && n <= 10 ? n : 0,
  room: /^[A-Za-z0-9_-]{6,100}$/.test(room) ? room : ""
};
const names = ["app.py","classroom.py","classroom_local.py","desk.py","shared.py","remote_room.py","downloads.py","meals.py","screens.py","급식조회.py","requirements.txt","프롬프트.json","프롬프트 모음.html","중식19일.csv", ...Array.from({length:8}, (_, i) => `그림/${i}.webp`)];

const files = Object.fromEntries(names.map(name=>[name,{url:new URL(name,assetBase).href}]));
files["launch.json"] = JSON.stringify(inputs);
try {
  const { mount } = await import("https://cdn.jsdelivr.net/npm/@stlite/browser@1.4.0/build/stlite.js");
  await mount({entrypoint:"app.py",requirements:["pandas","sqlite3"],files,
    idbfsMountpoints:["/home/pyodide/lunch-record"],
    streamlitConfig:{"theme.base":"light","theme.primaryColor":"#237250","client.toolbarMode":"minimal"}
  },document.getElementById("root"));
} catch (error) {
  console.error(error);
  const box=document.createElement("p");
  box.textContent="파이썬 실행 파일을 불러오지 못했습니다. 인터넷 연결을 확인한 뒤 새로고침해 주세요.";
  document.body.prepend(box);
}
