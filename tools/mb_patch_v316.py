from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

login_new=r'''    private void createLoginScreen(FrameLayout root) {
        login = baseScreen();
        TextView title = titleText("◆  MB ડાયમંડ ડાયરી");
        login.addView(title, fullWrap());

        TextView subtitle = bodyText("તમારી ભૂમિકા પસંદ કરો");
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, dp(18), 0, dp(14));
        login.addView(subtitle, fullWrap());

        bossLoginButton = primaryButton("શેઠ");
        bossLoginButton.setOnClickListener(v -> beginRoleLogin("boss", "both"));
        login.addView(bossLoginButton, fullWrap());

        hourLoginButton = secondaryButton("ઓફિસ (કલાકનું કામ)");
        hourLoginButton.setOnClickListener(v -> beginRoleLogin("worker", "hour"));
        login.addView(hourLoginButton, fullWrap());

        diamondLoginButton = secondaryButton("હીરા (કારીગર)");
        diamondLoginButton.setOnClickListener(v -> beginRoleLogin("worker", "diamond"));
        login.addView(diamondLoginButton, fullWrap());

        // Keep the legacy field pointing at the office button so shared enable/disable code remains safe.
        workerLoginButton = hourLoginButton;
        loginButton = bossLoginButton;
        loginStatus = bodyText("");
        loginStatus.setGravity(Gravity.CENTER);
        loginStatus.setPadding(0, dp(12), 0, 0);
        login.addView(loginStatus, fullWrap());
        root.addView(login, new FrameLayout.LayoutParams(-1, -1));
    }
'''
j, n = re.subn(r'    private void createLoginScreen\(FrameLayout root\) \{.*?\n    \}\n\n(?=    private void beginRoleLogin)', login_new+'\n', j, count=1, flags=re.S)
if n!=1: raise SystemExit(f'createLoginScreen replace count={n}')

role_new=r'''    private void createRoleChoiceScreen(FrameLayout root) {
        roleChoice = baseScreen();
        roleChoice.addView(titleText("◆  MB ડાયમંડ ડાયરી"), fullWrap());
        TextView title = sectionText("તમારી ભૂમિકા પસંદ કરો");
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(18), 0, dp(10));
        roleChoice.addView(title, fullWrap());

        Button boss = primaryButton("શેઠ");
        boss.setOnClickListener(v -> saveRole("boss", "both"));
        roleChoice.addView(boss, fullWrap());

        Button office = secondaryButton("ઓફિસ (કલાકનું કામ)");
        office.setOnClickListener(v -> saveRole("worker", "hour"));
        roleChoice.addView(office, fullWrap());

        Button diamond = secondaryButton("હીરા (કારીગર)");
        diamond.setOnClickListener(v -> saveRole("worker", "diamond"));
        roleChoice.addView(diamond, fullWrap());

        Button logout = secondaryButton("લોગ આઉટ");
        logout.setOnClickListener(v -> signOut());
        roleChoice.addView(logout, fullWrap());
        root.addView(roleChoice, new FrameLayout.LayoutParams(-1, -1));
        roleChoice.setVisibility(View.GONE);
    }
'''
j, n = re.subn(r'    private void createRoleChoiceScreen\(FrameLayout root\) \{.*?\n    \}\n\n(?=    private void createWorkerProfileScreen)', role_new+'\n', j, count=1, flags=re.S)
if n!=1: raise SystemExit(f'createRoleChoiceScreen replace count={n}')

old_apply=r'''                String savedRole = safe(snapshot.getString("role"));
                if ("boss".equals(savedRole) || "worker".equals(savedRole)) {
                    showAuthState();
                    return;
                }
                saveRole(selectedRole, selectedMode);'''
new_apply=r'''                saveRole(selectedRole, selectedMode);'''
if old_apply not in j: raise SystemExit('pending role guard block not found')
j=j.replace(old_apply,new_apply,1)

j=j.replace('                    worker.put("totalDiamonds", 0L);\n','',1)
old_set='database.collection("workers").document(user.getUid()).set(worker)'
new_set='database.collection("workers").document(user.getUid()).set(worker, com.google.firebase.firestore.SetOptions.merge())'
if old_set not in j: raise SystemExit('join worker destructive set not found')
j=j.replace(old_set,new_set,1)

watch_new=r'''    private void watchPendingWorkers(String companyId) {
        clearBossWorkersListener();
        bossWorkersListener = database.collection("workers")
            .whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error != null || snapshots == null) return;
                String month = currentMonthKey();
                List<DocumentSnapshot> docs = new ArrayList<>(snapshots.getDocuments());
                renderBossWorkers(docs, null, month);
                refreshBossDashboardFromEntries(docs, companyId, month);
            });
    }

    private Map<String,Object> calculateMonthFromEntries(com.google.firebase.firestore.QuerySnapshot snap, String month, String mode) {
        double diamonds = 0d, hours = 0d, earnings = 0d, withdrawal = 0d;
        if (snap != null) {
            for (DocumentSnapshot d : snap.getDocuments()) {
                if (!month.equals(monthKeyForEntryDate(safe(d.getString("date"))))) continue;
                String type = safe(d.getString("type"));
                String source = safe(d.getString("source"));
                if ("diamond".equals(mode) && !("diamond".equals(type) || ("withdrawal".equals(type) && "diamond".equals(source)))) continue;
                if ("hour".equals(mode) && !("hour".equals(type) || ("withdrawal".equals(type) && "hour".equals(source)))) continue;
                if ("diamond".equals(type)) {
                    diamonds += number(d, "pieces");
                    earnings += number(d, "amount");
                } else if ("hour".equals(type)) {
                    hours += number(d, "hours");
                    earnings += number(d, "amount");
                } else if ("withdrawal".equals(type)) {
                    withdrawal += number(d, "amount");
                }
            }
        }
        Map<String,Object> out = new HashMap<>();
        out.put("diamonds", diamonds);
        out.put("hours", hours);
        out.put("earnings", earnings);
        out.put("withdrawal", withdrawal);
        out.put("remaining", earnings - withdrawal);
        return out;
    }

    private Map<String,Object> bossMonthSummary(DocumentSnapshot worker, Map<String,Map<String,Object>> live, String month) {
        if (live != null) {
            Map<String,Object> one = live.get(worker.getId());
            if (one != null) return one;
        }
        return monthSummary(worker, month);
    }

    private void refreshBossDashboardFromEntries(List<DocumentSnapshot> workers, String companyId, String month) {
        if (!"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId)) return;
        List<DocumentSnapshot> activeWorkers = new ArrayList<>();
        for (DocumentSnapshot worker : workers) {
            if (Boolean.TRUE.equals(worker.getBoolean("removed"))) continue;
            if (Boolean.TRUE.equals(worker.getBoolean("active"))) activeWorkers.add(worker);
        }
        if (activeWorkers.isEmpty()) return;
        Map<String,Map<String,Object>> live = new HashMap<>();
        java.util.concurrent.atomic.AtomicInteger left = new java.util.concurrent.atomic.AtomicInteger(activeWorkers.size());
        for (DocumentSnapshot worker : activeWorkers) {
            String uid = worker.getId();
            String mode = safe(worker.getString("mode"));
            database.collection("diaryEntries").document(uid).collection("items").get()
                .addOnCompleteListener(task -> {
                    if (task.isSuccessful() && task.getResult() != null) {
                        live.put(uid, calculateMonthFromEntries(task.getResult(), month, mode));
                    }
                    if (left.decrementAndGet() == 0) {
                        FirebaseUser active = auth.getCurrentUser();
                        if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId)) return;
                        renderBossWorkers(workers, live, month);
                    }
                });
        }
    }

    private void renderBossWorkers(List<DocumentSnapshot> documents, Map<String,Map<String,Object>> live, String month) {
        bossWorkers.removeAllViews();
        currentBossWorkers.clear();
        long totalDiamonds = 0;
        double totalEarnings = 0;
        double totalWithdrawal = 0;
        double totalRemaining = 0;
        int visible = 0;
        List<DocumentSnapshot> hourWorkers = new ArrayList<>();
        List<DocumentSnapshot> diamondWorkers = new ArrayList<>();
        List<DocumentSnapshot> legacyWorkers = new ArrayList<>();
        for (DocumentSnapshot worker : documents) {
            boolean removed = Boolean.TRUE.equals(worker.getBoolean("removed"));
            if (removed) continue;
            visible++;
            String mode = safe(worker.getString("mode"));
            if ("hour".equals(mode)) hourWorkers.add(worker);
            else if ("diamond".equals(mode)) diamondWorkers.add(worker);
            else legacyWorkers.add(worker);

            Map<String,Object> ms = bossMonthSummary(worker, live, month);
            Map<String,Object> copy = new HashMap<>(worker.getData());
            copy.put("id", worker.getId());
            Map<String,Object> months = new HashMap<>();
            months.put(month, new HashMap<>(ms));
            copy.put("monthlySummaries", months);
            copy.put("summaryMonth", month);
            copy.put("monthDiamonds", mapNumber(ms, "diamonds"));
            copy.put("monthHours", mapNumber(ms, "hours"));
            copy.put("monthEarnings", mapNumber(ms, "earnings"));
            copy.put("monthWithdrawal", mapNumber(ms, "withdrawal"));
            copy.put("monthRemaining", mapNumber(ms, "remaining"));
            currentBossWorkers.add(copy);

            if (Boolean.TRUE.equals(worker.getBoolean("active"))) {
                totalDiamonds += Math.round(mapNumber(ms, "diamonds"));
                totalEarnings += mapNumber(ms, "earnings");
                totalWithdrawal += mapNumber(ms, "withdrawal");
                totalRemaining += mapNumber(ms, "remaining");
            }
        }
        if (!hourWorkers.isEmpty()) {
            TextView heading = sectionText("ઓફિસ / કલાક · " + hourWorkers.size());
            heading.setGravity(Gravity.START); bossWorkers.addView(heading, fullWrap());
            for (DocumentSnapshot worker : hourWorkers) addWorkerRow(worker, bossMonthSummary(worker, live, month));
        }
        if (!diamondWorkers.isEmpty()) {
            TextView heading = sectionText("હીરા કારીગરો · " + diamondWorkers.size());
            heading.setGravity(Gravity.START); bossWorkers.addView(heading, fullWrap());
            for (DocumentSnapshot worker : diamondWorkers) addWorkerRow(worker, bossMonthSummary(worker, live, month));
        }
        if (!legacyWorkers.isEmpty()) {
            TextView heading = sectionText("જૂના / કામ નક્કી બાકી · " + legacyWorkers.size());
            heading.setGravity(Gravity.START); bossWorkers.addView(heading, fullWrap());
            for (DocumentSnapshot worker : legacyWorkers) addWorkerRow(worker, bossMonthSummary(worker, live, month));
        }
        bossWorkersTitle.setText(visible == 0 ? "હજુ કોઈ કારીગર જોડાયેલો નથી" : "કારીગરો · " + visible);
        bossMonthLabel.setText(currentMonthLabel());
        bossSummaryDiamonds.setText(totalDiamonds + " નંગ");
        bossSummaryEarnings.setText(rupees(totalEarnings));
        bossSummaryWithdrawals.setText(rupees(totalWithdrawal));
        bossSummaryRemaining.setText(rupees(totalRemaining));
        bossSummaryRemaining.setTextColor(totalRemaining < 0 ? 0xffb02a37 : 0xff14845f);
    }
'''
j, n = re.subn(r'    private void watchPendingWorkers\(String companyId\) \{.*?\n    \}\n\n(?=    private void addWorkerRow\(DocumentSnapshot worker\))', watch_new+'\n', j, count=1, flags=re.S)
if n!=1: raise SystemExit(f'watchPendingWorkers replace count={n}')

old_sig='    private void addWorkerRow(DocumentSnapshot worker) {\n'
new_sig='''    private void addWorkerRow(DocumentSnapshot worker) { addWorkerRow(worker, null); }\n\n    private void addWorkerRow(DocumentSnapshot worker, Map<String,Object> overrideMonthData) {\n'''
if old_sig not in j: raise SystemExit('addWorkerRow signature not found')
j=j.replace(old_sig,new_sig,1)
old_month='        Map<String,Object> monthData = monthSummary(worker, currentMonthKey());\n'
new_month='        Map<String,Object> monthData = overrideMonthData != null ? overrideMonthData : monthSummary(worker, currentMonthKey());\n'
if old_month not in j: raise SystemExit('addWorkerRow monthData line not found')
j=j.replace(old_month,new_month,1)
old_meta='''        String workLabel = "hour".equals(workerMode) ? "કલાક / ઓફિસ" : ("diamond".equals(workerMode) ? "હીરા" : "જૂનો / નક્કી બાકી");\n        TextView meta = bodyText(workLabel + " · " + monthDiamonds + " નંગ · ઉપાડ " + rupees(withdrawal) + " · આપવાના બાકી " + rupees(remaining));'''
new_meta='''        String workLabel = "hour".equals(workerMode) ? "ઓફિસ / કલાક" : ("diamond".equals(workerMode) ? "હીરા" : "જૂનો / નક્કી બાકી");\n        double monthHours = mapNumber(monthData, "hours");\n        String hourText = String.format(Locale.US, "%.2f", monthHours);\n        if (hourText.endsWith(".00")) hourText = hourText.substring(0, hourText.length() - 3);\n        String workTotal = "hour".equals(workerMode) ? (hourText + " કલાક") : (monthDiamonds + " નંગ");\n        TextView meta = bodyText(workLabel + " · " + workTotal + " · ઉપાડ " + rupees(withdrawal) + " · આપવાના બાકી " + rupees(remaining));'''
if old_meta not in j: raise SystemExit('worker row meta block not found')
j=j.replace(old_meta,new_meta,1)

old_sync='''            double diamonds = o.optDouble("totalDiamonds", -1);\n            double earnings = o.optDouble("earnings", -1);'''
new_sync='''            double diamonds = o.optDouble("totalDiamonds", -1);\n            double hours = Math.max(0, o.optDouble("hours", 0));\n            double earnings = o.optDouble("earnings", -1);'''
if old_sync not in j: raise SystemExit('sync summary values block not found')
j=j.replace(old_sync,new_sync,1)
j=j.replace('            update.put("monthDiamonds", Math.round(diamonds));\n            update.put("monthEarnings", earnings);', '            update.put("monthDiamonds", Math.round(diamonds));\n            update.put("monthHours", hours);\n            update.put("monthEarnings", earnings);',1)
j=j.replace('                    sm.put("diamonds", Math.max(0, one.optDouble("diamonds", 0)));\n                    sm.put("earnings", Math.max(0, one.optDouble("earnings", 0)));', '                    sm.put("diamonds", Math.max(0, one.optDouble("diamonds", 0)));\n                    sm.put("hours", Math.max(0, one.optDouble("hours", 0)));\n                    sm.put("earnings", Math.max(0, one.optDouble("earnings", 0)));',1)

java.write_text(j)

js=root/'app/src/main/assets/app.js'
s=js.read_text()
old_js="""      monthlySummaries[m]={diamonds:diamonds.reduce((n,e)=>n+Number(e.pieces||0),0),earnings,withdrawal,remaining:earnings-withdrawal};\n    });\n    const month=today().slice(0,7), current=monthlySummaries[month]||{diamonds:0,earnings:0,withdrawal:0,remaining:0};\n    const summary={month,totalDiamonds:current.diamonds,earnings:current.earnings,withdrawal:current.withdrawal,remaining:current.remaining,monthlySummaries};"""
new_js="""      monthlySummaries[m]={diamonds:diamonds.reduce((n,e)=>n+Number(e.pieces||0),0),hours:hours.reduce((n,e)=>n+Number(e.hours||0),0),earnings,withdrawal,remaining:earnings-withdrawal};\n    });\n    const month=today().slice(0,7), current=monthlySummaries[month]||{diamonds:0,hours:0,earnings:0,withdrawal:0,remaining:0};\n    const summary={month,totalDiamonds:current.diamonds,hours:current.hours,earnings:current.earnings,withdrawal:current.withdrawal,remaining:current.remaining,monthlySummaries};"""
if old_js not in s: raise SystemExit('JS worker summary block not found')
s=s.replace(old_js,new_js,1)
js.write_text(s)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 53', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.1.6'", b, count=1)
build.write_text(b)
print('MB Diamond Diary v3.1.6 patch applied')
