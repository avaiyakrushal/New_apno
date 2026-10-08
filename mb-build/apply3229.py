from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 86","versionCode 87").replace("versionName '3.2.28'","versionName '3.2.29'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

old="""    private String bossLiveCompanyId;
    private ListenerRegistration diaryEntriesListener;
"""
new="""    private String bossLiveCompanyId;
    private final android.os.Handler eventualSyncHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private boolean eventualSyncStarted = false;
    private long bossServerRefreshGeneration = 0L;
    private static final long EVENTUAL_SYNC_INTERVAL_MS = 30L * 60L * 1000L;
    private final Runnable eventualSyncRunnable = new Runnable() {
        @Override public void run() {
            runEventualSyncNow();
            eventualSyncHandler.postDelayed(this, EVENTUAL_SYNC_INTERVAL_MS);
        }
    };
    private ListenerRegistration diaryEntriesListener;
"""
if old not in s: raise SystemExit("eventual sync field anchor missing")
s=s.replace(old,new,1)

# Start fallback loop after boss listeners are wired.
old="""        refreshBossWorkersCanonical(companyId);
    }

    private Map<String,Object> calculateMonthFromEntries"""
new="""        refreshBossWorkersCanonical(companyId);
        startEventualSyncLoop();
    }

    private Map<String,Object> calculateMonthFromEntries"""
if old not in s: raise SystemExit("boss start loop anchor missing")
s=s.replace(old,new,1)

# Worker live snapshot also starts the same safety loop once.
old="""                pushCloudEntries();
                if ("worker".equals(currentRole)) rebuildWorkerSummaryFromSnapshot(active, snap);
            });
"""
new="""                pushCloudEntries();
                if ("worker".equals(currentRole)) {
                    rebuildWorkerSummaryFromSnapshot(active, snap);
                    startEventualSyncLoop();
                }
            });
"""
if old not in s: raise SystemExit("worker start loop anchor missing")
s=s.replace(old,new,1)

# Insert fallback implementation before the existing boss render method.
anchor="""    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
"""
helpers="""    private void startEventualSyncLoop() {
        if (eventualSyncStarted) return;
        eventualSyncStarted = true;
        eventualSyncHandler.post(this::runEventualSyncNow);
        eventualSyncHandler.postDelayed(eventualSyncRunnable, EVENTUAL_SYNC_INTERVAL_MS);
    }

    private void runEventualSyncNow() {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null) return;
        database.enableNetwork().addOnCompleteListener(task -> {
            if ("boss".equals(currentRole)) {
                refreshBossWorkersServerFallback();
                refreshBossNoticesServerFallback();
            } else if ("worker".equals(currentRole)) {
                refreshWorkerEntriesServerFallback(user);
                refreshWorkerNoticesServerFallback();
            }
        });
    }

    private void refreshBossWorkersServerFallback() {
        final String companyId = currentCompanyId == null ? "" : currentCompanyId;
        final String companyCode = currentCompanyCode == null ? "" : currentCompanyCode;
        if (!"boss".equals(currentRole) || companyId.length() == 0) return;

        final long generation = ++bossServerRefreshGeneration;
        final Map<String,DocumentSnapshot> merged = new HashMap<>();
        final List<com.google.firebase.firestore.Query> queries = new ArrayList<>();
        final List<Boolean> onlyWorkers = new ArrayList<>();
        final List<Boolean> overwrite = new ArrayList<>();

        queries.add(database.collection("workers").whereEqualTo("companyId", companyId)); onlyWorkers.add(false); overwrite.add(true);
        queries.add(database.collection("workers").whereEqualTo("bossUid", companyId)); onlyWorkers.add(false); overwrite.add(true);
        queries.add(database.collection("users").whereEqualTo("companyId", companyId)); onlyWorkers.add(true); overwrite.add(false);
        queries.add(database.collection("users").whereEqualTo("bossUid", companyId)); onlyWorkers.add(true); overwrite.add(false);
        queries.add(database.collection("companies").document(companyId).collection("members")); onlyWorkers.add(true); overwrite.add(false);
        if (companyCode.length() > 0) {
            queries.add(database.collection("workers").whereEqualTo("companyCode", companyCode)); onlyWorkers.add(false); overwrite.add(true);
            queries.add(database.collection("users").whereEqualTo("companyCode", companyCode)); onlyWorkers.add(true); overwrite.add(false);
            queries.add(database.collection("companyCodes").document(companyCode).collection("members")); onlyWorkers.add(true); overwrite.add(false);
        }

        final java.util.concurrent.atomic.AtomicInteger remaining = new java.util.concurrent.atomic.AtomicInteger(queries.size());
        for (int i=0; i<queries.size(); i++) {
            final boolean filterWorkers = onlyWorkers.get(i);
            final boolean replace = overwrite.get(i);
            queries.get(i).get(com.google.firebase.firestore.Source.SERVER).addOnCompleteListener(task -> {
                if (generation != bossServerRefreshGeneration) return;
                if (task.isSuccessful() && task.getResult() != null)
                    addBossUnionDocs(merged, task.getResult(), filterWorkers, replace);
                if (remaining.decrementAndGet() == 0) {
                    FirebaseUser active = auth.getCurrentUser();
                    if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId)) return;
                    List<DocumentSnapshot> docs = new ArrayList<>(merged.values());
                    if (docs.isEmpty()) {
                        refreshBossWorkersCanonical(companyId);
                        return;
                    }
                    for (DocumentSnapshot worker : docs) backfillBossWorkerMembership(worker, companyId, companyCode);
                    renderBossWorkerDocuments(docs, companyId);
                    refreshBossEntriesServerFallback(docs, companyId);
                }
            });
        }
    }

    private void refreshBossEntriesServerFallback(List<DocumentSnapshot> workers, String companyId) {
        if (workers == null) return;
        for (DocumentSnapshot worker : workers) {
            if (worker == null || Boolean.TRUE.equals(worker.getBoolean("removed"))) continue;
            final String uid = worker.getId();
            final String mode = safe(worker.getString("mode"));
            database.collection("diaryEntries").document(uid).collection("items")
                .get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(snap -> {
                    FirebaseUser active = auth.getCurrentUser();
                    if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId)) return;
                    bossLiveEntrySummaries.put(uid, calculateMonthFromEntries(snap, currentMonthKey(), mode));
                    renderBossLiveDashboard();
                });
        }
    }

    private void refreshWorkerEntriesServerFallback(FirebaseUser user) {
        if (user == null || !"worker".equals(currentRole)) return;
        database.collection("diaryEntries").document(user.getUid()).collection("items")
            .get(com.google.firebase.firestore.Source.SERVER)
            .addOnSuccessListener(snap -> rebuildWorkerSummaryFromSnapshot(user, snap));
    }

    private void mergeServerNotices(com.google.firebase.firestore.QuerySnapshot snap) {
        if (snap == null) return;
        Map<String,Object> newest = null;
        long newestMillis = Long.MIN_VALUE;
        for (DocumentSnapshot d : snap.getDocuments()) {
            Map<String,Object> n = sharedNoticeFromDocument(d);
            String id = String.valueOf(n.get("id") == null ? "" : n.get("id"));
            if (id.length() == 0 || isNoticeDeleted(id)) continue;
            upsertSharedNotification(n);
            long when = noticeMillis(n);
            if (when > newestMillis) { newestMillis = when; newest = n; }
        }
        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
        pushNotifications();
        if (newest != null && "worker".equals(currentRole)) postWorkerSystemNotificationIfNew(newest);
    }

    private void refreshWorkerNoticesServerFallback() {
        if (!"worker".equals(currentRole)) return;
        final String companyId = currentCompanyId == null ? "" : currentCompanyId;
        final String companyCode = currentCompanyCode == null ? "" : currentCompanyCode;
        if (companyId.length() > 0) {
            database.collection("companies").document(companyId).get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(doc -> {
                    if (doc != null && doc.exists()) {
                        absorbDeletedNoticeIds(doc.get("deletedNoticeIds"));
                        Object latest = doc.get("latestNotice");
                        if (latest instanceof Map) {
                            Map<String,Object> n = new HashMap<>((Map<String,Object>) latest);
                            String id = String.valueOf(n.get("id") == null ? "" : n.get("id"));
                            if (!isNoticeDeleted(id)) {
                                upsertSharedNotification(n);
                                pushNotifications();
                                postWorkerSystemNotificationIfNew(n);
                            }
                        }
                    }
                });
            database.collection("companies").document(companyId).collection("notices")
                .get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(this::mergeServerNotices);
        }
        if (companyCode.length() > 0) {
            database.collection("companyCodes").document(companyCode).get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(doc -> {
                    if (doc != null && doc.exists()) absorbDeletedNoticeIds(doc.get("deletedNoticeIds"));
                });
            database.collection("companyCodes").document(companyCode).collection("notices")
                .get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(this::mergeServerNotices);
        }
    }

    private void refreshBossNoticesServerFallback() {
        if (!"boss".equals(currentRole)) return;
        final String companyId = currentCompanyId == null ? "" : currentCompanyId;
        if (companyId.length() == 0) return;
        database.collection("notifications").whereEqualTo("companyId", companyId)
            .get(com.google.firebase.firestore.Source.SERVER)
            .addOnSuccessListener(this::mergeServerNotices);
    }

"""
if anchor not in s: raise SystemExit("render boss anchor missing")
s=s.replace(anchor,helpers+anchor,1)

p.write_text(s)
print("v3.2.29 30-minute server fallback sync applied")
