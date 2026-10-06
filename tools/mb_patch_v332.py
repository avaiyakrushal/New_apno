from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

# Sheth dashboard: make both worker department lists explicit and visible on selection.
j=j.replace('Button diamondFilter = primaryButton("હીરા ડિપાર્ટમેન્ટ");',
            'Button diamondFilter = primaryButton("હીરા કારીગર · " + diamondWorkers.size());',1)
j=j.replace('Button hourFilter = secondaryButton("કલાક ડિપાર્ટમેન્ટ");',
            'Button hourFilter = secondaryButton("કલાક કારીગર · " + hourWorkers.size());',1)

# Department title makes it clear that the whole worker list is below.
j=j.replace('("diamond".equals(mode) ? "હીરા ડિપાર્ટમેન્ટ" : "કલાક ડિપાર્ટમેન્ટ") + " · " + workers.size() + " કારીગર"',
            '("diamond".equals(mode) ? "હીરા કારીગરોની લિસ્ટ" : "કલાક કારીગરોની લિસ્ટ") + " · " + workers.size() + " કારીગર"',1)

# Every visible worker card must have a remove button in both departments.
if 'Button remove = secondaryButton("કારીગર દૂર કરો");' in j:
    j=j.replace('Button remove = secondaryButton("કારીગર દૂર કરો");',
                'Button remove = secondaryButton("રીમુવ કારીગર");',1)
elif 'Button remove = secondaryButton("રીમુવ કારીગર");' not in j:
    raise SystemExit('worker remove button not found')

# The worker row already renders name/mobile/birthday/work totals. Keep inactive-but-not-removed
# workers visible so the boss can still remove them instead of silently losing them from the list.
old='''        boolean active = Boolean.TRUE.equals(worker.getBoolean("active"));
        boolean removed = Boolean.TRUE.equals(worker.getBoolean("removed"));
        if (removed) return;'''
new='''        boolean active = Boolean.TRUE.equals(worker.getBoolean("active"));
        boolean removed = Boolean.TRUE.equals(worker.getBoolean("removed"));
        if (removed) return;'''
if old not in j:
    raise SystemExit('worker visibility block not found')
j=j.replace(old,new,1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 68', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.10'", b, count=1)
build.write_text(b)
print('v3.2.10 Sheth Hira/Kalak full worker lists with remove button applied')
