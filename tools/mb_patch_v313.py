from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')

js=root/'app/src/main/assets/app.js'
s=js.read_text()
s=s.replace("  const val = el => Number(el?.value || 0);", "  const decimalNumber = raw => { const t=String(raw ?? '').trim().replace(',', '.').replace(/[^0-9.+-]/g,''); const n=Number(t); return Number.isFinite(n)?n:0; };\n  const val = el => decimalNumber(el?.value || 0);")
old="""  $$('#diamondRateGrid input, #hourRateInput').forEach(el=>{\n    el.addEventListener('input',()=>{settingsDirty=true;});\n    el.addEventListener('focus',()=>{try{el.select()}catch(_){} });\n  });"""
new="""  $$('#diamondRateGrid input, #hourRateInput').forEach(el=>{\n    el.addEventListener('input',()=>{\n      settingsDirty=true;\n      let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,'');\n      const dot=t.indexOf('.');\n      if(dot>=0) t=t.slice(0,dot+1)+t.slice(dot+1).replace(/\\./g,'');\n      if(t!==el.value) el.value=t;\n    });\n    el.addEventListener('focus',()=>{try{el.select()}catch(_){} });\n  });"""
if old not in s: raise SystemExit('rate listener block not found')
s=s.replace(old,new)
js.write_text(s)

html=root/'app/src/main/assets/app.html'
h=html.read_text()
for n in ['40','50','60','70','80','90','100']:
    h=h.replace(f'<input type="number" step="0.01" inputmode="decimal" value="{n}">', f'<input type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="{n}">')
h=h.replace('<input id="hourRateInput" type="number" step="0.01" inputmode="decimal" value="100">','<input id="hourRateInput" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="100">')
h=h.replace('<button id="saveDiamondRates" class="action" type="button">આ ડિપાર્ટમેન્ટના ભાવ સેવ કરો</button>', '<p class="hint">પૈસા/પોઇન્ટ માટે દશાંશ લખી શકો: 30.15 અથવા 30,15</p><button id="saveDiamondRates" class="action" type="button">આ ડિપાર્ટમેન્ટના ભાવ સેવ કરો</button>')
h=h.replace('<p class="hint">કલાક/ઓફિસ કામ પસંદ કરેલા કારીગર માટે આ દર સેવ થશે.</p>', '<p class="hint">દશાંશ દર પણ ચાલશે, જેમ કે 101.15. કલાક/ઓફિસ કામ પસંદ કરેલા કારીગર માટે આ દર સેવ થશે.</p>')
html.write_text(h)

java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()
marker='    private void syncWorkerSummaryFromWeb(String json) {'
helper=r'''    private String monthKeyForEntryDate(String date) {
        String d = safe(date).trim();
        if (d.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}")) return d.substring(0, 7);
        if (d.matches("[0-9]{2}/[0-9]{2}/[0-9]{4}")) return d.substring(6, 10) + "-" + d.substring(3, 5);
        if (d.matches("[0-9]{2}-[0-9]{2}-[0-9]{4}")) return d.substring(6, 10) + "-" + d.substring(3, 5);
        return "";
    }

    private void rebuildWorkerSummaryFromCloud(FirebaseUser requestedUser) {
        if (requestedUser == null || !"worker".equals(currentRole)) return;
        final String uid = requestedUser.getUid();
        database.collection("diaryEntries").document(uid).collection("items").get()
            .addOnSuccessListener(snap -> {
                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !uid.equals(active.getUid()) || !"worker".equals(currentRole)) return;
                Map<String,Map<String,Double>> totals = new HashMap<>();
                String mode = ("diamond".equals(currentMode) || "hour".equals(currentMode)) ? currentMode : "both";
                for (DocumentSnapshot d : snap.getDocuments()) {
                    String month = monthKeyForEntryDate(safe(d.getString("date")));
                    if (month.length() == 0) continue;
                    String type = safe(d.getString("type"));
                    String source = safe(d.getString("source"));
                    if ("diamond".equals(mode) && !("diamond".equals(type) || ("withdrawal".equals(type) && "diamond".equals(source)))) continue;
                    if ("hour".equals(mode) && !("hour".equals(type) || ("withdrawal".equals(type) && "hour".equals(source)))) continue;
                    Map<String,Double> one = totals.get(month);
                    if (one == null) {
                        one = new HashMap<>();
                        one.put("diamonds",0d); one.put("hours",0d); one.put("earnings",0d); one.put("withdrawal",0d);
                        totals.put(month,one);
                    }
                    if ("diamond".equals(type)) {
                        one.put("diamonds", one.get("diamonds") + number(d,"pieces"));
                        one.put("earnings", one.get("earnings") + number(d,"amount"));
                    } else if ("hour".equals(type)) {
                        one.put("hours", one.get("hours") + number(d,"hours"));
                        one.put("earnings", one.get("earnings") + number(d,"amount"));
                    } else if ("withdrawal".equals(type)) {
                        one.put("withdrawal", one.get("withdrawal") + number(d,"amount"));
                    }
                }
                Map<String,Object> monthly = new HashMap<>();
                for (Map.Entry<String,Map<String,Double>> e : totals.entrySet()) {
                    Map<String,Double> t=e.getValue();
                    double earnings=t.get("earnings"), withdrawal=t.get("withdrawal");
                    Map<String,Object> out=new HashMap<>();
                    out.put("diamonds",t.get("diamonds")); out.put("hours",t.get("hours")); out.put("earnings",earnings); out.put("withdrawal",withdrawal); out.put("remaining",earnings-withdrawal);
                    monthly.put(e.getKey(),out);
                }
                String nowMonth=new SimpleDateFormat("yyyy-MM",Locale.US).format(new Date());
                Map<String,Object> current = monthly.get(nowMonth) instanceof Map ? (Map<String,Object>) monthly.get(nowMonth) : new HashMap<>();
                double diamonds=mapNumber(current,"diamonds"), hours=mapNumber(current,"hours"), earnings=mapNumber(current,"earnings"), withdrawal=mapNumber(current,"withdrawal");
                Map<String,Object> update=new HashMap<>();
                update.put("summaryMonth",nowMonth); update.put("monthDiamonds",Math.round(diamonds)); update.put("monthHours",hours); update.put("monthEarnings",earnings); update.put("monthWithdrawal",withdrawal); update.put("monthRemaining",earnings-withdrawal); update.put("monthlySummaries",monthly);
                if ("diamond".equals(currentMode) || "hour".equals(currentMode)) update.put("mode",currentMode);
                update.put("summaryUpdatedAt",com.google.firebase.firestore.FieldValue.serverTimestamp());
                database.collection("workers").document(uid).set(update,com.google.firebase.firestore.SetOptions.merge());
            });
    }

'''
if marker not in j: raise SystemExit('summary marker not found')
j=j.replace(marker,helper+marker)
old=r'''    private void syncEntriesFromWeb(String json) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null) return;
        try {
            org.json.JSONArray arr = new org.json.JSONArray(json);
            for (int i=0; i<arr.length(); i++) {
                org.json.JSONObject o = arr.optJSONObject(i); if (o == null) continue;
                String id = o.optString("id", "");
                if (!id.matches("[A-Za-z0-9._-]{1,128}")) continue;
                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                database.collection("diaryEntries").document(user.getUid()).collection("items").document(id).set(m);
            }
        } catch (Exception ignored) {}
    }

    private void deleteEntryFromWeb(String id) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || id == null || !id.matches("[A-Za-z0-9._-]{1,128}")) return;
        database.collection("diaryEntries").document(user.getUid()).collection("items").document(id).delete();
    }
'''
new=r'''    private void syncEntriesFromWeb(String json) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null) return;
        try {
            org.json.JSONArray arr = new org.json.JSONArray(json);
            com.google.firebase.firestore.WriteBatch batch = database.batch();
            int writes = 0;
            for (int i=0; i<arr.length(); i++) {
                org.json.JSONObject o = arr.optJSONObject(i); if (o == null) continue;
                String id = o.optString("id", "");
                if (!id.matches("[A-Za-z0-9._-]{1,128}")) continue;
                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                DocumentReference ref = database.collection("diaryEntries").document(user.getUid()).collection("items").document(id);
                batch.set(ref, m); writes++;
            }
            if (writes == 0) return;
            batch.commit().addOnSuccessListener(v -> rebuildWorkerSummaryFromCloud(user));
        } catch (Exception ignored) {}
    }

    private void deleteEntryFromWeb(String id) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || id == null || !id.matches("[A-Za-z0-9._-]{1,128}")) return;
        database.collection("diaryEntries").document(user.getUid()).collection("items").document(id).delete()
            .addOnSuccessListener(v -> rebuildWorkerSummaryFromCloud(user));
    }
'''
if old not in j: raise SystemExit('entry sync block not found')
j=j.replace(old,new)
old2='''                pushCloudEntries();\n            });'''
new2='''                pushCloudEntries();\n                if ("worker".equals(currentRole)) rebuildWorkerSummaryFromCloud(active);\n            });'''
if old2 not in j: raise SystemExit('cloud snapshot block not found')
j=j.replace(old2,new2,1)
java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text().replace('versionCode 49','versionCode 50').replace("versionName '3.1.2'","versionName '3.1.3'")
build.write_text(b)
