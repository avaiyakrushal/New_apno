from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

needle='''    private ListenerRegistration notificationListener;
    private ListenerRegistration diaryEntriesListener;'''
rep='''    private ListenerRegistration notificationListener;
    private ListenerRegistration notificationFallbackListener;
    private ListenerRegistration notificationCompanyListener;
    private ListenerRegistration notificationCodeListener;
    private ListenerRegistration bossMembersListener;
    private ListenerRegistration bossCodeMembersListener;
    private ListenerRegistration diaryEntriesListener;'''
if needle not in j:
    raise SystemExit('listener fields anchor not found')
j=j.replace(needle,rep,1)

marker='''    private void joinCompany() {'''
helper=r'''    private void mirrorWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        if (user == null || worker == null) return;
        Map<String,Object> membership = new HashMap<>(worker);
        membership.put("uid", user.getUid());
        membership.put("role", "worker");
        membership.put("joined", true);
        membership.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        database.collection("users").document(user.getUid())
            .set(membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length() > 0) {
            database.collection("companyCodes").document(companyCode).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());
        }
        if (companyId != null && companyId.length() > 0) {
            database.collection("companies").document(companyId).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());
        }
    }

'''
if marker not in j:
    raise SystemExit('joinCompany marker not found')
j=j.replace(marker,helper+marker,1)

needle='''                            getPreferences(MODE_PRIVATE).edit()
                                    .putString("worker_company_id", companyId)
                                    .putString("worker_company_name", companyName)
                                    .putString("worker_company_code", code)
                                    .putString("worker_mode", joinMode)
                                    .putBoolean("worker_joined", true)
                                    .apply();
                            grantRole(user, "worker", joinMode);'''
rep='''                            getPreferences(MODE_PRIVATE).edit()
                                    .putString("worker_company_id", companyId)
                                    .putString("worker_company_name", companyName)
                                    .putString("worker_company_code", code)
                                    .putString("worker_mode", joinMode)
                                    .putBoolean("worker_joined", true)
                                    .apply();
                            mirrorWorkerMembership(user, worker, companyId, code);
                            grantRole(user, "worker", joinMode);'''
if needle not in j:
    raise SystemExit('join success anchor not found')
j=j.replace(needle,rep,1)

needle='''                database.collection("workers").document(active.getUid()).set(repair, com.google.firebase.firestore.SetOptions.merge());
                grantRole(active, "worker", mode);'''
rep='''                database.collection("workers").document(active.getUid()).set(repair, com.google.firebase.firestore.SetOptions.merge());
                Map<String,Object> mirror = new HashMap<>(snapshot.getData());
                mirror.putAll(repair);
                mirror.put("mode", mode);
                mirrorWorkerMembership(active, mirror, currentCompanyId, currentCompanyCode);
                grantRole(active, "worker", mode);'''
if needle not in j:
    raise SystemExit('existing worker mirror anchor not found')
j=j.replace(needle,rep,1)

old=r'''    private void loadAllWorkersFallback(String companyId) {
        database.collection("workers").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> matches = new ArrayList<>();
                for (DocumentSnapshot worker : snap.getDocuments()) {
                    String workerCompanyId = safe(worker.getString("companyId"));
                    String workerBossUid = safe(worker.getString("bossUid"));
                    String workerCode = safe(worker.getString("companyCode"));
                    boolean sameCompany = companyId.equals(workerCompanyId) || companyId.equals(workerBossUid);
                    if (!sameCompany && currentCompanyCode != null && currentCompanyCode.length() > 0)
                        sameCompany = currentCompanyCode.equalsIgnoreCase(workerCode);
                    if (sameCompany) matches.add(worker);
                }
                renderBossWorkerDocuments(matches, companyId);
            })
            .addOnFailureListener(e -> renderBossWorkerDocuments(new ArrayList<>(), companyId));
    }
'''
new=r'''    private void loadBossWorkersFromUsers(String companyId) {
        database.collection("users").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> matches = new ArrayList<>();
                for (DocumentSnapshot worker : snap.getDocuments()) {
                    if (!"worker".equals(safe(worker.getString("role")))) continue;
                    String workerCompanyId = safe(worker.getString("companyId"));
                    String workerBossUid = safe(worker.getString("bossUid"));
                    String workerCode = safe(worker.getString("companyCode"));
                    boolean sameCompany = companyId.equals(workerCompanyId) || companyId.equals(workerBossUid);
                    if (!sameCompany && currentCompanyCode != null && currentCompanyCode.length() > 0)
                        sameCompany = currentCompanyCode.equalsIgnoreCase(workerCode);
                    if (sameCompany && !Boolean.TRUE.equals(worker.getBoolean("removed"))) matches.add(worker);
                }
                renderBossWorkerDocuments(matches, companyId);
            })
            .addOnFailureListener(e -> renderBossWorkerDocuments(new ArrayList<>(), companyId));
    }

    private void loadBossWorkersFromCompanyMembers(String companyId) {
        database.collection("companies").document(companyId).collection("members").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadBossWorkersFromUsers(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersFromUsers(companyId));
    }

    private void loadBossWorkersFromCodeMembers(String companyId) {
        if (currentCompanyCode == null || currentCompanyCode.length() == 0) {
            loadBossWorkersFromCompanyMembers(companyId);
            return;
        }
        database.collection("companyCodes").document(currentCompanyCode).collection("members").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadBossWorkersFromCompanyMembers(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersFromCompanyMembers(companyId));
    }

    private void loadAllWorkersFallback(String companyId) {
        database.collection("workers").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> matches = new ArrayList<>();
                for (DocumentSnapshot worker : snap.getDocuments()) {
                    String workerCompanyId = safe(worker.getString("companyId"));
                    String workerBossUid = safe(worker.getString("bossUid"));
                    String workerCode = safe(worker.getString("companyCode"));
                    boolean sameCompany = companyId.equals(workerCompanyId) || companyId.equals(workerBossUid);
                    if (!sameCompany && currentCompanyCode != null && currentCompanyCode.length() > 0)
                        sameCompany = currentCompanyCode.equalsIgnoreCase(workerCode);
                    if (sameCompany) matches.add(worker);
                }
                if (!matches.isEmpty()) renderBossWorkerDocuments(matches, companyId);
                else loadBossWorkersFromCodeMembers(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersFromCodeMembers(companyId));
    }
'''
if old not in j:
    raise SystemExit('loadAllWorkersFallback block not found')
j=j.replace(old,new,1)

old=r'''    private void watchPendingWorkers(String companyId) {
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
'''
new=r'''    private void watchPendingWorkers(String companyId) {
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
        bossMembersListener = database.collection("companies").document(companyId).collection("members")
            .addSnapshotListener((snapshots, error) -> {
                if (error != null || snapshots == null || snapshots.isEmpty()) return;
                renderBossWorkerDocuments(new ArrayList<>(snapshots.getDocuments()), companyId);
            });
        if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
            bossCodeMembersListener = database.collection("companyCodes").document(currentCompanyCode).collection("members")
                .addSnapshotListener((snapshots, error) -> {
                    if (error != null || snapshots == null || snapshots.isEmpty()) return;
                    renderBossWorkerDocuments(new ArrayList<>(snapshots.getDocuments()), companyId);
                });
        }
    }
'''
if old not in j:
    raise SystemExit('watchPendingWorkers realtime block not found')
j=j.replace(old,new,1)

old=r'''    private void removeWorker(String workerId) {
        Map<String,Object> update = new HashMap<>();
        update.put("active", false);
        update.put("removed", true);
        update.put("removedByBoss", true);
        update.put("removedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        database.collection("workers").document(workerId).update(update);
    }
'''
new=r'''    private void removeWorker(String workerId) {
        Map<String,Object> update = new HashMap<>();
        update.put("active", false);
        update.put("removed", true);
        update.put("removedByBoss", true);
        update.put("removedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        database.collection("workers").document(workerId).set(update, com.google.firebase.firestore.SetOptions.merge());
        database.collection("users").document(workerId).set(update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyId != null && currentCompanyId.length() > 0)
            database.collection("companies").document(currentCompanyId).collection("members").document(workerId)
                .set(update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            database.collection("companyCodes").document(currentCompanyCode).collection("members").document(workerId)
                .set(update, com.google.firebase.firestore.SetOptions.merge());
    }
'''
if old not in j:
    raise SystemExit('removeWorker block not found')
j=j.replace(old,new,1)

marker='''    private long noticeMillis(Map<String,Object> item) {'''
helper=r'''    private void upsertSharedNotification(Map<String,Object> incoming) {
        if (incoming == null) return;
        String id = String.valueOf(incoming.get("id") == null ? "" : incoming.get("id"));
        if (id.length() == 0) return;
        for (int i=0; i<currentNotifications.size(); i++) {
            String existing = String.valueOf(currentNotifications.get(i).get("id") == null ? "" : currentNotifications.get(i).get("id"));
            if (id.equals(existing)) { currentNotifications.set(i, incoming); return; }
        }
        currentNotifications.add(incoming);
    }

    private Map<String,Object> sharedNoticeFromDocument(DocumentSnapshot d) {
        Map<String,Object> n = new HashMap<>(d.getData() == null ? new HashMap<>() : d.getData());
        n.put("id", d.getId());
        if (d.getTimestamp("createdAt") != null) n.put("createdAtMillis", d.getTimestamp("createdAt").toDate().getTime());
        return n;
    }

    private void consumeSharedNoticeSnapshot(com.google.firebase.firestore.QuerySnapshot snap) {
        if (snap == null) return;
        for (DocumentSnapshot d : snap.getDocuments()) upsertSharedNotification(sharedNoticeFromDocument(d));
        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
        pushNotifications();
    }

    private void watchWorkerNoticeSubcollections(String companyCode, String companyId) {
        if (companyCode != null && companyCode.length() > 0) {
            notificationListener = database.collection("companyCodes").document(companyCode).collection("notices").limit(50)
                .addSnapshotListener((snap,error) -> { if (error == null && snap != null) consumeSharedNoticeSnapshot(snap); });
        }
        if (companyId != null && companyId.length() > 0) {
            notificationFallbackListener = database.collection("companies").document(companyId).collection("notices").limit(50)
                .addSnapshotListener((snap,error) -> { if (error == null && snap != null) consumeSharedNoticeSnapshot(snap); });
            notificationCompanyListener = database.collection("companies").document(companyId)
                .addSnapshotListener((doc,error) -> {
                    if (error != null || doc == null || !doc.exists()) return;
                    Object raw = doc.get("latestNotice");
                    if (raw instanceof Map) {
                        Map<String,Object> n = new HashMap<>((Map<String,Object>)raw);
                        upsertSharedNotification(n);
                        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                        pushNotifications();
                    }
                });
        }
        if (companyCode != null && companyCode.length() > 0) {
            notificationCodeListener = database.collection("companyCodes").document(companyCode)
                .addSnapshotListener((doc,error) -> {
                    if (error != null || doc == null || !doc.exists()) return;
                    Object raw = doc.get("latestNotice");
                    if (raw instanceof Map) {
                        Map<String,Object> n = new HashMap<>((Map<String,Object>)raw);
                        upsertSharedNotification(n);
                        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                        pushNotifications();
                    }
                });
        }
    }

'''
if marker not in j:
    raise SystemExit('noticeMillis marker not found')
j=j.replace(marker,helper+marker,1)

old=r'''        if ("worker".equals(currentRole) && currentCompanyCode != null && currentCompanyCode.length() > 0) {
            watchWorkerSharedNotifications(currentCompanyCode);
            return;
        }'''
new=r'''        if ("worker".equals(currentRole)) {
            watchWorkerNoticeSubcollections(currentCompanyCode, currentCompanyId);
            return;
        }'''
if old not in j:
    raise SystemExit('worker watchNotifications branch not found')
j=j.replace(old,new,1)

old=r'''        database.collection("notifications").add(n)
            .addOnSuccessListener(v -> {
                lastChosenFileUri = null;
                page.evaluateJavascript("window.mbNoticeSent && window.mbNoticeSent(true,'સૂચના મોકલાઈ ગઈ')", null);
            })
            .addOnFailureListener(e -> page.evaluateJavascript("window.mbNoticeSent && window.mbNoticeSent(false,'સૂચના મોકલી શકાઈ નથી')", null));'''
new=r'''        database.collection("notifications").add(n)
            .addOnSuccessListener(ref -> {
                long now = System.currentTimeMillis();
                Map<String,Object> shared = new HashMap<>();
                shared.put("id", ref.getId());
                shared.put("companyId", currentCompanyId == null ? "" : currentCompanyId);
                shared.put("companyCode", currentCompanyCode == null ? "" : currentCompanyCode);
                shared.put("companyName", currentCompanyName == null ? "" : currentCompanyName);
                shared.put("senderUid", user.getUid());
                shared.put("text", clean);
                shared.put("imageBase64", image);
                shared.put("createdAtMillis", now);
                shared.put("createdAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
                    database.collection("companyCodes").document(currentCompanyCode).collection("notices").document(ref.getId())
                        .set(shared, com.google.firebase.firestore.SetOptions.merge());
                    Map<String,Object> latest = new HashMap<>(shared); latest.remove("createdAt");
                    database.collection("companyCodes").document(currentCompanyCode)
                        .set(java.util.Collections.singletonMap("latestNotice", latest), com.google.firebase.firestore.SetOptions.merge());
                }
                if (currentCompanyId != null && currentCompanyId.length() > 0) {
                    database.collection("companies").document(currentCompanyId).collection("notices").document(ref.getId())
                        .set(shared, com.google.firebase.firestore.SetOptions.merge());
                    Map<String,Object> latest = new HashMap<>(shared); latest.remove("createdAt");
                    database.collection("companies").document(currentCompanyId)
                        .set(java.util.Collections.singletonMap("latestNotice", latest), com.google.firebase.firestore.SetOptions.merge());
                }
                lastChosenFileUri = null;
                page.evaluateJavascript("window.mbNoticeSent && window.mbNoticeSent(true,'સૂચના મોકલાઈ ગઈ')", null);
            })
            .addOnFailureListener(e -> page.evaluateJavascript("window.mbNoticeSent && window.mbNoticeSent(false,'સૂચના મોકલી શકાઈ નથી')", null));'''
if old not in j:
    raise SystemExit('send notification add block not found')
j=j.replace(old,new,1)

old='''    private void clearBossWorkersListener() {
        if (bossWorkersListener != null) {
            bossWorkersListener.remove();
            bossWorkersListener = null;
        }
    }'''
new='''    private void clearBossWorkersListener() {
        if (bossWorkersListener != null) { bossWorkersListener.remove(); bossWorkersListener = null; }
        if (bossMembersListener != null) { bossMembersListener.remove(); bossMembersListener = null; }
        if (bossCodeMembersListener != null) { bossCodeMembersListener.remove(); bossCodeMembersListener = null; }
    }'''
if old not in j:
    raise SystemExit('clearBossWorkersListener block not found')
j=j.replace(old,new,1)

old='''    private void clearNotificationListener() { if (notificationListener != null) notificationListener.remove(); notificationListener = null; }'''
new='''    private void clearNotificationListener() {
        if (notificationListener != null) notificationListener.remove(); notificationListener = null;
        if (notificationFallbackListener != null) notificationFallbackListener.remove(); notificationFallbackListener = null;
        if (notificationCompanyListener != null) notificationCompanyListener.remove(); notificationCompanyListener = null;
        if (notificationCodeListener != null) notificationCodeListener.remove(); notificationCodeListener = null;
    }'''
if old not in j:
    raise SystemExit('clearNotificationListener block not found')
j=j.replace(old,new,1)

java.write_text(j)
b=root/'app/build.gradle'
t=b.read_text()
t=re.sub(r'versionCode\s+\d+','versionCode 65',t,count=1)
t=re.sub(r"versionName\s+'[^']+'","versionName '3.2.7'",t,count=1)
b.write_text(t)
print('v3.2.7 redundant membership + notification sync applied')
