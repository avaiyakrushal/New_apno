from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 85","versionCode 86").replace("versionName '3.2.27'","versionName '3.2.28'")
p.write_text(s)

p=root/"app/src/main/assets/app.html"
s=p.read_text()

repls={
".report-preview-overlay{display:none;position:fixed;inset:0;z-index:1000;background:#f3f5f9;overflow:auto;padding:10px 10px 22px}":
".report-preview-overlay{display:none;position:fixed;inset:0;z-index:1000;background:#eef1f6;overflow:hidden;padding:0}",
".report-preview-card{max-width:600px;margin:0 auto;background:#fff;border-radius:18px;padding:12px;box-shadow:0 8px 28px #14243b22}":
".report-preview-card{width:100%;height:100%;margin:0;background:#eef1f6;border-radius:0;padding:0;box-shadow:none;display:flex;flex-direction:column}",
".report-preview-head{position:sticky;top:0;z-index:2;background:#fff;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:4px 0 10px;border-bottom:1px solid #edf0f4}":
".report-preview-head{position:sticky;top:0;z-index:5;background:#8f1735;color:#fff;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:14px 12px;border-bottom:0;box-shadow:0 2px 8px #0002}",
".report-preview-head button{border:1px solid #dfe4ec;background:#fff;border-radius:10px;padding:8px 10px;font-weight:800}.report-preview-tools{display:flex;gap:6px;align-items:center}.report-preview-tools button{min-width:38px;padding:8px}.report-preview-zoom{font-size:12px;font-weight:900;min-width:44px;text-align:center}.report-preview-sheet{transform-origin:top left;transition:transform .12s ease;width:100%}":
".report-preview-head button{border:1px solid #ffffff55;background:#ffffff18;color:#fff;border-radius:12px;padding:9px 11px;font-weight:900}.report-preview-tools{display:flex;gap:6px;align-items:center}.report-preview-tools button{min-width:38px;padding:8px}.report-preview-zoom{font-size:12px;font-weight:900;min-width:44px;text-align:center;color:#fff}.report-preview-sheet{transform-origin:top left;transition:transform .12s ease;width:100%;padding:14px;box-sizing:border-box}.report-preview-month{background:#fff;border-bottom:1px solid #dfe4ec;padding:12px 14px;text-align:center;font-size:18px;font-weight:900;color:#17243a}",
".report-preview-body{padding-top:10px}":
".report-preview-body{padding:0;overflow:auto;flex:1;background:#eef1f6}",
".report-preview-body table{min-width:0!important;width:100%!important;table-layout:fixed}":
".report-preview-body table{min-width:0!important;width:100%!important;table-layout:fixed;background:#fff;border-collapse:collapse;box-shadow:0 2px 10px #14243b16}",
".report-preview-body th,.report-preview-body td{font-size:9px!important;padding:6px 1px!important;white-space:nowrap;overflow:hidden}":
".report-preview-body th,.report-preview-body td{font-size:11px!important;padding:10px 3px!important;white-space:nowrap;overflow:hidden;border:1px solid #dde2ea;text-align:center}",
".report-preview-actions{display:grid;grid-template-columns:1fr;gap:8px;margin-top:14px}":
".report-preview-actions{display:grid;grid-template-columns:1fr;gap:8px;padding:10px 14px 14px;background:#fff;border-top:1px solid #dfe4ec;margin-top:0}"
}
for a,b in repls.items():
    if a not in s: raise SystemExit("css anchor missing: "+a[:60])
    s=s.replace(a,b,1)

# Full-screen report specific cosmetics
extra="""
.report-preview-sheet h2{margin:4px 0 12px;font-size:18px;text-align:center;color:#17243a}
.report-preview-sheet .panel{border-radius:0;box-shadow:none;border:0;background:#fff;margin:12px 0 0}
.report-preview-sheet table thead th{background:#2f7f38;color:#fff;font-weight:900}
.report-preview-sheet table tfoot td{background:#16a51f;color:#fff;font-weight:900}
.report-preview-sheet .line{background:#fff}
"""
s=s.replace(".report-preview-actions .action{margin-top:0}",".report-preview-actions .action{margin-top:0}"+extra,1)
p.write_text(s)

p=root/"app/src/main/assets/app.js"
s=p.read_text()

old="""    overlay.innerHTML=`<div class="report-preview-card"><div class="report-preview-head"><button id="reportPreviewClose" type="button">← પાછા</button><b id="reportPreviewTitle">રિપોર્ટ</b><div class="report-preview-tools"><button id="reportZoomOut" type="button">−</button><span id="reportZoomLabel" class="report-preview-zoom">100%</span><button id="reportZoomIn" type="button">＋</button></div></div><div id="reportPreviewBody" class="report-preview-body"><div id="reportPreviewSheet" class="report-preview-sheet"></div></div><div class="report-preview-actions"><button id="reportPreviewPrint" class="action" type="button">PDF સેવ / પ્રિન્ટ કરો</button></div></div>`;
"""
new="""    overlay.innerHTML=`<div class="report-preview-card"><div class="report-preview-head"><button id="reportPreviewClose" type="button">← પાછા</button><b id="reportPreviewTitle">રિપોર્ટ</b><div class="report-preview-tools"><button id="reportZoomOut" type="button">−</button><span id="reportZoomLabel" class="report-preview-zoom">100%</span><button id="reportZoomIn" type="button">＋</button></div></div><div id="reportPreviewMonth" class="report-preview-month"></div><div id="reportPreviewBody" class="report-preview-body"><div id="reportPreviewSheet" class="report-preview-sheet"></div></div><div class="report-preview-actions"><button id="reportPreviewPrint" class="action" type="button">PDF સેવ / પ્રિન્ટ કરો</button></div></div>`;
"""
if old not in s: raise SystemExit("overlay html anchor missing")
s=s.replace(old,new,1)

old="""    const heading=`MB ડાયમંડ ડાયરી · ${esc(title)} · ${esc(selectedMonth)}`;
    $('#reportPreviewTitle').textContent=title;
    const sheet=$('#reportPreviewSheet'); if(sheet) sheet.innerHTML=`<h2>${heading}</h2>${html}`;
"""
new="""    const monthText=new Date(selectedMonth+'-01T12:00:00').toLocaleDateString('gu-IN',{month:'long',year:'numeric'});
    const heading=`MB ડાયમંડ ડાયરી · ${esc(title)}`;
    $('#reportPreviewTitle').textContent=title;
    const monthEl=$('#reportPreviewMonth'); if(monthEl) monthEl.textContent=monthText;
    const sheet=$('#reportPreviewSheet'); if(sheet) sheet.innerHTML=`<h2>${heading}</h2>${html}`;
"""
if old not in s: raise SystemExit("printReport heading anchor missing")
s=s.replace(old,new,1)

# Rename buttons to "tap to open whole screen" wording.
s=s.replace("સંપૂર્ણ માસિક રિપોર્ટ ખોલો","માસિક રિપોર્ટ આખી સ્ક્રીનમાં જુઓ")
p.write_text(s)

print("v3.2.28 full-screen monthly report UI applied")
