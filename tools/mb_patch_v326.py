from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
html=root/'app/src/main/assets/app.html'
js=root/'app/src/main/assets/app.js'
j=java.read_text(); h=html.read_text(); s=js.read_text()

needle='''                currentCompanyName = safe(snapshot.getString("companyName"));
                currentCompanyCode = safe(snapshot.getString("companyCode"));
                if (currentCompanyCode.length() == 0 && localCompanyCode != null) currentCompanyCode = localCompanyCode;
                currentCompanyId = safe(snapshot.getString("companyId"));
                boolean removed = Boolean.TRUE.equals(snapshot.getBoolean("removed"));'''
rep='''                String snapshotCompanyName = safe(snapshot.getString("companyName"));
                String snapshotCompanyCode = safe(snapshot.getString("companyCode"));
                String snapshotCompanyId = safe(snapshot.getString("companyId"));
                boolean removed = Boolean.TRUE.equals(snapshot.getBoolean("removed"));
                if (removed) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode").putBoolean("worker_joined", false).apply();
                    signOut();
                    return;
                }
                if (snapshotCompanyId.length() == 0 || snapshotCompanyName.length() == 0) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").putBoolean("worker_joined", false).apply();
                    currentCompanyId = null;
                    currentCompanyName = null;
                    currentCompanyCode = null;
                    showWorkerJoin();
                    workerJoinStatus.setText("કંપની કોડ નાખીને કંપનીમાં જોડાઓ");
                    return;
                }
                currentCompanyName = snapshotCompanyName;
                currentCompanyCode = snapshotCompanyCode;
                if (currentCompanyCode.length() == 0 && localCompanyCode != null) currentCompanyCode = localCompanyCode;
                currentCompanyId = snapshotCompanyId;'''
if needle not in j: raise SystemExit('membership validation anchor not found')
j=j.replace(needle,rep,1)

dup='''                if (removed) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode").putBoolean("worker_joined", false).apply();
                    signOut();
                    return;
                }
                String mode = safe(snapshot.getString("mode"));'''
if dup not in j: raise SystemExit('duplicate removed block not found')
j=j.replace(dup,'                String mode = safe(snapshot.getString("mode"));',1)

old_grid='''<div id="diamondRateGrid" class="grid"><b>ગ્રેડ</b><b>દર ₹</b><b></b><b>A</b><input type="text" inputmode="decimal" value="40"><span></span><b>B</b><input type="text" inputmode="decimal" value="50"><span></span><b>C</b><input type="text" inputmode="decimal" value="60"><span></span><b>D</b><input type="text" inputmode="decimal" value="70"><span></span><b>E</b><input type="text" inputmode="decimal" value="80"><span></span><b>F</b><input type="text" inputmode="decimal" value="90"><span></span><b>G</b><input type="text" inputmode="decimal" value="100"><span></span></div>'''
new_grid='''<div id="diamondRateGrid" class="grid"><b>ગ્રેડ</b><b>દર ₹</b><b>પોઇન્ટ</b><b>A</b><input type="text" inputmode="decimal" value="40"><button type="button" class="rate-dot">.</button><b>B</b><input type="text" inputmode="decimal" value="50"><button type="button" class="rate-dot">.</button><b>C</b><input type="text" inputmode="decimal" value="60"><button type="button" class="rate-dot">.</button><b>D</b><input type="text" inputmode="decimal" value="70"><button type="button" class="rate-dot">.</button><b>E</b><input type="text" inputmode="decimal" value="80"><button type="button" class="rate-dot">.</button><b>F</b><input type="text" inputmode="decimal" value="90"><button type="button" class="rate-dot">.</button><b>G</b><input type="text" inputmode="decimal" value="100"><button type="button" class="rate-dot">.</button></div>'''
if old_grid not in h: raise SystemExit('diamond rate grid not found')
h=h.replace(old_grid,new_grid,1)

old_hour='<input id="hourRateInput" type="text" inputmode="decimal" value="100">'
if old_hour not in h: raise SystemExit('hourRateInput not found')
h=h.replace(old_hour, old_hour+'<button id="hourRateDot" type="button" class="choice rate-dot-hour">. પોઇન્ટ</button>',1)

old_value='<input id="hourValue" type="text" inputmode="decimal" placeholder="જેમ કે 7.5">'
if old_value not in h: raise SystemExit('hourValue not found')
h=h.replace(old_value,old_value+'<button id="hourValueDot" type="button" class="choice rate-dot-hour">. પોઇન્ટ</button>',1)

style='''.rate-dot{width:100%;min-height:38px;border:1px solid #d8dee8;border-radius:10px;background:#fff;color:#9b1e3b;font-weight:900;font-size:22px;line-height:1}.rate-dot-hour{margin:8px 0 4px;padding:8px 14px;font-size:15px}
'''
if '.rate-dot{' not in h:
    if '</style>' not in h: raise SystemExit('style close not found')
    h=h.replace('</style>',style+'</style>',1)

marker="""  $$('#diamondRateGrid input, #hourRateInput').forEach(el=>{
    el.addEventListener('input',()=>{
      settingsDirty=true;
      let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,'');
      const dot=t.indexOf('.');
      if(dot>=0) t=t.slice(0,dot+1)+t.slice(dot+1).replace(/\./g,'');
      if(t!==el.value) el.value=t;
    });
    el.addEventListener('focus',()=>{try{el.select()}catch(_){} });
  });"""
if marker not in s: raise SystemExit('rate listener marker not found')
helper=marker+"""

  const insertDecimalPoint = el => {
    if(!el) return;
    let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,'');
    if(!t) t='0';
    if(!t.includes('.')) t += '.';
    el.value=t;
    settingsDirty=true;
    try{el.focus(); const p=el.value.length; el.setSelectionRange(p,p)}catch(_){}
    el.dispatchEvent(new Event('input',{bubbles:true}));
  };
  $$('#diamondRateGrid .rate-dot').forEach(btn=>btn.addEventListener('click',()=>insertDecimalPoint(btn.previousElementSibling)));
  const hourRateDot=$('#hourRateDot'); if(hourRateDot) hourRateDot.addEventListener('click',()=>insertDecimalPoint($('#hourRateInput')));
  const hourValueDot=$('#hourValueDot'); if(hourValueDot) hourValueDot.addEventListener('click',()=>{
    const el=$('#hourValue'); if(!el)return; let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,''); if(!t)t='0'; if(!t.includes('.'))t+='.'; el.value=t; try{el.focus();const p=el.value.length;el.setSelectionRange(p,p)}catch(_){}; el.dispatchEvent(new Event('input',{bubbles:true}));
  });
"""
s=s.replace(marker,helper,1)

java.write_text(j); html.write_text(h); js.write_text(s)
b=root/'app/build.gradle'; t=b.read_text(); t=re.sub(r'versionCode\\s+\\d+','versionCode 63',t,1); t=re.sub(r"versionName\\s+'[^']+'","versionName '3.2.5'",t,1); b.write_text(t)
print('v3.2.5 membership validation and explicit decimal-point controls applied')
