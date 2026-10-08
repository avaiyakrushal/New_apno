from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 89","versionCode 90").replace("versionName '3.2.31'","versionName '3.2.32'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

start=s.index("    private void createAdminScreen(FrameLayout root) {")
end=s.index("    @Override protected void onStart() {", start)
new=r'''    private void createAdminScreen(FrameLayout root) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        adminScreen = baseScreen();
        adminScreen.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        scroll.addView(adminScreen, new ScrollView.LayoutParams(-1, -2));

        adminScreen.addView(titleText("◆  MB ડાયમંડ ડાયરી"), fullWrap());
        TextView title = sectionText("Super Admin Dashboard");
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(10), 0, dp(4));
        adminScreen.addView(title, fullWrap());

        TextView sub = bodyText("કંપની, શેઠ, કારીગર અને સૂચનાઓનું નિયંત્રણ");
        sub.setGravity(Gravity.CENTER);
        sub.setTextColor(0xff69758e);
        sub.setPadding(0, 0, 0, dp(12));
        adminScreen.addView(sub, fullWrap());

        adminStats = bodyText("ડેટા લોડ થઈ રહ્યો છે…");
        adminStats.setTextSize(16);
        adminStats.setPadding(dp(14), dp(14), dp(14), dp(14));
        adminStats.setBackground(roundedBackground(0xffffffff, 0xffe3e7ef, 16));
        adminScreen.addView(adminStats, fullWrap());

        TextView companyTitle = sectionText("બધી કંપનીઓ");
        companyTitle.setPadding(0, dp(18), 0, dp(8));
        adminScreen.addView(companyTitle, fullWrap());

        adminCompanies = new LinearLayout(this);
        adminCompanies.setOrientation(LinearLayout.VERTICAL);
        adminScreen.addView(adminCompanies, fullWrap());

        Button refresh = primaryButton("રીફ્રેશ કરો");
        refresh.setOnClickListener(v -> loadAdminDashboard());
        adminScreen.addView(refresh, fullWrap());

        Button logout = secondaryButton("લોગ આઉટ");
        logout.setOnClickListener(v -> signOut());
        adminScreen.addView(logout, fullWrap());

        adminScreen.setTag(scroll);
        root.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        scroll.setVisibility(View.GONE);
    }

    private void setAdminVisible(boolean visible) {
        if (adminScreen == null) return;
        Object tag = adminScreen.getTag();
        if (tag instanceof ScrollView) ((ScrollView) tag).setVisibility(visible ? View.VISIBLE : View.GONE);
    }

    private boolean isSuperAdmin(FirebaseUser user) {
        return user != null && "maniyajitesh56@gmail.com".equalsIgnoreCase(safe(user.getEmail()));
    }

    private void showAdminDashboard() {
        FirebaseUser user = auth.getCurrentUser();
        if (!isSuperAdmin(user)) { signOut(); return; }
        currentRole = "admin";
        clearWorkerListener();
        clearBossWorkersListener();
        clearCloudListeners();
        hideAll();
        setAdminVisible(true);
        loadAdminDashboard();
    }

    private boolean docFlag(DocumentSnapshot doc, String key) {
        return doc != null && Boolean.TRUE.equals(doc.getBoolean(key));
    }

    private void adminToast(String text) {
        android.widget.Toast.makeText(this, text, android.widget.Toast.LENGTH_SHORT).show();
    }

    private void loadAdminDashboard() {
        FirebaseUser admin = auth.getCurrentUser();
        if (!isSuperAdmin(admin) || adminStats == null || adminCompanies == null) return;
        adminStats.setText("ડેટા લોડ થઈ રહ્યો છે…");
        adminCompanies.removeAllViews();
        database.collection("users").get().addOnSuccessListener(usersSnap -> {
            database.collection("companies").get().addOnSuccessListener(companiesSnap -> {
                database.collection("workers").get().addOnSuccessListener(workersSnap -> {
                    Map<String,DocumentSnapshot> usersById = new HashMap<>();
                    for (DocumentSnapshot u : usersSnap.getDocuments()) usersById.put(u.getId(), u);
                    List<DocumentSnapshot> allWorkers = new ArrayList<>(workersSnap.getDocuments());
                    int activeWorkers = 0, blockedWorkers = 0, blockedCompanies = 0;
                    for (DocumentSnapshot workerDoc : allWorkers) {
                        if (!docFlag(workerDoc,"removed")) activeWorkers++;
                        if (docFlag(workerDoc,"adminBlocked") || docFlag(workerDoc,"adminCompanyBlocked")) blockedWorkers++;
                    }
                    for (DocumentSnapshot companyDoc : companiesSnap.getDocuments())
                        if (docFlag(companyDoc,"adminBlocked") || docFlag(companyDoc,"adminDeleted")) blockedCompanies++;

                    adminStats.setText(
                        "કુલ Companies: " + companiesSnap.size() +
                        "   ·   Blocked: " + blockedCompanies +
                        "\nકુલ Workers: " + activeWorkers +
                        "   ·   Blocked: " + blockedWorkers +
                        "\nકુલ Users: " + usersSnap.size()
                    );
                    adminCompanies.removeAllViews();
                    List<DocumentSnapshot> companies = new ArrayList<>(companiesSnap.getDocuments());
                    companies.sort((a,b) -> safe(a.getString("name")).compareToIgnoreCase(safe(b.getString("name"))));
                    for (DocumentSnapshot company : companies) addAdminCompanyCard(company, usersById, allWorkers);
                    if (companies.isEmpty()) adminCompanies.addView(bodyText("હજુ કોઈ કંપની નથી."), fullWrap());
                }).addOnFailureListener(e -> adminStats.setText("Workers ડેટા લોડ થઈ શક્યો નથી."));
            }).addOnFailureListener(e -> adminStats.setText("Companies ડેટા લોડ થઈ શક્યો નથી."));
        }).addOnFailureListener(e -> adminStats.setText("Users ડેટા લોડ થઈ શક્યો નથી."));
    }

    private void addAdminCompanyCard(DocumentSnapshot company, Map<String,DocumentSnapshot> usersById, List<DocumentSnapshot> allWorkers) {
        final String companyId = company.getId();
        final String companyName = safe(company.getString("name")).length() == 0 ? "નામ વગરની કંપની" : safe(company.getString("name"));
        final String companyCode = safe(company.getString("code"));
        boolean blocked = docFlag(company,"adminBlocked");
        boolean deleted = docFlag(company,"adminDeleted");
        DocumentSnapshot boss = usersById.get(companyId);
        String bossName = boss == null ? "—" : safe(boss.getString("googleName"));
        if (bossName.length() == 0 && boss != null) bossName = safe(boss.getString("name"));
        String bossEmail = boss == null ? "—" : safe(boss.getString("email"));

        List<DocumentSnapshot> workers = new ArrayList<>();
        for (DocumentSnapshot worker : allWorkers) {
            String cid = safe(worker.getString("companyId"));
            String bid = safe(worker.getString("bossUid"));
            String ccode = safe(worker.getString("companyCode"));
            boolean same = companyId.equals(cid) || companyId.equals(bid) || (companyCode.length() > 0 && companyCode.equalsIgnoreCase(ccode));
            if (same && !docFlag(worker,"removed")) workers.add(worker);
        }

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(14), dp(14), dp(14));
        card.setBackground(roundedBackground(0xffffffff, blocked || deleted ? 0xffcf6679 : 0xffe3e7ef, 18));
        card.setElevation(dp(1));

        TextView name = sectionText(companyName + (deleted ? "  ·  Deleted" : (blocked ? "  ·  Blocked" : "")));
        name.setGravity(Gravity.START);
        name.setTextColor(deleted || blocked ? 0xffa80d32 : 0xff17243a);
        card.addView(name, fullWrap());

        TextView meta = bodyText("કોડ: " + (companyCode.length()==0 ? "—" : companyCode) + "   ·   કારીગર: " + workers.size());
        meta.setTextSize(13); meta.setTextColor(0xff536073); meta.setPadding(0,dp(5),0,0);
        card.addView(meta, fullWrap());
        TextView bossView = bodyText("શેઠ: " + (bossName.length()==0 ? "—" : bossName) + "\n" + (bossEmail.length()==0 ? "—" : bossEmail));
        bossView.setTextSize(13); bossView.setTextColor(0xff69758e); bossView.setPadding(0,dp(4),0,dp(10));
        card.addView(bossView, fullWrap());

        LinearLayout workersBox = new LinearLayout(this);
        workersBox.setOrientation(LinearLayout.VERTICAL);
        workersBox.setVisibility(View.GONE);

        LinearLayout row1 = new LinearLayout(this); row1.setOrientation(LinearLayout.HORIZONTAL);
        Button open = secondaryButton("કારીગર જુઓ");
        open.setOnClickListener(v -> {
            boolean show = workersBox.getVisibility() != View.VISIBLE;
            workersBox.setVisibility(show ? View.VISIBLE : View.GONE);
            open.setText(show ? "કારીગર છુપાવો" : "કારીગર જુઓ");
        });
        Button block = secondaryButton(blocked || deleted ? "Unblock" : "Block");
        block.setOnClickListener(v -> setAdminCompanyBlocked(companyId, companyCode, workers, !(blocked || deleted), false));
        row1.addView(open, new LinearLayout.LayoutParams(0,-2,1f));
        LinearLayout.LayoutParams bLp = new LinearLayout.LayoutParams(0,-2,1f); bLp.leftMargin=dp(8); row1.addView(block,bLp);
        card.addView(row1, fullWrap());

        LinearLayout row2 = new LinearLayout(this); row2.setOrientation(LinearLayout.HORIZONTAL);
        Button rename = secondaryButton("નામ બદલો");
        rename.setOnClickListener(v -> editAdminCompanyName(companyId, companyCode, companyName, workers));
        Button notice = secondaryButton("સૂચના મોકલો");
        notice.setOnClickListener(v -> promptAdminCompanyNotice(companyId, companyCode, companyName, workers));
        row2.addView(rename, new LinearLayout.LayoutParams(0,-2,1f));
        LinearLayout.LayoutParams nLp = new LinearLayout.LayoutParams(0,-2,1f); nLp.leftMargin=dp(8); row2.addView(notice,nLp);
        card.addView(row2, fullWrap());

        Button delete = secondaryButton(deleted ? "કંપની ફરી ચાલુ કરો" : "કંપની બંધ / Delete");
        delete.setOnClickListener(v -> {
            if (deleted) setAdminCompanyBlocked(companyId, companyCode, workers, false, true);
            else confirmAdminDeleteCompany(companyId, companyCode, workers);
        });
        card.addView(delete, fullWrap());

        if (workers.isEmpty()) workersBox.addView(bodyText("આ કંપનીમાં કોઈ active કારીગર નથી."), fullWrap());
        else for (DocumentSnapshot worker : workers) addAdminWorkerCard(workersBox, worker, companyId, companyCode);
        card.addView(workersBox, fullWrap());
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(-1,-2); cardLp.bottomMargin=dp(12);
        adminCompanies.addView(card, cardLp);
    }

    private void addAdminWorkerCard(LinearLayout target, DocumentSnapshot worker, String companyId, String companyCode) {
        String uid = worker.getId();
        String name = safe(worker.getString("name")); if (name.length()==0) name="કારીગર";
        String mode = safe(worker.getString("mode"));
        boolean blocked = docFlag(worker,"adminBlocked") || docFlag(worker,"adminCompanyBlocked");
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(12),dp(10),dp(12),dp(10));
        box.setBackground(roundedBackground(0xfff8f9fb, blocked ? 0xffcf6679 : 0xffe5e8ef, 14));
        TextView title = sectionText(name + (blocked ? "  ·  Blocked" : "")); title.setGravity(Gravity.START); title.setTextSize(15); box.addView(title,fullWrap());
        TextView meta = bodyText(("hour".equals(mode)?"કલાક":"diamond".equals(mode)?"હીરા":"—") + "  ·  " + safe(worker.getString("phone")));
        meta.setTextSize(12); meta.setTextColor(0xff69758e); box.addView(meta,fullWrap());
        Button toggle = secondaryButton(blocked ? "કારીગર Unblock" : "કારીગર Block");
        toggle.setOnClickListener(v -> setAdminWorkerBlocked(uid, companyId, companyCode, !blocked));
        box.addView(toggle,fullWrap());
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2); lp.topMargin=dp(8); target.addView(box,lp);
    }

    private void setAdminWorkerBlocked(String uid, String companyId, String companyCode, boolean blocked) {
        Map<String,Object> update = new HashMap<>();
        update.put("adminBlocked", blocked);
        update.put("adminBlockedAt", blocked ? com.google.firebase.firestore.FieldValue.serverTimestamp() : com.google.firebase.firestore.FieldValue.delete());
        update.put("adminBlockedReason", blocked ? "Super Admin" : com.google.firebase.firestore.FieldValue.delete());
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("workers").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length()>0) batch.set(database.collection("companies").document(companyId).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length()>0) batch.set(database.collection("companyCodes").document(companyCode).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.commit().addOnSuccessListener(v -> { adminToast(blocked ? "કારીગર Block થયો" : "કારીગર Unblock થયો"); loadAdminDashboard(); })
            .addOnFailureListener(e -> adminToast("ફેરફાર સેવ થઈ શક્યો નથી"));
    }

    private void setAdminCompanyBlocked(String companyId, String companyCode, List<DocumentSnapshot> workers, boolean blocked, boolean restoreDeleted) {
        Map<String,Object> companyUpdate = new HashMap<>();
        companyUpdate.put("adminBlocked", blocked);
        if (restoreDeleted) companyUpdate.put("adminDeleted", false);
        companyUpdate.put("adminUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        Map<String,Object> memberUpdate = new HashMap<>();
        memberUpdate.put("adminCompanyBlocked", blocked);
        memberUpdate.put("adminCompanyBlockedAt", blocked ? com.google.firebase.firestore.FieldValue.serverTimestamp() : com.google.firebase.firestore.FieldValue.delete());
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("companies").document(companyId), companyUpdate, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(companyId), memberUpdate, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length()>0) batch.set(database.collection("companyCodes").document(companyCode), companyUpdate, com.google.firebase.firestore.SetOptions.merge());
        for (DocumentSnapshot w : workers) {
            String uid=w.getId();
            batch.set(database.collection("workers").document(uid), memberUpdate, com.google.firebase.firestore.SetOptions.merge());
            batch.set(database.collection("users").document(uid), memberUpdate, com.google.firebase.firestore.SetOptions.merge());
            batch.set(database.collection("companies").document(companyId).collection("members").document(uid), memberUpdate, com.google.firebase.firestore.SetOptions.merge());
            if (companyCode != null && companyCode.length()>0) batch.set(database.collection("companyCodes").document(companyCode).collection("members").document(uid), memberUpdate, com.google.firebase.firestore.SetOptions.merge());
        }
        batch.commit().addOnSuccessListener(v -> { adminToast(blocked ? "કંપની Block થઈ" : "કંપની Unblock થઈ"); loadAdminDashboard(); })
            .addOnFailureListener(e -> adminToast("કંપની status સેવ થઈ શક્યો નથી"));
    }

    private void confirmAdminDeleteCompany(String companyId, String companyCode, List<DocumentSnapshot> workers) {
        new android.app.AlertDialog.Builder(this)
            .setTitle("કંપની બંધ / Delete")
            .setMessage("કંપનીને Super Admin દ્વારા બંધ કરશો? જૂનો હીરા/કલાક/ખર્ચ data ડિલીટ નહીં થાય અને પછી ફરી Restore કરી શકશો.")
            .setPositiveButton("બંધ કરો", (d,w) -> {
                Map<String,Object> u=new HashMap<>(); u.put("adminDeleted",true); u.put("adminBlocked",true); u.put("adminDeletedAt",com.google.firebase.firestore.FieldValue.serverTimestamp());
                database.collection("companies").document(companyId).set(u,com.google.firebase.firestore.SetOptions.merge())
                    .addOnSuccessListener(v -> setAdminCompanyBlocked(companyId,companyCode,workers,true,false));
                if(companyCode!=null && companyCode.length()>0) database.collection("companyCodes").document(companyCode).set(u,com.google.firebase.firestore.SetOptions.merge());
            })
            .setNegativeButton("રદ કરો",null).show();
    }

    private void editAdminCompanyName(String companyId, String companyCode, String oldName, List<DocumentSnapshot> workers) {
        EditText input=new EditText(this); input.setText(oldName); input.setSingleLine(true); input.setPadding(dp(16),dp(12),dp(16),dp(12));
        new android.app.AlertDialog.Builder(this).setTitle("કંપનીનું નામ બદલો").setView(input)
            .setPositiveButton("સેવ",(d,w)->{
                String name=input.getText().toString().trim(); if(name.length()<2){adminToast("માન્ય નામ લખો");return;} if(name.length()>80)name=name.substring(0,80);
                Map<String,Object> up=new HashMap<>(); up.put("name",name); up.put("companyName",name); up.put("adminUpdatedAt",com.google.firebase.firestore.FieldValue.serverTimestamp());
                com.google.firebase.firestore.WriteBatch batch=database.batch();
                batch.set(database.collection("companies").document(companyId),up,com.google.firebase.firestore.SetOptions.merge());
                if(companyCode!=null&&companyCode.length()>0) batch.set(database.collection("companyCodes").document(companyCode),up,com.google.firebase.firestore.SetOptions.merge());
                for(DocumentSnapshot wr:workers){String uid=wr.getId(); batch.set(database.collection("workers").document(uid),java.util.Collections.singletonMap("companyName",name),com.google.firebase.firestore.SetOptions.merge()); batch.set(database.collection("users").document(uid),java.util.Collections.singletonMap("companyName",name),com.google.firebase.firestore.SetOptions.merge());}
                batch.commit().addOnSuccessListener(v->{adminToast("નામ બદલાયું");loadAdminDashboard();}).addOnFailureListener(e->adminToast("નામ બદલાઈ શક્યું નથી"));
            }).setNegativeButton("રદ કરો",null).show();
    }

    private void promptAdminCompanyNotice(String companyId, String companyCode, String companyName, List<DocumentSnapshot> workers) {
        EditText input=new EditText(this); input.setHint("સૂચના લખો"); input.setMinLines(3); input.setGravity(Gravity.TOP); input.setPadding(dp(16),dp(12),dp(16),dp(12));
        new android.app.AlertDialog.Builder(this).setTitle("Super Admin સૂચના").setView(input)
            .setPositiveButton("મોકલો",(d,w)->{
                String text=input.getText().toString().trim(); if(text.length()==0){adminToast("સૂચના લખો");return;} if(text.length()>500)text=text.substring(0,500);
                sendAdminCompanyNotice(companyId,companyCode,companyName,workers,text);
            }).setNegativeButton("રદ કરો",null).show();
    }

    private void sendAdminCompanyNotice(String companyId, String companyCode, String companyName, List<DocumentSnapshot> workers, String text) {
        FirebaseUser admin=auth.getCurrentUser(); if(!isSuperAdmin(admin))return;
        Map<String,Object> notice=new HashMap<>(); long now=System.currentTimeMillis();
        notice.put("companyId",companyId); notice.put("companyCode",companyCode==null?"":companyCode); notice.put("companyName",companyName==null?"":companyName); notice.put("senderUid",admin.getUid()); notice.put("senderRole","super_admin"); notice.put("text",text); notice.put("createdAtMillis",now); notice.put("createdAt",com.google.firebase.firestore.FieldValue.serverTimestamp());
        database.collection("notifications").add(notice).addOnSuccessListener(ref->{
            Map<String,Object> shared=new HashMap<>(notice); shared.put("id",ref.getId()); shared.remove("createdAt");
            Map<String,Object> latest=new HashMap<>(shared);
            if(companyCode!=null&&companyCode.length()>0){ database.collection("companyCodes").document(companyCode).collection("notices").document(ref.getId()).set(shared,com.google.firebase.firestore.SetOptions.merge()); database.collection("companyCodes").document(companyCode).set(java.util.Collections.singletonMap("latestNotice",latest),com.google.firebase.firestore.SetOptions.merge()); }
            database.collection("companies").document(companyId).collection("notices").document(ref.getId()).set(shared,com.google.firebase.firestore.SetOptions.merge());
            database.collection("companies").document(companyId).set(java.util.Collections.singletonMap("latestNotice",latest),com.google.firebase.firestore.SetOptions.merge());
            for(DocumentSnapshot wr:workers){String uid=wr.getId(); Map<String,Object> inbox=new HashMap<>(); inbox.put("latestNotice",latest); inbox.put("noticeUpdatedAt",com.google.firebase.firestore.FieldValue.serverTimestamp()); database.collection("workers").document(uid).set(inbox,com.google.firebase.firestore.SetOptions.merge()); database.collection("users").document(uid).set(inbox,com.google.firebase.firestore.SetOptions.merge());}
            adminToast("સૂચના મોકલાઈ ગઈ");
        }).addOnFailureListener(e->adminToast("સૂચના મોકલી શકાઈ નથી"));
    }

    private void signOutBlocked(String message) {
        adminToast(message == null || message.length()==0 ? "Super Admin દ્વારા access બંધ છે" : message);
        signOut();
    }

'''
s=s[:start]+new+s[end:]

old='''                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !user.getUid().equals(active.getUid())) return;
                String role = safe(snapshot.getString("role"));
'''
new='''                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !user.getUid().equals(active.getUid())) return;
                if (docFlag(snapshot,"adminBlocked") || docFlag(snapshot,"adminCompanyBlocked") || docFlag(snapshot,"adminDeleted")) {
                    signOutBlocked("Super Admin દ્વારા આ accountનો access બંધ છે");
                    return;
                }
                String role = safe(snapshot.getString("role"));
'''
if old not in s: raise SystemExit("route block anchor missing")
s=s.replace(old,new,1)

old='''                if (snapshot.exists()) {
                    currentCompanyName = safe(snapshot.getString("name"));
                    currentCompanyCode = safe(snapshot.getString("code"));
                    showBossCompanyInfo(user);
'''
new='''                if (snapshot.exists()) {
                    if (docFlag(snapshot,"adminBlocked") || docFlag(snapshot,"adminDeleted")) {
                        signOutBlocked("Super Admin દ્વારા કંપનીનો access બંધ છે");
                        return;
                    }
                    currentCompanyName = safe(snapshot.getString("name"));
                    currentCompanyCode = safe(snapshot.getString("code"));
                    showBossCompanyInfo(user);
'''
if old not in s: raise SystemExit("boss company block anchor missing")
s=s.replace(old,new,1)

old='''                if (snapshot != null && snapshot.exists()) consumeWorkerLatestNotice(snapshot);
                if (snapshot == null || !snapshot.exists()) {
'''
new='''                if (snapshot != null && snapshot.exists()) {
                    if (docFlag(snapshot,"adminBlocked") || docFlag(snapshot,"adminCompanyBlocked") || docFlag(snapshot,"adminDeleted")) {
                        signOutBlocked("Super Admin દ્વારા કારીગર access બંધ છે");
                        return;
                    }
                    consumeWorkerLatestNotice(snapshot);
                }
                if (snapshot == null || !snapshot.exists()) {
'''
if old not in s: raise SystemExit("worker listener block anchor missing")
s=s.replace(old,new,1)

old='''                if (!snapshot.exists()) {
                    workerJoinButton.setEnabled(true);
                    workerJoinStatus.setText("આ શેઠનો કોડ મળ્યો નથી");
                    return;
                }
                String companyId = safe(snapshot.getString("companyId"));
'''
new='''                if (!snapshot.exists()) {
                    workerJoinButton.setEnabled(true);
                    workerJoinStatus.setText("આ શેઠનો કોડ મળ્યો નથી");
                    return;
                }
                if (docFlag(snapshot,"adminBlocked") || docFlag(snapshot,"adminDeleted")) {
                    workerJoinButton.setEnabled(true);
                    workerJoinStatus.setText("આ કંપની Super Admin દ્વારા બંધ છે");
                    return;
                }
                String companyId = safe(snapshot.getString("companyId"));
'''
if old not in s: raise SystemExit("join block anchor missing")
s=s.replace(old,new,1)

s=s.replace('''        if ("maniyajitesh56@gmail.com".equalsIgnoreCase(safe(user.getEmail()))) {
            showAdminDashboard();
            return;
        }
''','''        if (isSuperAdmin(user)) {
            showAdminDashboard();
            return;
        }
''',1)

p.write_text(s)
print("v3.2.32 Super Admin controls applied")
