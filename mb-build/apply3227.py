from pathlib import Path
import sys, re

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 84","versionCode 85").replace("versionName '3.2.26'","versionName '3.2.27'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

# Extra live membership/query triggers + per-worker entry listeners
old="""    private ListenerRegistration bossMembersListener;
    private ListenerRegistration bossCodeMembersListener;
    private ListenerRegistration bossUsersListener;
    private ListenerRegistration diaryEntriesListener;
"""
new="""    private ListenerRegistration bossMembersListener;
    private ListenerRegistration bossCodeMembersListener;
    private ListenerRegistration bossUsersListener;
    private ListenerRegistration bossWorkersCodeListener;
    private ListenerRegistration bossWorkersBossUidListener;
    private ListenerRegistration bossUsersCodeListener;
    private ListenerRegistration bossUsersBossUidListener;
    private final Map<String,ListenerRegistration> bossEntryListeners = new HashMap<>();
    private final Map<String,Map<String,Object>> bossLiveEntrySummaries = new HashMap<>();
    private final List<DocumentSnapshot> bossLiveWorkerDocs = new ArrayList<>();
    private String bossLiveCompanyId;
    private ListenerRegistration diaryEntriesListener;
"""
if old not in s: raise SystemExit("listener field anchor missing")
s=s.replace(old,new,1)

# Replace one-shot boss dashboard reads with realtime per-worker entry listeners
old="""    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
        String month = currentMonthKey();
        List<DocumentSnapshot> stable = new ArrayList<>(docs);
        stable.sort((a,b) -> Long.compare(workerJoinedMillis(b), workerJoinedMillis(a)));
        long revision = ++bossWorkerRenderRevision;
        renderBossWorkers(stable, null, month);
        refreshBossDashboardFromEntries(stable, companyId, month, revision);
    }
"""
new="""    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
        List<DocumentSnapshot> stable = new ArrayList<>(docs);
        stable.sort((a,b) -> Long.compare(workerJoinedMillis(b), workerJoinedMillis(a)));
        ++bossWorkerRenderRevision;
        bossLiveCompanyId = companyId;
        bossLiveWorkerDocs.clear();
        bossLiveWorkerDocs.addAll(stable);
        attachBossEntryListeners(stable, companyId);
        renderBossLiveDashboard();
    }

    private void attachBossEntryListeners(List<DocumentSnapshot> workers, String companyId) {
        Set<String> desired = new HashSet<>();
        for (DocumentSnapshot worker : workers) {
            if (worker == null || Boolean.TRUE.equals(worker.getBoolean("removed"))) continue;
            desired.add(worker.getId());
        }

        List<String> stale = new ArrayList<>();
        for (String uid : bossEntryListeners.keySet()) if (!desired.contains(uid)) stale.add(uid);
        for (String uid : stale) {
            ListenerRegistration reg = bossEntryListeners.remove(uid);
            if (reg != null) reg.remove();
            bossLiveEntrySummaries.remove(uid);
        }

        for (DocumentSnapshot worker : workers) {
            if (worker == null || Boolean.TRUE.equals(worker.getBoolean("removed"))) continue;
            final String uid = worker.getId();
            if (bossEntryListeners.containsKey(uid)) continue;
            ListenerRegistration reg = database.collection("diaryEntries").document(uid).collection("items")
                .addSnapshotListener((snap,error) -> {
                    FirebaseUser active = auth.getCurrentUser();
                    if (error != null || snap == null || active == null || !"boss".equals(currentRole)
                        || currentCompanyId == null || !currentCompanyId.equals(companyId)) return;
                    DocumentSnapshot currentWorker = null;
                    for (DocumentSnapshot one : bossLiveWorkerDocs) if (uid.equals(one.getId())) { currentWorker = one; break; }
                    if (currentWorker == null) return;
                    String mode = safe(currentWorker.getString("mode"));
                    bossLiveEntrySummaries.put(uid, calculateMonthFromEntries(snap, currentMonthKey(), mode));
                    renderBossLiveDashboard();
                });
            bossEntryListeners.put(uid, reg);
        }
    }

    private void renderBossLiveDashboard() {
        FirebaseUser active = auth.getCurrentUser();
        if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || bossLiveCompanyId == null
            || !currentCompanyId.equals(bossLiveCompanyId)) return;
        List<DocumentSnapshot> stable = new ArrayList<>(bossLiveWorkerDocs);
        stable.sort((a,b) -> Long.compare(workerJoinedMillis(b), workerJoinedMillis(a)));
        renderBossWorkers(stable, new HashMap<>(bossLiveEntrySummaries), currentMonthKey());
    }
"""
if old not in s: raise SystemExit("renderBossWorkerDocuments block missing")
s=s.replace(old,new,1)

# Add every relevant membership query as a change trigger so partial/legacy records still wake the union refresh.
anchor="""        bossUsersListener = database.collection("users").whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });

        refreshBossWorkersCanonical(companyId);
"""
insert="""        bossUsersListener = database.collection("users").whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });

        bossWorkersBossUidListener = database.collection("workers").whereEqualTo("bossUid", companyId)
            .addSnapshotListener((snapshots,error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });
        bossUsersBossUidListener = database.collection("users").whereEqualTo("bossUid", companyId)
            .addSnapshotListener((snapshots,error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });

        if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
            final String code = currentCompanyCode;
            bossWorkersCodeListener = database.collection("workers").whereEqualTo("companyCode", code)
                .addSnapshotListener((snapshots,error) -> {
                    if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
                });
            bossUsersCodeListener = database.collection("users").whereEqualTo("companyCode", code)
                .addSnapshotListener((snapshots,error) -> {
                    if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
                });
        }

        refreshBossWorkersCanonical(companyId);
"""
if anchor not in s: raise SystemExit("watchPendingWorkers users anchor missing")
s=s.replace(anchor,insert,1)

# Make worker summary update directly from the live entry snapshot instead of issuing an extra delayed get().
old="""                pushCloudEntries();
                if ("worker".equals(currentRole)) rebuildWorkerSummaryFromCloud(active);
            });
"""
new="""                pushCloudEntries();
                if ("worker".equals(currentRole)) rebuildWorkerSummaryFromSnapshot(active, snap);
            });
"""
if old not in s: raise SystemExit("worker cloud listener anchor missing")
s=s.replace(old,new,1)

# Refactor summary function to consume snapshot immediately.
start=s.find("    private void rebuildWorkerSummaryFromCloud(FirebaseUser requestedUser) {")
end=s.find("    private void syncWorkerSummaryFromWeb(String json) {", start)
if start<0 or end<0: raise SystemExit("summary function boundaries missing")
old_block=s[start:end]
new_block="""    private void rebuildWorkerSummaryFromCloud(FirebaseUser requestedUser) {
        if (requestedUser == null || !"worker".equals(currentRole)) return;
        final String uid = requestedUser.getUid();
        database.collection("diaryEntries").document(uid).collection("items").get()
            .addOnSuccessListener(snap -> rebuildWorkerSummaryFromSnapshot(requestedUser, snap));
    }

    private void rebuildWorkerSummaryFromSnapshot(FirebaseUser requestedUser, com.google.firebase.firestore.QuerySnapshot snap) {
        if (requestedUser == null || snap == null || !"worker".equals(currentRole)) return;
        final String uid = requestedUser.getUid();
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
            out.put("diamonds",t.get("diamonds")); out.put("hours",t.get("hours"));
            out.put("earnings",earnings); out.put("withdrawal",withdrawal);
            out.put("remaining",earnings-withdrawal);
            monthly.put(e.getKey(),out);
        }

        String nowMonth=new SimpleDateFormat("yyyy-MM",Locale.US).format(new Date());
        Map<String,Object> current = monthly.get(nowMonth) instanceof Map ? (Map<String,Object>) monthly.get(nowMonth) : new HashMap<>();
        double diamonds=mapNumber(current,"diamonds"), hours=mapNumber(current,"hours"),
            earnings=mapNumber(current,"earnings"), withdrawal=mapNumber(current,"withdrawal");
        Map<String,Object> update=new HashMap<>();
        update.put("summaryMonth",nowMonth);
        update.put("monthDiamonds",Math.round(diamonds));
        update.put("monthHours",hours);
        update.put("monthEarnings",earnings);
        update.put("monthWithdrawal",withdrawal);
        update.put("monthRemaining",earnings-withdrawal);
        update.put("monthlySummaries",monthly);
        if ("diamond".equals(currentMode) || "hour".equals(currentMode)) update.put("mode",currentMode);
        update.put("summaryUpdatedAt",com.google.firebase.firestore.FieldValue.serverTimestamp());

        // Update all mirrors so every boss-side listener can react immediately.
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("workers").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyId != null && currentCompanyId.length() > 0)
            batch.set(database.collection("companies").document(currentCompanyId).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            batch.set(database.collection("companyCodes").document(currentCompanyCode).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.commit();
    }

"""
s=s[:start]+new_block+s[end:]

# Mark each entry mutation with server update time. Helps cache reconciliation and guarantees a remote metadata change.
old="""                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                DocumentReference ref = database.collection("diaryEntries").document(user.getUid()).collection("items").document(id);
"""
new="""                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                m.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                DocumentReference ref = database.collection("diaryEntries").document(user.getUid()).collection("items").document(id);
"""
if old not in s: raise SystemExit("entry mutation anchor missing")
s=s.replace(old,new,1)

# Clear all newly-added realtime listeners/maps.
old="""        if (bossCodeMembersListener != null) { bossCodeMembersListener.remove(); bossCodeMembersListener = null; }
        if (bossUsersListener != null) { bossUsersListener.remove(); bossUsersListener = null; }
    }
"""
new="""        if (bossCodeMembersListener != null) { bossCodeMembersListener.remove(); bossCodeMembersListener = null; }
        if (bossUsersListener != null) { bossUsersListener.remove(); bossUsersListener = null; }
        if (bossWorkersCodeListener != null) { bossWorkersCodeListener.remove(); bossWorkersCodeListener = null; }
        if (bossWorkersBossUidListener != null) { bossWorkersBossUidListener.remove(); bossWorkersBossUidListener = null; }
        if (bossUsersCodeListener != null) { bossUsersCodeListener.remove(); bossUsersCodeListener = null; }
        if (bossUsersBossUidListener != null) { bossUsersBossUidListener.remove(); bossUsersBossUidListener = null; }
        for (ListenerRegistration reg : new ArrayList<>(bossEntryListeners.values())) if (reg != null) reg.remove();
        bossEntryListeners.clear();
        bossLiveEntrySummaries.clear();
        bossLiveWorkerDocs.clear();
        bossLiveCompanyId = null;
    }
"""
if old not in s: raise SystemExit("clearBossWorkersListener anchor missing")
s=s.replace(old,new,1)

p.write_text(s)
print("v3.2.27 direct realtime sync fixes applied")
