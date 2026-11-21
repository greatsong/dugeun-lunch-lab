/* Anonymous, short-lived class totals. Use a separate project for a new school. */
const DEFAULT_MENU = ['버섯잡채','떡갈비','오이상추무침','만두탕수','시금치나물','가자미순살튀김','온두부김치볶음','부추해물전'];
const MAX_ROOMS = 18;
const LIFETIME = 7 * 24 * 3600 * 1000;
const ADMIN_ACTIONS = ['verify_admin','new_round','open_cup','admit','close_cup','portion_summary','remove_room'];
const WRITE_ACTIONS = ['new_round','add_heart','open_cup','admit','finish','close_cup','save_portion'];

function insist(ok, message) { if (!ok) throw Error(message); }
function digest(s) {
  return Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s)).replace(/=+$/, '');
}
function randomKey() { return Utilities.getUuid().replace(/-/g, ''); }
function integer(x, min, max) { return Number.isInteger(x) && x >= min && x <= max; }
function validText(s, max) { return typeof s === 'string' && s.trim().length > 0 && s.length <= max; }
function json(data) { return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON); }
function doGet() { return json({service:'두근두근 급식실', version:1}); }
function doPost(e) {
  let lock;
  try {
    insist(e && e.postData && e.postData.contents.length <= 6000, '전송할 자료의 길이를 확인해 주세요.');
    const req = JSON.parse(e.postData.contents);
    insist(req && typeof req === 'object', '요청 형식을 확인해 주세요.');
    lock = LockService.getScriptLock();
    insist(lock.tryLock(15000), '다른 표를 접수하고 있어요. 잠시 뒤 다시 눌러 주세요.');
    return json({ok:true, value:dispatch(req, PropertiesService.getScriptProperties())});
  } catch (e) {
    return json({ok:false, error:e.message || '연결이 끊겼어요. 다시 열어 주세요.'});
  } finally {
    if (lock && lock.hasLock()) lock.releaseLock();
  }
}
function expire(store, registry) {
  const now = Date.now();
  Object.keys(registry).forEach(id=>{
    if (registry[id] <= now) { dropRoom(store,id); delete registry[id]; }
  });
}
function dropRoom(store, id) {
  const count = Number(store.getProperty('n'+id)) || 0;
  for (let i=0;i<count;i++) store.deleteProperty(id+'.'+i);
  store.deleteProperty('n'+id);
}
function readRoom(store,id) {
  const n = Number(store.getProperty('n'+id)) || 0;
  insist(n > 0, '학급 코드를 확인하세요. 학급 자료는 일주일 동안 보관합니다.');
  let text = '';
  for(let i=0;i<n;i++) text += store.getProperty(id+'.'+i);
  const room = JSON.parse(text);
  if (room.expires <= Date.now()) {
    dropRoom(store,id);
    throw Error('이 학급의 보관 기간이 끝났어요.');
  }
  return room;
}
function saveRoom(store,id,room) {
  const text = JSON.stringify(room);
  insist(text.length <= 20500, '한 회차에서 받을 수 있는 표를 모두 받았어요.');
  const data = {};
  const parts = text.match(/[\s\S]{1,1800}/gu);
  for(let i=0;i<parts.length;i++) data[id+'.'+i] = parts[i];
  const previous = Number(store.getProperty('n'+id)) || 0;
  data['n'+id] = String(parts.length);
  store.setProperties(data);
  for(let i=parts.length;i<previous;i++) store.deleteProperty(id+'.'+i);
}
function round(names,days,source) {
  insist(Array.isArray(names) && integer(names.length,2,8) && new Set(names).size===names.length
    && names.every(n=>validText(n,50)) && validText(source,160), '서로 다른 메뉴를 2~8개 골라 주세요.');
  return {round_id:randomKey(), phase:'heart', observed:null, source:source, salt:randomKey(),
          menus:names.map(name=>({name:name, days:days && integer(days[name],0,366)?days[name]:null, hearts:0, wins:0})),
          tickets:{}, admitted:[], receipts:[], portions:{}};
}
function dispatch(q,store) {
  const action=q.action;
  if (action==='create') {
    const registry = JSON.parse(store.getProperty('active') || '{}');
    expire(store,registry);
    insist(Object.keys(registry).length < MAX_ROOMS, '지금은 학급이 모두 열려 있어요. 사용을 마친 학급을 닫은 뒤 다시 시도해 주세요.');
    const room = randomKey().slice(0,20), admin = randomKey()+randomKey(), expires=Date.now()+LIFETIME;
    saveRoom(store,room,{adminHash:digest(admin), expires:expires, data:round(DEFAULT_MENU, {}, '수업 예시 후보')});
    registry[room] = expires;
    store.setProperty('active', JSON.stringify(registry));
    return {room:room, admin:admin};
  }
  insist(typeof q.room==='string' && /^[0-9a-f]{20}$/.test(q.room),'학급 코드를 확인해 주세요.');
  const room = readRoom(store,q.room), r=room.data, a=q.args || {};
  if (ADMIN_ACTIONS.includes(action)) {
    insist(typeof q.admin==='string' && q.admin.length===64 && digest(q.admin)===room.adminHash,'교사용 관리 코드를 확인하세요.');
  }
  if (action==='verify_admin') return true;
  if (action==='remove_room') {
    dropRoom(store,q.room);
    const registry=JSON.parse(store.getProperty('active') || '{}');
    delete registry[q.room]; store.setProperty('active',JSON.stringify(registry));
    return true;
  }
  if (action==='snapshot') {
    const finished = r.menus.reduce((n,m)=>n+m.wins,0);
    const visible = r.phase==='closed' && finished>=5;
    return {round_id:r.round_id, phase:r.phase, observed:r.observed, source:r.source, finished:finished, public:visible,
      menus:r.menus.map(m=>({name:m.name,days:m.days,hearts:m.hearts,wins:visible?m.wins:null}))};
  }
  insist(r.round_id===q.rid, '새 회차가 시작됐어요. 화면을 다시 여세요.');
  function phase(allowed) { insist(allowed.includes(r.phase), '지금은 이 투표를 받지 않아요. 회차를 확인하세요.'); }
  function candidate(name) { const m = r.menus.find(m=>m.name===name); insist(m,'이번 회차의 메뉴를 확인하세요.'); return m; }
  function shortHash(kind,val) {return digest(r.salt+':'+kind+':'+val).slice(0,16);}
  function ticket() {
    phase(['cup']);
    insist(typeof a.code==='string' && /^[A-F0-9]{8}$/.test(a.code), '참가권 여덟 자리를 확인해 주세요.');
    const key=shortHash('ticket',a.code);
    insist(r.tickets[key]===false,'받은 참가권을 확인하세요. 이미 낸 표는 다시 쓸 수 없어요.');
    return key;
  }
  let result = true;
  switch(action) {
    case 'new_round': room.data=round(a.names,a.days,a.source); break;
    case 'add_heart': {
      phase(['heart']); const m=candidate(a.name); insist(m.hearts < 10000,'이 메뉴의 하트 투표를 마감해 주세요.'); m.hearts++; break;
    }
    case 'open_cup': {
      phase(['heart']);
      insist(integer(a.count,1,200) && integer(a.observed,0,200), '참가권은 1~200장, 관찰 인원은 0~200명으로 입력하세요.');
      const codes=new Set();
      while(codes.size<a.count) codes.add(randomKey().slice(0,8).toUpperCase());
      result=Array.from(codes);
      for(const code of result) r.tickets[shortHash('ticket',code)]=false;
      r.phase='cup'; r.observed=a.observed; break;
    }
    case 'admit':{
      phase(['cup']);
      insist(typeof a.tag==='string' && /^[a-f0-9]{64}$/.test(a.tag),'접수 기록을 확인하세요.');
      const key=shortHash('admit',a.tag);
      insist(!r.admitted.includes(key),'이미 접수한 학번이에요. 참가권은 한 장씩 뽑아요.');
      insist(r.admitted.length<Object.keys(r.tickets).length,'참가권을 모두 나눠 주었어요.');
      r.admitted.push(key); break;
    }
    case 'enter': ticket(); break;
    case 'finish':{
      const key=ticket(), m=candidate(a.winner);
      r.tickets[key]=true; m.wins++; break;
    }
    case 'close_cup': phase(['cup']); r.phase='closed'; break;
    case 'save_portion':{
      phase(['heart','cup']);
      insist(['직접 담기','배식받기'].includes(a.mode) && ['조금','보통','건너뛰기'].includes(a.choice)
        && typeof a.receipt==='string' && /^[a-f0-9]{32}$/.test(a.receipt),'배식 방식과 원하는 양을 골라 주세요.');
      const key=shortHash('portion',a.receipt), pair=a.mode+'|'+a.choice;
      if (r.receipts.includes(key)) return false;
      insist(r.receipts.length<200, '이 회차에서 받을 수 있는 배식 응답 200건을 모두 받았어요.');
      r.receipts.push(key); r.portions[pair]=(r.portions[pair] || 0)+1; break;
    }
    case 'portion_summary': return Object.keys(r.portions).sort().map(k=>({'배식 방식':k.split('|')[0],'선택':k.split('|')[1],'응답 수':r.portions[k]}));
    default: throw Error('요청한 기능을 확인하세요.');
  }
  if (WRITE_ACTIONS.includes(action)) saveRoom(store,q.room,room);
  return result;
}
