from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 83","versionCode 84").replace("versionName '3.2.25'","versionName '3.2.26'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

old="""    private void loadBossUnionUsers(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("users").whereEqualTo("companyId", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                finishBossWorkerUnion(companyId, loadRevision, merged);
            });
    }
"""
new="""    private void loadBossUnionUsers(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("users").whereEqualTo("companyId", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                loadBossUnionUsersByBossUid(companyId, loadRevision, merged);
            });
    }

    private void loadBossUnionUsersByBossUid(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        database.collection("users").whereEqualTo("bossUid", companyId).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                loadBossUnionUsersByCode(companyId, loadRevision, merged);
            });
    }

    private void loadBossUnionUsersByCode(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        String companyCode = currentCompanyCode == null ? "" : currentCompanyCode;
        if (companyCode.length() == 0) {
            finishBossWorkerUnion(companyId, loadRevision, merged);
            return;
        }
        database.collection("users").whereEqualTo("companyCode", companyCode).get()
            .addOnCompleteListener(task -> {
                if (loadRevision != bossWorkerLoadRevision) return;
                if (task.isSuccessful()) addBossUnionDocs(merged, task.getResult(), true, false);
                finishBossWorkerUnion(companyId, loadRevision, merged);
            });
    }
"""
if old not in s: raise SystemExit("loadBossUnionUsers block missing")
s=s.replace(old,new,1)

old="""    private void finishBossWorkerUnion(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        List<DocumentSnapshot> docs = new ArrayList<>(merged.values());
        if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
        else renderBossWorkerDocuments(new ArrayList<>(), companyId);
    }
"""
new="""    private void finishBossWorkerUnion(String companyId, long loadRevision, Map<String,DocumentSnapshot> merged) {
        if (loadRevision != bossWorkerLoadRevision) return;
        List<DocumentSnapshot> docs = new ArrayList<>(merged.values());
        if (!docs.isEmpty()) {
            for (DocumentSnapshot worker : docs) backfillBossWorkerMembership(worker, companyId, currentCompanyCode);
            renderBossWorkerDocuments(docs, companyId);
        } else renderBossWorkerDocuments(new ArrayList<>(), companyId);
    }

    private void backfillBossWorkerMembership(DocumentSnapshot snapshot, String companyId, String companyCode) {
        if (snapshot == null || snapshot.getId() == null || snapshot.getId().length() == 0) return;
        if (Boolean.TRUE.equals(snapshot.getBoolean("removed"))) return;
        String sourceCollection = snapshot.getReference().getParent().getId();
        boolean canonical = "workers".equals(sourceCollection)
            && companyId.equals(safe(snapshot.getString("companyId")))
            && companyId.equals(safe(snapshot.getString("bossUid")))
            && (companyCode == null || companyCode.length() == 0 || companyCode.equalsIgnoreCase(safe(snapshot.getString("companyCode"))));
        if (canonical) return;

        Map<String,Object> membership = new HashMap<>();
        if (snapshot.getData() != null) membership.putAll(snapshot.getData());
        membership.put("uid", snapshot.getId());
        membership.put("role", "worker");
        membership.put("companyId", companyId);
        membership.put("bossUid", companyId);
        if (companyCode != null && companyCode.length() > 0) membership.put("companyCode", companyCode);
        membership.put("active", true);
        membership.put("removed", false);
        membership.put("joined", true);
        if (!(membership.get("joinedAtMillis") instanceof Number)) membership.put("joinedAtMillis", System.currentTimeMillis());
        membership.put("membershipRepairedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("workers").document(snapshot.getId()), membership, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(snapshot.getId()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length() > 0)
            batch.set(database.collection("companies").document(companyId).collection("members").document(snapshot.getId()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length() > 0)
            batch.set(database.collection("companyCodes").document(companyCode).collection("members").document(snapshot.getId()), membership, com.google.firebase.firestore.SetOptions.merge());
        batch.commit();
    }
"""
if old not in s: raise SystemExit("finishBossWorkerUnion block missing")
s=s.replace(old,new,1)

old="""    private void mirrorWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
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
"""
new="""    private Map<String,Object> normalizedWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        Map<String,Object> membership = new HashMap<>();
        if (worker != null) membership.putAll(worker);
        membership.put("uid", user.getUid());
        membership.put("role", "worker");
        membership.put("joined", true);
        membership.put("active", true);
        membership.put("removed", false);
        membership.put("companyId", companyId == null ? "" : companyId);
        membership.put("bossUid", companyId == null ? "" : companyId);
        membership.put("companyCode", companyCode == null ? "" : companyCode);
        if (!(membership.get("joinedAtMillis") instanceof Number)) membership.put("joinedAtMillis", System.currentTimeMillis());
        membership.put("membershipSyncedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        return membership;
    }

    private com.google.android.gms.tasks.Task<Void> commitWorkerMembershipBatch(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        Map<String,Object> membership = normalizedWorkerMembership(user, worker, companyId, companyCode);
        membership.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("workers").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length() > 0)
            batch.set(database.collection("companyCodes").document(companyCode).collection("members").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length() > 0)
            batch.set(database.collection("companies").document(companyId).collection("members").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        return batch.commit();
    }

    private void mirrorWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        if (user == null || worker == null) return;
        Map<String,Object> membership = normalizedWorkerMembership(user, worker, companyId, companyCode);
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("users").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length() > 0)
            batch.set(database.collection("companyCodes").document(companyCode).collection("members").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length() > 0)
            batch.set(database.collection("companies").document(companyId).collection("members").document(user.getUid()), membership, com.google.firebase.firestore.SetOptions.merge());
        batch.commit();
    }
"""
if old not in s: raise SystemExit("mirrorWorkerMembership block missing")
s=s.replace(old,new,1)

old="""        database.collection("workers").document(user.getUid())
            .set(worker, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> mirrorWorkerMembership(user, worker, companyId, companyCode));
        mirrorWorkerMembership(user, worker, companyId, companyCode);
"""
new="""        commitWorkerMembershipBatch(user, worker, companyId, companyCode);
"""
if old not in s: raise SystemExit("repairWorkerFromLocalMembership write block missing")
s=s.replace(old,new,1)

old="""                    database.collection("workers").document(user.getUid()).set(worker, com.google.firebase.firestore.SetOptions.merge())
                        .addOnSuccessListener(v -> {
"""
new="""                    commitWorkerMembershipBatch(user, worker, companyId, code)
                        .addOnSuccessListener(v -> {
"""
if old not in s: raise SystemExit("joinCompany worker write missing")
s=s.replace(old,new,1)

old="""                            mirrorWorkerMembership(user, worker, companyId, code);
                            grantRole(user, "worker", joinMode);
"""
new="""                            grantRole(user, "worker", joinMode);
"""
if old not in s: raise SystemExit("joinCompany mirror line missing")
s=s.replace(old,new,1)

s=s.replace('workerJoinStatus.setText("કંપનીમાં જોડાઈ શકાયું નથી. ફરી પ્રયાસ કરો.");',
            'workerJoinStatus.setText("કંપનીના કારીગર લિસ્ટમાં નામ સેવ થયું નથી. ફરી Join દબાવો.");',1)

p.write_text(s)
print("v3.2.26 membership batch + boss backfill fixes applied")
