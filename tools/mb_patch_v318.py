from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')

html=root/'app/src/main/assets/app.html'
h=html.read_text()

# Final UX: no separate point buttons. Hira A-G and Kalak rate use the phone's decimal keyboard.
h=re.sub(r'<button type="button" class="rate-dot" aria-label="પોઇન્ટ">\.</button>', '<span></span>', h)
h=h.replace('<button id="hourRateDot" type="button" class="choice rate-dot-hour">. પોઇન્ટ</button>', '')
h=re.sub(r'\n\.rate-dot\{[^\n]*\}\.rate-dot-hour\{[^\n]*\}\n', '\n', h)

# Force decimal keyboard semantics on every rate field.
h=re.sub(r'(<div id="diamondRateGrid"[\s\S]*?</div>)', lambda m: re.sub(r'<input\s+type="text"\s+inputmode="decimal"\s+pattern="\[0-9\]\*\[\.,\]\?\[0-9\]\*"', '<input type="text" inputmode="decimal"', m.group(1)), h, count=1)
h=h.replace('<input id="hourRateInput" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="100">', '<input id="hourRateInput" type="text" inputmode="decimal" value="100">')
html.write_text(h)

js=root/'app/src/main/assets/app.js'
s=js.read_text()
# Remove v3.1.7 helper/listeners for separate dot controls; keep decimal parsing/listener from v3.1.3.
s=re.sub(r'''\n\s*const insertRateDot = el => \{[\s\S]*?if\(hourRateDot\) hourRateDot\.addEventListener\('click',\(\)=>insertRateDot\(\$\('#hourRateInput'\)\)\);\n''', '\n', s, count=1)
js.write_text(s)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 55', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.1.8'", b, count=1)
build.write_text(b)
print('MB Diamond Diary v3.1.8 phone-keyboard decimal input applied')
