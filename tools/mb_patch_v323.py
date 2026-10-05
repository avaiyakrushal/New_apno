from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

# 1) Login: make company-code join direct and remove request/pending wording.
j=j.replace('workerJoinButton = primaryButton("રિક્વેસ્ટ મોકલો");','workerJoinButton = primaryButton("કંપનીમાં જોડાઓ");',1)
j=j.replace('workerJoinStatus.setText("રિક્વેસ્ટ મોકલી શકાયી નથી. ફરી પ્રયાસ કરો.");','workerJoinStatus.setText("કંપનીમાં જોડાઈ શકાયું નથી. ફરી પ્રયાસ કરો.");')

# 2) Exact Super Admin account; all other users follow normal role routing.
old_route=re.search(r'''    private void routeSignedInUser\(FirebaseUser user\) \{.*?\n    \}\n\n    private void routeRegularUser''', j, re.S)
if not old_route: raise SystemExit('routeSignedInUser block not found')
new_route='''    private void routeSignedInUser(FirebaseUser user) {
        hideAll();
        touchLastActive(user);
        registerPushToken(user);
        if ("maniyajitesh56@gmail.com".equalsIgnoreCase(safe(user.getEmail()))) {
            showAdminDashboard();
            return;
        }
        routeRegularUser(user);
    }

    private void routeRegularUser'''
j=j[:old_route.start()]+new_route+j[old_route.end():]

# 3) Super Admin shows only the three finalized totals.
admin=re.search(r'''    private void loadAdminDashboard\(\) \{.*?\n    \}\n\n    @Override protected void onStart''', j, re.S)
if not admin: raise SystemExit('loadAdminDashboard block not found')
admin_new='''    private void loadAdminDashboard() {
        if (adminStats == null || adminCompanies == null) return;
        adminStats.setText("ડેટા લોડ થઈ રહ્યો છે…");
        adminCompanies.removeAllViews();
        database.collection("users").get().addOnSuccessListener(usersSnap -> {
            database.collection("companies").get().addOnSuccessListener(companiesSnap -> {
                database.collection("workers").get().addOnSuccessListener(workersSnap -> {
                    int workers = 0;
                    for (DocumentSnapshot workerDoc : workersSnap.getDocuments()) {
                        if (!Boolean.TRUE.equals(workerDoc.getBoolean("removed"))) workers++;
                    }
                    adminStats.setText(
                        "કુલ Companies: " + companiesSnap.size() +
                        "\\nકુલ Workers: " + workers +
                        "\\nકુલ Users: " + usersSnap.size()
                    );
                    adminCompanies.removeAllViews();
                }).addOnFailureListener(e -> adminStats.setText("Workers ડેટા લોડ થઈ શક્યો નથી."));
            }).addOnFailureListener(e -> adminStats.setText("Companies ડેટા લોડ થઈ શક્યો નથી."));
        }).addOnFailureListener(e -> adminStats.setText("Users ડેટા લોડ થઈ શક્યો નથી."));
    }

    @Override protected void onStart'''
j=j[:admin.start()]+admin_new+j[admin.end():]

# 4) Worker state: never bounce a joined worker to request/pending due to transient listener errors.
worker_state=re.search(r'''    private void showWorkerState\(FirebaseUser user\) \{.*?\n    \}\n\n    private void showWorkerJoin''', j, re.S)
if not worker_state: raise SystemExit('showWorkerState block not found')
worker_new='''    private void showWorkerState(FirebaseUser user) {
        if (user == null) return;
        if (user.getUid().equals(watchingUid) && workerListener != null) {
            if ("worker".equals(currentRole) && ("hour".equals(currentMode) || "diamond".equals(currentMode)))
                grantRole(user, "worker", currentMode);
            return;
        }
        hideAll();
        page.setVisibility(View.GONE);
        clearWorkerListener();
        watchingUid = user.getUid();
        workerListener = database.collection("workers").document(watchingUid)
            .addSnapshotListener((snapshot, error) -> {
                FirebaseUser active = auth.getCurrentUser();
                if (active == null || watchingUid == null || !watchingUid.equals(active.getUid())) return;
                android.content.SharedPreferences prefs = getPreferences(MODE_PRIVATE);
                boolean localJoined = prefs.getBoolean("worker_joined", false);
                String localCompanyId = prefs.getString("worker_company_id", "");
                String localCompanyName = prefs.getString("worker_company_name", "");
                String localMode = prefs.getString("worker_mode", currentMode == null ? "" : currentMode);
                if (error != null) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        grantRole(active, "worker", currentMode);
                    } else {
                        showWorkerJoin();
                        workerJoinStatus.setText("કોડ તપાસવામાં ભૂલ. ફરી પ્રયાસ કરો.");
                    }
                    return;
                }
                if (snapshot == null || !snapshot.exists()) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        grantRole(active, "worker", currentMode);
                    } else showWorkerJoin();
                    return;
                }
                currentCompanyName = safe(snapshot.getString("companyName"));
                currentCompanyId = safe(snapshot.getString("companyId"));
                boolean removed = Boolean.TRUE.equals(snapshot.getBoolean("removed"));
                if (removed) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_mode").putBoolean("worker_joined", false).apply();
                    signOut();
                    return;
                }
                String mode = safe(snapshot.getString("mode"));
                if (!("hour".equals(mode) || "diamond".equals(mode))) mode = currentMode;
                if (!("hour".equals(mode) || "diamond".equals(mode))) mode = "diamond";
                currentMode = mode;
                prefs.edit().putString("worker_company_id", currentCompanyId).putString("worker_company_name", currentCompanyName)
                    .putString("worker_mode", mode).putBoolean("worker_joined", true).apply();
                if (!Boolean.TRUE.equals(snapshot.getBoolean("active"))) {
                    Map<String,Object> activate = new HashMap<>();
                    activate.put("active", true);
                    activate.put("removed", false);
                    database.collection("workers").document(active.getUid()).set(activate, com.google.firebase.firestore.SetOptions.merge());
                }
                grantRole(active, "worker", mode);
            });
    }

    private void showWorkerJoin'''
j=j[:worker_state.start()]+worker_new+j[worker_state.end():]

# Pending screen is no longer part of the flow. Keep method for compatibility but route directly.
pending=re.search(r'''    private void showWorkerPending\(String companyName\) \{.*?\n    \}\n\n    private void grantRole''', j, re.S)
if not pending: raise SystemExit('showWorkerPending block not found')
pending_new='''    private void showWorkerPending(String companyName) {
        FirebaseUser user = auth.getCurrentUser();
        if (user != null) showWorkerState(user); else showWorkerJoin();
    }

    private void grantRole'''
j=j[:pending.start()]+pending_new+j[pending.end():]

# 5) Sheth dashboard: remove the old mixed factory total cards from the top.
old_total=re.search(r'''        TextView totalTitle = sectionText\("કારખાનાનો કુલ"\);.*?        bossInfoBox.addView\(rowTwo, fullWrap\(\)\);\n''', j, re.S)
if not old_total: raise SystemExit('boss total cards block not found')
new_total='''        TextView totalTitle = sectionText("વિભાગ પસંદ કરો");
        totalTitle.setPadding(0, dp(14), 0, dp(8));
        bossInfoBox.addView(totalTitle, fullWrap());
        // Keep legacy summary fields alive for compatibility, but department totals are rendered below.
        bossSummaryDiamonds = metricValue("0 નંગ");
        bossSummaryEarnings = metricValue("₹0");
        bossSummaryWithdrawals = metricValue("₹0");
        bossSummaryRemaining = metricValue("₹0");
'''
j=j[:old_total.start()]+new_total+j[old_total.end():]

# Insert a department renderer helper before addWorkerRow.
marker='''    private void addWorkerRow(DocumentSnapshot worker) { addWorkerRow(worker, null); }'''
if marker not in j: raise SystemExit('addWorkerRow marker not found')
helper='''    private void renderBossDepartment(LinearLayout target, String mode, List<DocumentSnapshot> workers, Map<String,Map<String,Object>> live, String month) {
        target.removeAllViews();
        long pieces = 0;
        double hours = 0d, earnings = 0d, withdrawal = 0d, remaining = 0d;
        for (DocumentSnapshot worker : workers) {
            Map<String,Object> ms = bossMonthSummary(worker, live, month);
            pieces += Math.round(mapNumber(ms, "diamonds"));
            hours += mapNumber(ms, "hours");
            earnings += mapNumber(ms, "earnings");
            withdrawal += mapNumber(ms, "withdrawal");
            remaining += mapNumber(ms, "remaining");
        }
        TextView title = sectionText(("diamond".equals(mode) ? "હીરા ડિપાર્ટમેન્ટ" : "કલાક ડિપાર્ટમેન્ટ") + " · " + workers.size() + " કારીગર");
        title.setGravity(Gravity.START);
        target.addView(title, fullWrap());
        String workText;
        if ("diamond".equals(mode)) workText = "કુલ કામ: " + pieces + " નંગ";
        else {
            String h = String.format(Locale.US, "%.2f", hours);
            if (h.endsWith(".00")) h = h.substring(0, h.length()-3);
            workText = "કુલ કામ: " + h + " કલાક";
        }
        TextView summary = bodyText(workText + "  ·  કમાણી " + rupees(earnings) + "  ·  ઉપાડ " + rupees(withdrawal) + "  ·  બાકી " + rupees(remaining));
        summary.setPadding(0, dp(8), 0, dp(12));
        target.addView(summary, fullWrap());
        for (DocumentSnapshot worker : workers) addWorkerRowTo(target, worker, bossMonthSummary(worker, live, month));
        if (workers.isEmpty()) {
            TextView empty = bodyText("આ વિભાગમાં હજુ કોઈ કારીગર નથી.");
            empty.setPadding(0, dp(12), 0, dp(12));
            target.addView(empty, fullWrap());
        }
    }

'''
j=j.replace(marker,helper+marker,1)

# Replace old filter/list portion with two top-level department choices + department-specific totals.
old_filters=re.search(r'''        LinearLayout filters = new LinearLayout\(this\);.*?        showDiamond\.run\(\);\n''', j, re.S)
if not old_filters: raise SystemExit('boss filters block not found')
new_filters='''        LinearLayout filters = new LinearLayout(this);
        filters.setOrientation(LinearLayout.HORIZONTAL);
        Button diamondFilter = primaryButton("હીરા ડિપાર્ટમેન્ટ");
        Button hourFilter = secondaryButton("કલાક ડિપાર્ટમેન્ટ");
        filters.addView(diamondFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        filters.addView(hourFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        bossWorkers.addView(filters, fullWrap());
        LinearLayout filteredList = new LinearLayout(this);
        filteredList.setOrientation(LinearLayout.VERTICAL);
        bossWorkers.addView(filteredList, fullWrap());
        Runnable showDiamond = () -> {
            diamondFilter.setEnabled(false); hourFilter.setEnabled(true);
            renderBossDepartment(filteredList, "diamond", diamondWorkers, live, month);
        };
        Runnable showHours = () -> {
            hourFilter.setEnabled(false); diamondFilter.setEnabled(true);
            renderBossDepartment(filteredList, "hour", hourWorkers, live, month);
        };
        diamondFilter.setOnClickListener(v -> showDiamond.run());
        hourFilter.setOnClickListener(v -> showHours.run());
        showDiamond.run();
'''
j=j[:old_filters.start()]+new_filters+j[old_filters.end():]

# Do not show legacy/mixed workers in either department.
legacy=re.search(r'''        if \(!legacyWorkers\.isEmpty\(\)\) \{.*?        \}\n''', j, re.S)
if legacy:
    j=j[:legacy.start()]+j[legacy.end():]

# Update title and keep hidden legacy summary values for compatibility.
j=j.replace('bossWorkersTitle.setText(visible == 0 ? "હજુ કોઈ કારીગર જોડાયેલો નથી" : "કારીગરો · " + visible);',
            'bossWorkersTitle.setText(visible == 0 ? "હજુ કોઈ કારીગર જોડાયેલો નથી" : "વિભાગ મુજબ કારીગરો · " + visible);',1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 60', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.2'", b, count=1)
build.write_text(b)
print('v3.2.2 final six-point patch applied')
