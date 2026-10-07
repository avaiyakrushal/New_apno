from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 82","versionCode 83").replace("versionName '3.2.24'","versionName '3.2.25'")
p.write_text(s)

p=root/"app/src/main/assets/app.html"
s=p.read_text()
old=".report-preview-head button{border:1px solid #dfe4ec;background:#fff;border-radius:10px;padding:8px 10px;font-weight:800}"
new=old+".report-preview-tools{display:flex;gap:6px;align-items:center}.report-preview-tools button{min-width:38px;padding:8px}.report-preview-zoom{font-size:12px;font-weight:900;min-width:44px;text-align:center}.report-preview-sheet{transform-origin:top left;transition:transform .12s ease;width:100%}"
if old not in s: raise SystemExit("preview css anchor missing")
s=s.replace(old,new,1)
p.write_text(s)

p=root/"app/src/main/assets/app.js"
s=p.read_text()

old="""    overlay.innerHTML=`<div class="report-preview-card"><div class="report-preview-head"><button id="reportPreviewClose" type="button">← પાછા</button><b id="reportPreviewTitle">રિપોર્ટ</b></div><div id="reportPreviewBody" class="report-preview-body"></div><div class="report-preview-actions"><button id="reportPreviewPrint" class="action" type="button">PDF સેવ / પ્રિન્ટ કરો</button></div></div>`;
    document.body.appendChild(overlay);
    $('#reportPreviewClose').onclick=closeReportPreview;
"""
new="""    overlay.innerHTML=`<div class="report-preview-card"><div class="report-preview-head"><button id="reportPreviewClose" type="button">← પાછા</button><b id="reportPreviewTitle">રિપોર્ટ</b><div class="report-preview-tools"><button id="reportZoomOut" type="button">−</button><span id="reportZoomLabel" class="report-preview-zoom">100%</span><button id="reportZoomIn" type="button">＋</button></div></div><div id="reportPreviewBody" class="report-preview-body"><div id="reportPreviewSheet" class="report-preview-sheet"></div></div><div class="report-preview-actions"><button id="reportPreviewPrint" class="action" type="button">PDF સેવ / પ્રિન્ટ કરો</button></div></div>`;
    document.body.appendChild(overlay);
    let zoom=1;
    const applyZoom=()=>{const sheet=$('#reportPreviewSheet');if(sheet)sheet.style.transform=`scale(${zoom})`;const body=$('#reportPreviewBody');if(body){body.style.width=`${100/zoom}%`;body.style.minHeight=`${Math.ceil((sheet?.scrollHeight||0)*zoom)}px`;}const label=$('#reportZoomLabel');if(label)label.textContent=`${Math.round(zoom*100)}%`;};
    $('#reportPreviewClose').onclick=closeReportPreview;
    $('#reportZoomOut').onclick=()=>{zoom=Math.max(.7,Math.round((zoom-.1)*10)/10);applyZoom();};
    $('#reportZoomIn').onclick=()=>{zoom=Math.min(1.8,Math.round((zoom+.1)*10)/10);applyZoom();};
    overlay._resetZoom=()=>{zoom=1;applyZoom();};
"""
if old not in s: raise SystemExit("preview overlay block missing")
s=s.replace(old,new,1)

old="""    $('#reportPreviewBody').innerHTML=`<h2>${heading}</h2>${html}`;
    pendingReportDocument="""
new="""    const sheet=$('#reportPreviewSheet'); if(sheet) sheet.innerHTML=`<h2>${heading}</h2>${html}`;
    pendingReportDocument="""
if old not in s: raise SystemExit("preview body missing")
s=s.replace(old,new,1)
s=s.replace("    document.body.style.overflow='hidden';\n    overlay.scrollTo(0,0);","    document.body.style.overflow='hidden';\n    if(overlay._resetZoom) overlay._resetZoom();\n    overlay.scrollTo(0,0);",1)

s=s.replace('id="diamondPdf">હીરાનો માસિક PDF કાઢો','id="diamondFullReport">સંપૂર્ણ માસિક રિપોર્ટ ખોલો',1)
s=s.replace('id="hourPdf">કલાકનો PDF રિપોર્ટ કાઢો','id="hourFullReport">સંપૂર્ણ માસિક રિપોર્ટ ખોલો',1)

old="""    const diamondPdf=$('#diamondPdf');
    if(diamondPdf) diamondPdf.onclick=()=>printReport(`<h2>${esc(reportLabel)}</h2>${monthly.html}<p>${rateTotals.replaceAll('<div class="line">','<p>').replaceAll('</div>','</p>')}</p><p>કુલ હીરા: ${sum(diamonds,'pieces')} · કમાણી: ${money(diamondPay)} · ઉપાડ: ${money(diamondWithdrawalAmount)} · ઉપાડ બાદ: ${money(diamondAfterWithdrawal)}</p>`,`${reportLabel} · હીરાનો માસિક રિપોર્ટ`);
"""
new="""    const diamondFullReport=$('#diamondFullReport');
    if(diamondFullReport) diamondFullReport.onclick=()=>printReport(`<h2>${esc(reportLabel)}</h2>${monthly.html}<div class="panel"><h3>ભાવ પ્રમાણે મહિનાનો કુલ</h3>${rateTotals}${line('કુલ કમાણી',diamondPay,'green')}${line('ઉપાડ',diamondWithdrawalAmount,'red')}${line('ઉપાડ બાદ',diamondAfterWithdrawal,diamondAfterWithdrawal<0?'red':'green')}</div>`,`${reportLabel} · હીરાનો માસિક રિપોર્ટ`);
"""
if old not in s: raise SystemExit("diamond handler missing")
s=s.replace(old,new,1)

old="""    const hourPdf=$('#hourPdf');
    if(hourPdf) hourPdf.onclick=()=>printReport(hourTable+`<p>ઉપાડ: ${money(hourWithdraw)} · બાકી: ${money(hourPay-hourWithdraw)}</p>`,'કલાકનો રિપોર્ટ');
"""
new="""    const hourFullReport=$('#hourFullReport');
    if(hourFullReport) hourFullReport.onclick=()=>printReport(hourTable+`<div class="panel">${line('કુલ કમાણી',hourPay,'green')}${line('ઉપાડ',hourWithdraw,'red')}${line('મળવાનો બાકી',hourPay-hourWithdraw,(hourPay-hourWithdraw)<0?'red':'green')}</div>`,'કલાકનો માસિક રિપોર્ટ');
"""
if old not in s: raise SystemExit("hour handler missing")
s=s.replace(old,new,1)
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()
s=s.replace("    private ListenerRegistration bossCodeMembersListener;\n","    private ListenerRegistration bossCodeMembersListener;\n    private ListenerRegistration bossUsersListener;\n",1)

pattern=r'''        bossWorkersListener = database\.collection\("workers"\)\n            \.whereEqualTo\("companyId", companyId\)\n            \.addSnapshotListener\(\(snapshots, error\) -> \{.*?            \}\);'''
replacement='''        bossWorkersListener = database.collection("workers")
            .whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> refreshBossWorkersCanonical(companyId));'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit("boss worker listener block missing")

anchor="""        refreshBossWorkersCanonical(companyId);
    }

    private Map<String,Object> calculateMonthFromEntries"""
insert="""        bossUsersListener = database.collection("users").whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });

        refreshBossWorkersCanonical(companyId);
    }

    private Map<String,Object> calculateMonthFromEntries"""
if anchor not in s: raise SystemExit("boss users listener anchor missing")
s=s.replace(anchor,insert,1)

clear='        if (bossCodeMembersListener != null) { bossCodeMembersListener.remove(); bossCodeMembersListener = null; }\n'
if clear not in s: raise SystemExit("clear listener anchor missing")
s=s.replace(clear,clear+'        if (bossUsersListener != null) { bossUsersListener.remove(); bossUsersListener = null; }\n',1)
p.write_text(s)
print("v3.2.25 fixes applied")
