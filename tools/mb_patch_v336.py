from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
html=root/'app/src/main/assets/app.html'
h=html.read_text()

# v3.2.14 report-tab stability:
# async role/profile refreshes must not force Expense back to Hira/Hours.
old='''  if(worker && workMode !== 'both'){
    const target = workMode === 'hour' ? 'hoursReport' : 'diamonds';
    document.querySelectorAll('.report').forEach(r=>r.classList.toggle('active',r.id===target));
    document.querySelectorAll('[data-report]').forEach(x=>x.classList.toggle('on',x.dataset.report===target));
  }'''
new='''  if(worker && workMode !== 'both'){
    const current = window.__mbActiveReport || document.querySelector('.report.active')?.id || '';
    const currentAllowed = !!reportRules[current];
    if(!currentAllowed){
      const target = workMode === 'hour' ? 'hoursReport' : 'diamonds';
      window.__mbActiveReport = target;
      document.querySelectorAll('.report').forEach(r=>r.classList.toggle('active',r.id===target));
      document.querySelectorAll('[data-report]').forEach(x=>x.classList.toggle('on',x.dataset.report===target));
    }
  }'''
if old not in h: raise SystemExit('worker report role-reset block not found')
h=h.replace(old,new,1)

old='''document.querySelectorAll('[data-report]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.report').forEach(s=>s.classList.toggle('active',s.id===b.dataset.report));document.querySelectorAll('[data-report]').forEach(x=>x.classList.toggle('on',x===b))});'''
new='''window.__mbActiveReport = document.querySelector('.report.active')?.id || 'diamonds';
document.querySelectorAll('[data-report]').forEach(b=>b.onclick=()=>{
  const target=b.dataset.report;
  window.__mbActiveReport=target;
  document.querySelectorAll('.report').forEach(s=>s.classList.toggle('active',s.id===target));
  document.querySelectorAll('[data-report]').forEach(x=>x.classList.toggle('on',x===b));
});'''
if old not in h: raise SystemExit('report click handler not found')
h=h.replace(old,new,1)

html.write_text(h)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 72', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.14'", b, count=1)
build.write_text(b)
print('v3.2.14 stable report tab selection applied')
