(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const grades = 'ABCDEFG'.split('');
  const isoLocal = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const today = () => isoLocal(new Date());
  const money = n => '₹ ' + Number(n || 0).toLocaleString('en-IN', {minimumFractionDigits:2,maximumFractionDigits:2});
  const val = el => Number(el?.value || 0);
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid = new URLSearchParams(location.search).get('uid');
  if (!uid) return; // Entries are available only after native Firebase sign-in.
  const key = name => `${name}_${uid}`;
  // Claim the offline v2 records for the first account that signs in on this phone.
  if (!localStorage.getItem('mb_migrated_v2')) {
    for (const name of ['mb_entries_v1','mb_rates_v1','mb_hour_rate_v1']) {
      const old = localStorage.getItem(name);
      if (old !== null && localStorage.getItem(key(name)) === null) localStorage.setItem(key(name), old);
      localStorage.removeItem(name);
    }
    localStorage.setItem('mb_migrated_v2', uid);
  }
  const load = (key, fallback) => { try {return JSON.parse(localStorage.getItem(key)) ?? fallback} catch (_) {return fallback} };
  let entries = load(key('mb_entries_v1'), []), rates = load(key('mb_rates_v1'), [40,50,60,70,80,90,100]);
  let hourRate = Number(localStorage.getItem(key('mb_hour_rate_v1')) || 100);
  let selectedMonth = today().slice(0,7);
  const save = () => localStorage.setItem(key('mb_entries_v1'), JSON.stringify(entries));
  const add = records => { entries.push(...records); save(); renderReports(); alert('એન્ટ્રી સેવ થઈ'); };
  const records = (type) => entries.filter(e => e.type === type && e.date.startsWith(selectedMonth));
  const sum = (arr, key='amount') => arr.reduce((n,e) => n + Number(e[key] || 0),0);
  const line = (label,amount,cls='') => `<div class="line"><span>${esc(label)}</span><b class="${cls}">${money(amount)}</b></div>`;
  const panel = (heading,body) => `<div class="panel"><h3>${esc(heading)}</h3>${body}</div>`;
  const actualDate = () => today();
  const diamond = $('#diamond .panel');
  const diamondCounts = $$('.grid input', diamond).filter((_,i)=>i%2===0);
  const diamondRates = $$('.grid input', diamond).filter((_,i)=>i%2===1);
  const diamondWithdrawal = $('input[placeholder*="ઉપાડ"]',diamond);
  function refreshRates(){
    diamondRates.forEach((el,i)=>el.value=money(rates[i]));
    const settingInputs=$$('#settings .settings-pair .panel:first-child .grid input');
    settingInputs.forEach((el,i)=>el.value=rates[i]);
    $('#hours input[readonly]').value=money(hourRate);
    $('#settings .settings-pair .panel:last-child input').value=hourRate;
  }
  refreshRates();
  $('#diamond .action').onclick = () => {
    const department=$('#diamond select').value;
    if(department==='ડિપાર્ટમેન્ટ પસંદ કરો'){alert('ડિપાર્ટમેન્ટ પસંદ કરો');return}
    const date=actualDate(), items=[]; let invalid=false;
    diamondCounts.forEach((el,i)=>{
      const pieces=val(el);
      if(pieces<0 || !Number.isInteger(pieces)){el.focus();alert('નંગ પૂર્ણાંક હોવા જોઈએ');items.length=0;invalid=true;return}
      if(pieces>0)items.push({type:'diamond',date,department,grade:grades[i],pieces,rate:rates[i],amount:pieces*rates[i]});
    });
    if(invalid)return;
    const withdrawal=val(diamondWithdrawal);
    if(withdrawal<0){alert('ઉપાડ માન્ય નથી');return}
    if(withdrawal)items.push({type:'withdrawal',source:'diamond',date,amount:withdrawal});
    if(!items.some(e=>e.type==='diamond')){alert('નંગ ભરો');return}
    add(items); diamondCounts.forEach(el=>el.value='');diamondWithdrawal.value='';
  };
  const hoursPanel=$('#hours .panel');
  const hoursInputs=$$('input',hoursPanel);
  hoursInputs[0].value=actualDate();
  $('.action',hoursPanel).onclick=()=>{
    const date=hoursInputs[0].value || actualDate(), hours=val(hoursInputs[1]), withdrawal=val(hoursInputs[3]);
    if(hours<=0||withdrawal<0){alert('માન્ય કલાક અને ઉપાડ લખો');return}
    const items=[{type:'hour',date,hours,rate:hourRate,amount:hours*hourRate}];
    if(withdrawal)items.push({type:'withdrawal',source:'hour',date,amount:withdrawal});
    add(items);hoursInputs[1].value='';hoursInputs[3].value='';
  };
  const expensePanel=$('#expense .panel');
  $('.action',expensePanel).onclick=()=>{
    const selects=$$('select',expensePanel), inputs=$$('input',expensePanel), amount=val(inputs[1]);
    if(selects[0].selectedIndex===0||selects[1].selectedIndex===0||amount<=0){alert('કામ, ખર્ચનો પ્રકાર અને રકમ ભરો');return}
    add([{type:'expense',source:selects[0].selectedIndex===1?'diamond':'hour',category:selects[1].value,note:inputs[0].value,date:actualDate(),amount}]);
    inputs.forEach(x=>x.value='');
  };
  const settings=$$('#settings .settings-pair .panel');
  $('.action',settings[0]).onclick=()=>{
    const changed=$$('.grid input',settings[0]).map(val);
    if(changed.some(n=>n<0||!Number.isFinite(n))){alert('માન્ય ભાવ ભરો');return}
    rates=changed;localStorage.setItem(key('mb_rates_v1'),JSON.stringify(rates));refreshRates();alert('ભાવ સેવ થયા');
  };
  $('.action',settings[1]).onclick=()=>{
    const n=val($('input',settings[1]));if(n<=0){alert('માન્ય કલાકનો દર ભરો');return}
    hourRate=n;localStorage.setItem(key('mb_hour_rate_v1'),String(n));refreshRates();alert('કલાકનો દર સેવ થયો');
  };
  // The PDF receives precisely the month and entries currently visible in the report.
  function printReport(html,title){
    if(window.Android?.printPdf){window.Android.printPdf(`<html lang="gu"><meta charset="utf-8"><style>body{font-family:sans-serif;margin:24px;color:#17243a}h1{font-size:19px}table{border-collapse:collapse;width:100%;font-size:10px}td,th{border:1px solid #aaa;padding:7px;text-align:center}th{background:#17243a;color:white}tfoot{background:#1da248;color:white}</style><h1>MB ડાયમંડ ડાયરી · ${esc(title)} · ${esc(selectedMonth)}</h1>${html}</html>`)}
    else alert('PDF માટે Android એપમાં ખોલો');
  }
  function diamondMatrix(items){
    const days=[...new Set(items.map(e=>e.date))].sort();
    const header='<thead><tr><th>તારીખ</th>'+grades.map(g=>`<th>${g}</th>`).join('')+'<th>કુલ</th></tr></thead>';
    let total=Array(7).fill(0);
    const body=days.map(d=>{
      const counts=grades.map((g,i)=>{const n=sum(items.filter(e=>e.date===d&&e.grade===g),'pieces');total[i]+=n;return n});
      return '<tr><td>'+esc(d)+'</td>'+counts.map(n=>`<td>${n||'–'}</td>`).join('')+`<td>${counts.reduce((a,b)=>a+b,0)}</td></tr>`;
    }).join('');
    const footer='<tfoot><tr><td>કુલ</td>'+total.map(n=>`<td>${n}</td>`).join('')+`<td>${total.reduce((a,b)=>a+b,0)}</td></tr></tfoot>`;
    return {html:`<table>${header}<tbody>${body}</tbody>${footer}</table>`,total};
  }
  function renderReports(){
    const diamonds=records('diamond'), hours=records('hour'), expenses=records('expense'), withdrawals=records('withdrawal');
    const diamondPay=sum(diamonds), hourPay=sum(hours), totalWithdrawal=sum(withdrawals);
    const monthly=diamondMatrix(diamonds);
    const allDiamondPieces=sum(entries.filter(e=>e.type==='diamond'),'pieces');
    if(window.Android?.syncWorkerTotalDiamonds) window.Android.syncWorkerTotalDiamonds(Math.round(allDiamondPieces));
    const rateTotals=grades.map(g=>{
      const gradeEntries=diamonds.filter(e=>e.grade===g),pieces=sum(gradeEntries,'pieces');
      return `<div class="line"><span>${g} · ${pieces} નંગ</span><b>${money(sum(gradeEntries))}</b></div>`;
    }).join('');
    const byDate=[...new Set(diamonds.map(e=>e.date))].sort().reverse().map(d=>panel(d,diamonds.filter(e=>e.date===d).map(e=>line(`${e.department} · ${e.grade} · ${e.pieces} નંગ × ${money(e.rate)}`,e.amount)).join('')+line('આ તારીખનો કુલ',sum(diamonds.filter(e=>e.date===d)),'green'))).join('');
    $('#monthly').innerHTML=panel('તારીખ પ્રમાણે A–G હિસાબ',`<div class="table-wrap">${monthly.html}</div>`)+panel('ભાવ પ્રમાણે આખા મહિનાનો કુલ',rateTotals+line('મહિનાની કુલ કમાણી',diamondPay,'green')+'<button class="action" id="diamondPdf">હીરાનો સંપૂર્ણ માસિક PDF કાઢો</button>');
    $('#daily').innerHTML=byDate||panel('રોજનો હીરાનો રિપોર્ટ','<p class="small">આ મહિને હીરાની એન્ટ્રી નથી.</p>');
    $('#diamonds > .panel:last-child').innerHTML='<h3>હીરાની કમાણી</h3>'+line('કુલ નંગ',sum(diamonds,'pieces'))+line('કુલ કમાણી',diamondPay,'green');
    const hourRows=hours.slice().sort((a,b)=>a.date.localeCompare(b.date)).map(e=>{const wd=sum(withdrawals.filter(w=>w.source==='hour'&&w.date===e.date));return `<tr><td>${esc(e.date)}</td><td>${e.hours}</td><td>${money(e.rate)}</td><td>${money(e.amount)}</td><td>${money(wd)}</td></tr>`}).join('');
    const hourWithdrawal=sum(withdrawals.filter(e=>e.source==='hour'));
    const hourTable=`<table><thead><tr><th>તારીખ</th><th>કલાક</th><th>દર</th><th>કમાણી</th><th>ઉપાડ</th></tr></thead><tbody>${hourRows}</tbody><tfoot><tr><td>કુલ</td><td>${sum(hours,'hours')}</td><td></td><td>${money(hourPay)}</td><td>${money(hourWithdrawal)}</td></tr></tfoot></table>`;
    $('#hoursReport').innerHTML=panel('કલાકનો માસિક રિપોર્ટ',`<div class="table-wrap">${hourTable}</div>`+line('કુલ કમાણી',hourPay,'green')+'<button class="action" id="hourPdf">કલાક / સમયનો PDF રિપોર્ટ કાઢો</button>');
    $('#salaryReport').innerHTML=panel('આખો રિપોર્ટ · પગાર અને ઉપાડ',line('હીરાની કમાણી',diamondPay)+line('કલાકની કમાણી',hourPay)+line('પૂરેપૂરો પગાર',diamondPay+hourPay,'green')+line('હીરાનો ઉપાડ',sum(withdrawals.filter(e=>e.source==='diamond')),'red')+line('કલાકનો ઉપાડ',sum(withdrawals.filter(e=>e.source==='hour')),'red')+line('મળવાનો બાકી પગાર',diamondPay+hourPay-totalWithdrawal));
    const sourceBlock=(source,label,pay)=>{const cost=sum(expenses.filter(e=>e.source===source));return panel(`${label} · ખર્ચનો હિસાબ`,line('કમાણી',pay)+line('ખર્ચ',cost,'red')+line('ખર્ચ સામે વધેલી રકમ',pay-cost,'green'))};
    $('#expenseReport').innerHTML=sourceBlock('diamond','હીરા',diamondPay)+sourceBlock('hour','કલાક',hourPay)+panel('ખર્ચની નોંધો',expenses.map(e=>line(`${e.date} · ${e.category}${e.note?' · '+e.note:''}`,e.amount)).join('')||'<p class="small">ખર્ચની નોંધ નથી.</p>');
    $('#diamondPdf').onclick=()=>printReport(monthly.html+`<p>${rateTotals.replaceAll('<div class="line">','<p>').replaceAll('</div>','</p>')}</p><p>કુલ હીરા: ${sum(diamonds,'pieces')} · કમાણી: ${money(diamondPay)} · ઉપાડ: ${money(sum(withdrawals.filter(e=>e.source==='diamond')))}</p>`,'હીરાનો માસિક રિપોર્ટ');
    $('#hourPdf').onclick=()=>printReport(hourTable+`<p>ઉપાડ: ${money(sum(withdrawals.filter(e=>e.source==='hour')))}</p>`,'કલાકનો માસિક રિપોર્ટ');
  }
  const monthBar=$$('#reports > .panel .line b');
  const updateMonth=()=>{monthBar[1].textContent=new Date(selectedMonth+'-01T12:00:00').toLocaleDateString('gu-IN',{month:'long',year:'numeric'});renderReports()};
  monthBar[0].onclick=()=>{const d=new Date(selectedMonth+'-01T12:00:00');d.setMonth(d.getMonth()-1);selectedMonth=isoLocal(d).slice(0,7);updateMonth()};
  monthBar[2].onclick=()=>{const d=new Date(selectedMonth+'-01T12:00:00');d.setMonth(d.getMonth()+1);selectedMonth=isoLocal(d).slice(0,7);updateMonth()};
  updateMonth();
})();
