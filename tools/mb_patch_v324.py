from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
html=root/'app/src/main/assets/app.html'
j=java.read_text()
h=html.read_text()

# 1) Compact worker pages: remove the two global intro lines above every screen.
h, n = re.subn(r'<main><span class="badge">.*?</span><p class="intro">.*?</p>\s*', '<main>', h, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'global intro removal count={n}')

# 2) Worker decimal keyboard: hours and rate inputs must request a decimal-capable phone keyboard.
old_hour='<input id="hourValue" type="number" step="0.5" placeholder="જેમ કે 7.5">'
new_hour='<input id="hourValue" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" placeholder="જેમ કે 7.5">'
if old_hour not in h:
    raise SystemExit('hourValue input not found')
h=h.replace(old_hour,new_hour,1)

# Keep the finalized no-extra-dot-button design; use the mobile keyboard point for all rate fields.
h=re.sub(r'(<div id="diamondRateGrid"[\s\S]*?</div>)',
         lambda m: re.sub(r'<input type="text" inputmode="decimal"(?! pattern=)', '<input type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*"', m.group(1)),
         h, count=1)
h=h.replace('<input id="hourRateInput" type="text" inputmode="decimal" value="100">',
            '<input id="hourRateInput" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="100">',1)

# 3) Persist company name + code locally as soon as the worker joins, so the worker dashboard
# always restores them even if a Firestore read is delayed.
needle='''                            currentCompanyName = companyName;
                            currentCompanyId = companyId;
                            currentMode = joinMode;'''
rep='''                            currentCompanyName = companyName;
                            currentCompanyCode = code;
                            currentCompanyId = companyId;
                            currentMode = joinMode;'''
if needle not in j: raise SystemExit('join current company block not found')
j=j.replace(needle,rep,1)

needle='''.putString("worker_company_name", companyName)
                                    .putString("worker_mode", joinMode)'''
rep='''.putString("worker_company_name", companyName)
                                    .putString("worker_company_code", code)
                                    .putString("worker_mode", joinMode)'''
if needle not in j: raise SystemExit('join prefs block not found')
j=j.replace(needle,rep,1)

# Store bossUid too. This is a compatibility mirror for boss-side worker listing.
needle='''                    worker.put("companyId", companyId);
                    worker.put("companyName", companyName);
                    worker.put("companyCode", code);'''
rep='''                    worker.put("companyId", companyId);
                    worker.put("bossUid", companyId);
                    worker.put("companyName", companyName);
                    worker.put("companyCode", code);'''
if needle not in j: raise SystemExit('worker company fields block not found')
j=j.replace(needle,rep,1)

# 4) Worker state restore: restore the company code and repair compatibility fields on the worker doc.
needle='''                String localCompanyName = prefs.getString("worker_company_name", "");
                String localMode = prefs.getString("worker_mode", currentMode == null ? "" : currentMode);'''
rep='''                String localCompanyName = prefs.getString("worker_company_name", "");
                String localCompanyCode = prefs.getString("worker_company_code", "");
                String localMode = prefs.getString("worker_mode", currentMode == null ? "" : currentMode);'''
if needle not in j: raise SystemExit('worker local restore block not found')
j=j.replace(needle,rep,1)

# There are two local-fallback blocks (listener error and missing snapshot).
j=j.replace('''                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;''',
            '''                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;''', 2)

needle='''                currentCompanyName = safe(snapshot.getString("companyName"));
                currentCompanyId = safe(snapshot.getString("companyId"));'''
rep='''                currentCompanyName = safe(snapshot.getString("companyName"));
                currentCompanyCode = safe(snapshot.getString("companyCode"));
                if (currentCompanyCode.length() == 0 && localCompanyCode != null) currentCompanyCode = localCompanyCode;
                currentCompanyId = safe(snapshot.getString("companyId"));'''
if needle not in j: raise SystemExit('snapshot company restore block not found')
j=j.replace(needle,rep,1)

needle='''                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_mode").putBoolean("worker_joined", false).apply();'''
rep='''                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode").putBoolean("worker_joined", false).apply();'''
if needle not in j: raise SystemExit('removed worker prefs clear block not found')
j=j.replace(needle,rep,1)

needle='''                prefs.edit().putString("worker_company_id", currentCompanyId).putString("worker_company_name", currentCompanyName)
                    .putString("worker_mode", mode).putBoolean("worker_joined", true).apply();
                if (!Boolean.TRUE.equals(snapshot.getBoolean("active"))) {
                    Map<String,Object> activate = new HashMap<>();
                    activate.put("active", true);
                    activate.put("removed", false);
                    database.collection("workers").document(active.getUid()).set(activate, com.google.firebase.firestore.SetOptions.merge());
                }'''
rep='''                prefs.edit().putString("worker_company_id", currentCompanyId).putString("worker_company_name", currentCompanyName)
                    .putString("worker_company_code", currentCompanyCode).putString("worker_mode", mode).putBoolean("worker_joined", true).apply();
                Map<String,Object> repair = new HashMap<>();
                repair.put("bossUid", currentCompanyId);
                repair.put("companyId", currentCompanyId);
                repair.put("companyName", currentCompanyName);
                if (currentCompanyCode != null && currentCompanyCode.length() > 0) repair.put("companyCode", currentCompanyCode);
                repair.put("active", true);
                repair.put("removed", false);
                database.collection("workers").document(active.getUid()).set(repair, com.google.firebase.firestore.SetOptions.merge());'''
if needle not in j: raise SystemExit('worker repair block not found')
j=j.replace(needle,rep,1)

# 5) Leaving company must clear the persisted membership as well.
needle='''                currentCompanyName = null;
                currentCompanyCode = null;
                currentCompanyId = null;
                currentMode = null;'''
rep='''                currentCompanyName = null;
                currentCompanyCode = null;
                currentCompanyId = null;
                currentMode = null;
                getPreferences(MODE_PRIVATE).edit()
                    .remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode")
                    .putBoolean("worker_joined", false).apply();'''
if needle not in j: raise SystemExit('leave company clear block not found')
j=j.replace(needle,rep,1)

# 6) Worker dashboard company card: use local persisted company info immediately, then refresh from Firestore.
profile_method=re.search(r'''    private void pushWorkerProfileToPage\(\) \{.*?\n    \}\n\n    private void updateRoleInPage''', j, re.S)
if not profile_method: raise SystemExit('pushWorkerProfileToPage method not found')
profile_new=r'''    private void pushWorkerCompanyCard(String companyName, String companyCode) {
        if (page == null || page.getVisibility() != View.VISIBLE) return;
        try {
            org.json.JSONObject data = new org.json.JSONObject();
            data.put("companyName", companyName == null ? "" : companyName);
            data.put("companyCode", companyCode == null ? "" : companyCode);
            page.evaluateJavascript("window.mbWorkerProfile && window.mbWorkerProfile(" + data.toString() + ");", null);
        } catch (Exception ignored) {}
    }

    private void pushWorkerProfileToPage() {
        FirebaseUser user = auth == null ? null : auth.getCurrentUser();
        if (user == null || page == null || page.getVisibility() != View.VISIBLE || !"worker".equals(currentRole)) return;
        android.content.SharedPreferences prefs = getPreferences(MODE_PRIVATE);
        String localName = currentCompanyName == null ? "" : currentCompanyName;
        if (localName.length() == 0) localName = prefs.getString("worker_company_name", "");
        String localCode = currentCompanyCode == null ? "" : currentCompanyCode;
        if (localCode.length() == 0) localCode = prefs.getString("worker_company_code", "");
        final String fallbackName = localName == null ? "" : localName;
        final String fallbackCode = localCode == null ? "" : localCode;
        pushWorkerCompanyCard(fallbackName, fallbackCode);

        final String uid = user.getUid();
        database.collection("workers").document(uid).get()
            .addOnSuccessListener(worker -> {
                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !uid.equals(active.getUid()) || !"worker".equals(currentRole)) return;
                String companyName = worker.exists() ? safe(worker.getString("companyName")) : fallbackName;
                String companyCode = worker.exists() ? safe(worker.getString("companyCode")) : fallbackCode;
                if (companyName.length() == 0) companyName = fallbackName;
                if (companyCode.length() == 0) companyCode = fallbackCode;
                currentCompanyName = companyName;
                currentCompanyCode = companyCode;
                prefs.edit().putString("worker_company_name", companyName).putString("worker_company_code", companyCode).apply();
                pushWorkerCompanyCard(companyName, companyCode);
            })
            .addOnFailureListener(e -> pushWorkerCompanyCard(fallbackName, fallbackCode));
    }

    private void updateRoleInPage'''
j=j[:profile_method.start()]+profile_new+j[profile_method.end():]

# 7) Boss worker list: if the canonical companyId query is empty/blocked, fall back to bossUid,
# then companyCode. This repairs workers created during earlier versions without changing reports.
watch=re.search(r'''    private void watchPendingWorkers\(String companyId\) \{.*?\n    \}\n\n    private Map<String,Object> calculateMonthFromEntries''', j, re.S)
if not watch: raise SystemExit('watchPendingWorkers method not found')
watch_new=r'''    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
        String month = currentMonthKey();
        renderBossWorkers(docs, null, month);
        refreshBossDashboardFromEntries(docs, companyId, month);
    }

    private void loadBossWorkersByCompanyCode(String companyId) {
        if (currentCompanyCode == null || currentCompanyCode.length() == 0) {
            renderBossWorkerDocuments(new ArrayList<>(), companyId);
            return;
        }
        database.collection("workers").whereEqualTo("companyCode", currentCompanyCode).get()
            .addOnSuccessListener(snap -> renderBossWorkerDocuments(new ArrayList<>(snap.getDocuments()), companyId))
            .addOnFailureListener(e -> renderBossWorkerDocuments(new ArrayList<>(), companyId));
    }

    private void loadBossWorkersFallback(String companyId) {
        database.collection("workers").whereEqualTo("bossUid", companyId).get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadBossWorkersByCompanyCode(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersByCompanyCode(companyId));
    }

    private void watchPendingWorkers(String companyId) {
        clearBossWorkersListener();
        bossWorkersListener = database.collection("workers")
            .whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error != null || snapshots == null) {
                    loadBossWorkersFallback(companyId);
                    return;
                }
                List<DocumentSnapshot> docs = new ArrayList<>(snapshots.getDocuments());
                if (docs.isEmpty()) loadBossWorkersFallback(companyId);
                else renderBossWorkerDocuments(docs, companyId);
            });
    }

    private Map<String,Object> calculateMonthFromEntries'''
j=j[:watch.start()]+watch_new+j[watch.end():]

java.write_text(j)
html.write_text(h)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 61', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.3'", b, count=1)
build.write_text(b)
print('v3.2.3 worker company card, boss membership fallback, compact UI and decimal keyboard patch applied')
