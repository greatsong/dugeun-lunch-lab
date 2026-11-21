const el = id => document.getElementById(id);
const examples = await fetch("./activities.json").then(r => r.json());
const drafts = new Map();
let selected, original, support = {}, requestCount = 0, outgoing;
for (const entry of examples) el("unit").add(new Option(entry.label,entry.id));
function showEmpty(){
  outgoing=undefined;
  const p=document.createElement("p"); p.textContent="코드를 읽고 실행을 누르세요.";
  el("output").replaceChildren(p);
}
async function load(id){
  const seq=++requestCount;
  if (selected && original !== undefined) drafts.set(selected.id,el("editor").value);
  const entry=examples.find(a=>a.id===id)||examples[0];
  selected=entry; original=undefined; el("run").disabled=true; el("unit").value=entry.id;
  const url=new URL(location.href);url.searchParams.set("unit",entry.id); history.replaceState(null,"",url);
  for(const key of ["title","situation","prompt","predict","change","check"]) el(key).textContent=entry[key];
  el("notice").textContent="";showEmpty();
  const response=await fetch("examples/"+entry.id+".py");
  if(!response.ok) throw new Error("예제 파일을 읽지 못했어요.");
  const source=await response.text();
  const companions = {};
  if (entry.id==="2"){
    for(const file of ["meals.py","중식19일.csv"]){
      const asset=await fetch("../src/"+file);
      if(!asset.ok) throw new Error("급식 조회 예제의 파일을 읽지 못했어요.");
      companions[file]=await asset.text();
    }
  }
  if(seq!==requestCount)return;
  support=companions; el("companions").hidden=entry.id!=="2"; original=source;el("editor").value=drafts.get(entry.id)??source;el("run").disabled=false;
}
const errors=err=>{el("notice").textContent=String(err.message||err)};
el("unit").onchange=()=>load(el("unit").value).catch(errors);
el("copy").onclick=async()=>{try{await navigator.clipboard.writeText(selected.prompt);el("notice").textContent="프롬프트를 복사했어요."}catch{window.getSelection().selectAllChildren(el("prompt"));el("notice").textContent="선택된 문장을 복사하세요."}};
el("reset").onclick=()=>{if(original===undefined)return;if(el("editor").value!==original&&!confirm("작성한 코드를 지우고 처음 예제를 다시 열까요?"))return;el("editor").value=original;showEmpty()};
el("save").onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([el("editor").value],{type:"text/plain;charset=utf-8"}));a.download="app.py";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
window.addEventListener("message",e=>{if(e.source===outgoing?.frame.contentWindow && e.origin==="null" && e.data==="ready")e.source.postMessage({code:outgoing.code,support:outgoing.support},"*")});
el("run").onclick=()=>{
  if(!el("editor").value.trim()){el("notice").textContent="실행할 코드를 먼저 적어 주세요.";return}
  const frame=document.createElement("iframe");frame.title="내 파이썬 실행 결과";frame.sandbox="allow-scripts allow-downloads";frame.src="runner.html";
  outgoing={frame,code:el("editor").value,support};el("output").replaceChildren(frame);el("notice").textContent="코드를 바꾼 뒤 다시 실행할 수 있어요.";
};
await load(new URL(location.href).searchParams.get("unit")||"1").catch(errors);
