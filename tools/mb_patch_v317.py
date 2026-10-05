from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')

html=root/'app/src/main/assets/app.html'
h=html.read_text()

# Use the existing third column in the diamond rate grid for a guaranteed decimal-point key.
h=h.replace('<span></span><b>B</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>B</b>')
h=h.replace('<span></span><b>C</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>C</b>')
h=h.replace('<span></span><b>D</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>D</b>')
h=h.replace('<span></span><b>E</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>E</b>')
h=h.replace('<span></span><b>F</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>F</b>')
h=h.replace('<span></span><b>G</b>', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button><b>G</b>')
# Final row A-G grid ends before the save controls; replace the last placeholder too.
h=h.replace('<span></span></div>\n<button id="saveDiamondRates"', '<button type="button" class="rate-dot" aria-label="પોઇન્ટ">.</button></div>\n<button id="saveDiamondRates"')

# Hour rate gets its own explicit decimal key as well.
needle='<input id="hourRateInput" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="100">'
if needle not in h:
    raise SystemExit('hourRateInput not found')
h=h.replace(needle, needle+'<button id="hourRateDot" type="button" class="choice rate-dot-hour">. પોઇન્ટ</button>', 1)

# Add compact styling. The visible dot button is a fallback for keyboards that hide decimal punctuation.
style='''\n.rate-dot{width:100%;height:38px;border:1px solid #d8dee8;border-radius:10px;background:#fff;color:#9b1e3b;font-weight:900;font-size:22px;line-height:1}.rate-dot-hour{margin-top:8px;padding:8px 14px;font-size:15px}\n'''
if '</style>' in h:
    h=h.replace('</style>', style+'</style>', 1)
else:
    h=style+h
html.write_text(h)

js=root/'app/src/main/assets/app.js'
s=js.read_text()
marker="""  $$('#diamondRateGrid input, #hourRateInput').forEach(el=>{\n    el.addEventListener('input',()=>{\n      settingsDirty=true;\n      let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,'');\n      const dot=t.indexOf('.');\n      if(dot>=0) t=t.slice(0,dot+1)+t.slice(dot+1).replace(/\\./g,'');\n      if(t!==el.value) el.value=t;\n    });\n    el.addEventListener('focus',()=>{try{el.select()}catch(_){} });\n  });"""
if marker not in s:
    raise SystemExit('rate listener block not found')
replacement=marker+"""\n\n  const insertRateDot = el => {\n    if(!el) return;\n    let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,'');\n    if(!t) t='0';\n    if(!t.includes('.')) t += '.';\n    el.value=t;\n    settingsDirty=true;\n    try{ el.focus(); const p=el.value.length; el.setSelectionRange(p,p); }catch(_){}\n    el.dispatchEvent(new Event('input',{bubbles:true}));\n  };\n  $$('#diamondRateGrid .rate-dot').forEach(btn=>{\n    btn.addEventListener('click',()=>{\n      const el=btn.previousElementSibling;\n      if(el && el.tagName==='INPUT') insertRateDot(el);\n    });\n  });\n  const hourRateDot=$('#hourRateDot');\n  if(hourRateDot) hourRateDot.addEventListener('click',()=>insertRateDot($('#hourRateInput')));\n"""
s=s.replace(marker,replacement,1)
js.write_text(s)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 54', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.1.7'", b, count=1)
build.write_text(b)
print('MB Diamond Diary v3.1.7 decimal point controls applied')
