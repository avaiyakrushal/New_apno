from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 77","versionCode 78").replace("versionName '3.2.19'","versionName '3.2.20'")
gradle.write_text(s)

html=root/"app/src/main/assets/app.html"
s=html.read_text()

old="""document.getElementById('approveWorker').onclick = () => {
  const uid = document.getElementById('workerUid').value.trim();
  const name = document.getElementById('workerName').value.trim();
  const mode = document.getElementById('workerMode').value;
  if (!/^[A-Za-z0-9]{20,128}$/.test(uid)) { alert('માન્ય કારીગર ID લખો'); return; }
  window.Android?.approveWorker(uid, name, mode);
};
"""
new="""const approveWorker=document.getElementById('approveWorker');
if(approveWorker) approveWorker.onclick = () => {
  const uidEl=document.getElementById('workerUid');
  const nameEl=document.getElementById('workerName');
  const modeEl=document.getElementById('workerMode');
  if(!uidEl||!modeEl)return;
  const uid = uidEl.value.trim();
  const name = nameEl ? nameEl.value.trim() : '';
  const mode = modeEl.value;
  if (!/^[A-Za-z0-9]{20,128}$/.test(uid)) { alert('માન્ય કારીગર ID લખો'); return; }
  window.Android?.approveWorker(uid, name, mode);
};
"""
if old not in s:
    raise SystemExit("approveWorker crash block not found")
s=s.replace(old,new)

# Make worker company label resilient: never overwrite a valid native value with blanks.
old2="""window.mbWorkerProfile = data => {
  data=data||{};
  const company=document.getElementById('workerCompanyName');
  const code=document.getElementById('workerCompanyCode');
  if(company) company.textContent=data.companyName||'કંપની';
  if(code) code.textContent=data.companyCode?`કોડ: ${data.companyCode}`:'કોડ: —';
};
"""
new2="""window.mbWorkerProfile = data => {
  data=data||{};
  const company=document.getElementById('workerCompanyName');
  const code=document.getElementById('workerCompanyCode');
  const companyName=String(data.companyName||'').trim();
  const companyCode=String(data.companyCode||'').trim();
  if(company && companyName) company.textContent=companyName;
  if(code && companyCode) code.textContent=`કોડ: ${companyCode}`;
};
"""
if old2 in s:
    s=s.replace(old2,new2)

html.write_text(s)
print("v3.2.20 UI/navigation/company crash fix applied")
