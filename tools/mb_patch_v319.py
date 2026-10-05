from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

# New workers join the company immediately; no boss approval/pending stage.
old='''                    worker.put("birthday", safe(profile.getString("birthday")));
                    worker.put("active", false);'''
new='''                    worker.put("birthday", safe(profile.getString("birthday")));
                    worker.put("active", true);'''
if old not in j: raise SystemExit('join active flag block not found')
j=j.replace(old,new,1)

old='''                    worker.put("mode", selectedMode);
                    worker.put("removed", false);'''
new='''                    worker.put("mode", selectedMode);
                    final String joinMode = selectedMode;
                    worker.put("removed", false);'''
if old not in j: raise SystemExit('join mode block not found')
j=j.replace(old,new,1)

j=j.replace('workerJoinStatus.setText("રિક્વેસ્ટ મોકલાઈ રહી છે…");','workerJoinStatus.setText("કંપનીમાં જોડાઈ રહ્યા છો…");',1)

old='''                            currentCompanyName = companyName;
                            showWorkerPending(companyName);'''
new='''                            currentCompanyName = companyName;
                            currentCompanyId = companyId;
                            currentMode = joinMode;
                            grantRole(user, "worker", joinMode);'''
if old not in j: raise SystemExit('join success pending block not found')
j=j.replace(old,new,1)

# Boss list: remove the request/approve UI. Every non-removed worker is already joined;
# boss only gets the remove control.
pattern=r'''        if \(!active\) \{\n            TextView status = bodyText\("મંજૂરી બાકી"\);.*?        \} else \{\n            Button remove = secondaryButton\("કારીગર દૂર કરો"\);\n            remove\.setOnClickListener\(v -> confirmRemoveWorker\(workerId\)\);\n            card\.addView\(remove, fullWrap\(\)\);\n        \}'''
replacement='''        Button remove = secondaryButton("કારીગર દૂર કરો");
        remove.setOnClickListener(v -> confirmRemoveWorker(workerId));
        card.addView(remove, fullWrap());'''
j, n = re.subn(pattern, replacement, j, count=1, flags=re.S)
if n!=1: raise SystemExit(f'approve UI replace count={n}')

# If the boss removes a worker, that worker is immediately signed out on the next
# Firestore snapshot instead of being left on a re-join/pending screen.
old='''                if (removed) {
                    showWorkerJoin();
                    workerJoinStatus.setText("તમને કંપનીમાંથી દૂર કરવામાં આવ્યા છે. નવો કોડ નાખીને ફરી જોડાઈ શકો છો.");
                } else if (Boolean.TRUE.equals(snapshot.getBoolean("active"))) {'''
new='''                if (removed) {
                    signOut();
                    return;
                } else if (Boolean.TRUE.equals(snapshot.getBoolean("active"))) {'''
if old not in j: raise SystemExit('removed worker state block not found')
j=j.replace(old,new,1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 56', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.1.9'", b, count=1)
build.write_text(b)
print('MB Diamond Diary v3.1.9 direct join/removal logout applied')
