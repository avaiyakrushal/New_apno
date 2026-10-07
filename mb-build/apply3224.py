from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 81","versionCode 82").replace("versionName '3.2.23'","versionName '3.2.24'")
gradle.write_text(s)

java=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=java.read_text()

s=s.replace(
"""    private long bossWorkerRenderRevision = 0L;
    private final Set<String> deletedNoticeIds = new HashSet<>();
""",
"""    private long bossWorkerRenderRevision = 0L;
    private long bossWorkerLoadRevision = 0L;
    private final Set<String> deletedNoticeIds = new HashSet<>();
"""
)

old = """    private void refreshBossWorkersCanonical(String companyId) {
        if (companyId == null || companyId.length() == 0) return;
        database.collection("workers").whereEqualTo("companyId", companyId).get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadBossWorkersFallback(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersFallback(companyId));
    }
"""

new = """    private void addBossUnionDocs(Map<String,DocumentSnapshot> merged, com.google.firebase.firestore.QuerySnapshot snap, boolean onlyWorkers, boolean overwrite) {
        if (snap == null) return;
        for (DocumentSnapshot d : snap.getDocuments()) {
            if (Boolean.TRUE.equals(d.getBoolean("removed"))) continue;
            if (onlyWorkers) {
                String role = safe(d.getString("role"));
                if (role.length() > 0 && !"worker".equals(role)) continue;
            }
            if (overwrite || !merged.containsKey(d.getId())) merged.put(d.getId(), d);
        }
    }

    private void finishBossWorkerUnion(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        List<DocumentSnapshot> docs = new ArrayList<>(merged.values());
        if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
        else renderBossWorkerDocuments(new ArrayList<>(), companyId);
    }

    private void loadBossUnionUsers(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("users").whereEqualTo("companyId", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                finishBossWorkerUnion(companyId, loadRevision, merged);
            });
    }

    private void loadBossUnionCodeMembers(String companyId, String companyCode, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        if (companyCode == null || companyCode.length() == 0) {
            loadBossUnionUsers(companyId, loadRevision, merged);
            return;
        }
        database.collection("companyCodes").document(companyCode).collection("members").get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                loadBossUnionUsers(companyId, loadRevision, merged);
            });
    }

    private void loadBossUnionCompanyMembers(String companyId, String companyCode, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("companies").document(companyId).collection("members").get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                loadBossUnionCodeMembers(companyId, companyCode, loadRevision, merged);
            });
    }

    private void loadBossUnionWorkerCode(String companyId, String companyCode, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        if (companyCode == null || companyCode.length() == 0) {
            loadBossUnionCompanyMembers(companyId, companyCode, loadRevision, merged);
            return;
        }
        database.collection("workers").whereEqualTo("companyCode", companyCode).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), false, true);
                loadBossUnionCompanyMembers(companyId, companyCode, loadRevision, merged);
            });
    }

    private void loadBossUnionBossUid(String companyId, String companyCode, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("workers").whereEqualTo("bossUid", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), false, true);
                loadBossUnionWorkerCode(companyId, companyCode, loadRevision, merged);
            });
    }

    private void refreshBossWorkersCanonical(String companyId) {
        if (companyId == null || companyId.length() == 0) return;
        final long loadRevision = ++bossWorkerLoadRevision;
        final String codeAtStart = currentCompanyCode == null ? "" : currentCompanyCode;
        final Map<String,DocumentSnapshot> merged = new HashMap<>();

        database.collection("workers").whereEqualTo("companyId", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), false, true);
                loadBossUnionBossUid(companyId, codeAtStart, loadRevision, merged);
            });
    }
"""

if old not in s:
    raise SystemExit("refreshBossWorkersCanonical block not found")
s=s.replace(old,new)

# Every successful worker join explicitly refreshes all mirror fields; include a monotonic timestamp for the boss list.
old_join = """                    worker.put("removed", false);
                    worker.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                    database.collection("workers").document(user.getUid()).set(worker, com.google.firebase.firestore.SetOptions.merge())
"""
new_join = """                    worker.put("removed", false);
                    worker.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                    worker.put("joinedAtMillis", System.currentTimeMillis());
                    database.collection("workers").document(user.getUid()).set(worker, com.google.firebase.firestore.SetOptions.merge())
"""
if old_join not in s:
    raise SystemExit("join worker timestamp block not found")
s=s.replace(old_join,new_join)

# Sort with joinedAtMillis fallback too.
old_sort = """        Timestamp t = worker.getTimestamp("joinedAt");
        if (t != null) return t.toDate().getTime();
        return 0L;
"""
new_sort = """        Timestamp t = worker.getTimestamp("joinedAt");
        if (t != null) return t.toDate().getTime();
        Object raw = worker.get("joinedAtMillis");
        if (raw instanceof Number) return ((Number) raw).longValue();
        return 0L;
"""
if old_sort not in s:
    raise SystemExit("workerJoinedMillis block not found")
s=s.replace(old_sort,new_sort)

java.write_text(s)
print("v3.2.24 boss worker list union + stale request fix applied")
