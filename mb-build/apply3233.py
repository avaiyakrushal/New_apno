from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 90","versionCode 91").replace("versionName '3.2.32'","versionName '3.2.33'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

old="""    private Map<String,Object> bossMonthSummary(DocumentSnapshot worker, Map<String,Map<String,Object>> live, String month) {
        if (live != null) {
            Map<String,Object> one = live.get(worker.getId());
            if (one != null) return one;
        }
        return monthSummary(worker, month);
    }
"""
new="""    @SuppressWarnings("unchecked")
    private boolean hasWorkerMonthSummary(DocumentSnapshot worker, String month) {
        if (worker == null || month == null) return false;
        Object raw = worker.get("monthlySummaries");
        if (raw instanceof Map && ((Map<?,?>) raw).get(month) instanceof Map) return true;
        return month.equals(safe(worker.getString("summaryMonth")));
    }

    private Map<String,Object> bossMonthSummary(DocumentSnapshot worker, Map<String,Map<String,Object>> live, String month) {
        // The worker summary document is the cross-device canonical dashboard source.
        // A direct diaryEntries listener is only a fallback. This prevents a stale cached
        // diary snapshot from overriding a newer Hira/Kalak total already published by worker.
        if (hasWorkerMonthSummary(worker, month)) return monthSummary(worker, month);
        if (live != null) {
            Map<String,Object> one = live.get(worker.getId());
            if (one != null) return one;
        }
        return monthSummary(worker, month);
    }
"""
if old not in s: raise SystemExit("bossMonthSummary anchor missing")
s=s.replace(old,new,1)

# Publish summary to canonical worker doc first, and mirrors independently.
anchor="""    private void syncWorkerSummaryFromWeb(String json) {
"""
helper="""    private void publishWorkerSummaryUpdate(FirebaseUser user, Map<String,Object> update) {
        if (user == null || update == null || !"worker".equals(currentRole)) return;
        final String uid = user.getUid();

        // Never make one denied mirror path block the canonical worker summary.
        database.collection("workers").document(uid)
            .set(update, com.google.firebase.firestore.SetOptions.merge())
            .addOnFailureListener(e -> eventualSyncHandler.postDelayed(this::runEventualSyncNow, 5000L));

        database.collection("users").document(uid)
            .set(update, com.google.firebase.firestore.SetOptions.merge());

        if (currentCompanyId != null && currentCompanyId.length() > 0)
            database.collection("companies").document(currentCompanyId).collection("members").document(uid)
                .set(update, com.google.firebase.firestore.SetOptions.merge());

        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            database.collection("companyCodes").document(currentCompanyCode).collection("members").document(uid)
                .set(update, com.google.firebase.firestore.SetOptions.merge());
    }

"""
if anchor not in s: raise SystemExit("summary helper insertion anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""        // Update all mirrors so every boss-side listener can react immediately.
        com.google.firebase.firestore.WriteBatch batch = database.batch();
        batch.set(database.collection("workers").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.set(database.collection("users").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyId != null && currentCompanyId.length() > 0)
            batch.set(database.collection("companies").document(currentCompanyId).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            batch.set(database.collection("companyCodes").document(currentCompanyCode).collection("members").document(uid), update, com.google.firebase.firestore.SetOptions.merge());
        batch.commit();
"""
new="""        // Publish the canonical summary and mirrors independently.
        publishWorkerSummaryUpdate(requestedUser, update);
"""
if old not in s: raise SystemExit("rebuild summary batch anchor missing")
s=s.replace(old,new,1)

old="""            if ("hour".equals(currentMode) || "diamond".equals(currentMode)) update.put("mode", currentMode);
            database.collection("workers").document(user.getUid()).set(update, com.google.firebase.firestore.SetOptions.merge());
        } catch (Exception ignored) {}
"""
new="""            if ("hour".equals(currentMode) || "diamond".equals(currentMode)) update.put("mode", currentMode);
            publishWorkerSummaryUpdate(user, update);
        } catch (Exception ignored) {}
"""
if old not in s: raise SystemExit("syncWorkerSummaryFromWeb write anchor missing")
s=s.replace(old,new,1)

old="""    private void refreshWorkerEntriesServerFallback(FirebaseUser user) {
        if (user == null || !"worker".equals(currentRole)) return;
        database.collection("diaryEntries").document(user.getUid()).collection("items")
            .get(com.google.firebase.firestore.Source.SERVER)
            .addOnSuccessListener(snap -> rebuildWorkerSummaryFromSnapshot(user, snap));
    }
"""
new="""    private void refreshWorkerEntriesServerFallback(FirebaseUser user) {
        if (user == null || !"worker".equals(currentRole)) return;
        final String uid = user.getUid();
        database.collection("diaryEntries").document(uid).collection("items")
            .get(com.google.firebase.firestore.Source.SERVER)
            .addOnSuccessListener(snap -> {
                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !uid.equals(active.getUid()) || !"worker".equals(currentRole)) return;

                // Feed the authoritative server snapshot back to JS. mbCloudEntries compares
                // this with phone-local entries and automatically re-uploads any missing Hira/
                // Kalak records, so a temporarily missed write is repaired on resume/30-min sync.
                currentCloudEntries.clear();
                for (DocumentSnapshot d : snap.getDocuments()) {
                    Map<String,Object> item = new HashMap<>(d.getData());
                    item.put("id", d.getId());
                    currentCloudEntries.add(item);
                }
                pushCloudEntries();
                rebuildWorkerSummaryFromSnapshot(user, snap);
            })
            .addOnFailureListener(e -> eventualSyncHandler.postDelayed(this::runEventualSyncNow, 10000L));
    }
"""
if old not in s: raise SystemExit("worker server fallback anchor missing")
s=s.replace(old,new,1)

old="""            if (writes == 0) return;
            batch.commit().addOnSuccessListener(v -> rebuildWorkerSummaryFromCloud(user));
        } catch (Exception ignored) {}
"""
new="""            if (writes == 0) return;
            batch.commit()
                .addOnSuccessListener(v -> refreshWorkerEntriesServerFallback(user))
                .addOnFailureListener(e -> eventualSyncHandler.postDelayed(this::runEventualSyncNow, 5000L));
        } catch (Exception ignored) {}
"""
if old not in s: raise SystemExit("syncEntries commit anchor missing")
s=s.replace(old,new,1)

old="""        database.collection("diaryEntries").document(user.getUid()).collection("items").document(id).delete()
            .addOnSuccessListener(v -> rebuildWorkerSummaryFromCloud(user));
"""
new="""        database.collection("diaryEntries").document(user.getUid()).collection("items").document(id).delete()
            .addOnSuccessListener(v -> refreshWorkerEntriesServerFallback(user))
            .addOnFailureListener(e -> eventualSyncHandler.postDelayed(this::runEventualSyncNow, 5000L));
"""
if old not in s: raise SystemExit("deleteEntry anchor missing")
s=s.replace(old,new,1)


# Reinstall/self-heal: do not let one denied mirror path block canonical worker membership.
old="""    private com.google.android.gms.tasks.Task<Void> commitWorkerMembershipBatch(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
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
"""
new="""    private com.google.android.gms.tasks.Task<Void> commitWorkerMembershipBatch(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        Map<String,Object> membership = normalizedWorkerMembership(user, worker, companyId, companyCode);
        membership.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

        com.google.android.gms.tasks.Task<Void> workerTask = database.collection("workers").document(user.getUid())
            .set(membership, com.google.firebase.firestore.SetOptions.merge());
        com.google.android.gms.tasks.Task<Void> userTask = database.collection("users").document(user.getUid())
            .set(membership, com.google.firebase.firestore.SetOptions.merge());

        if (companyCode != null && companyCode.length() > 0)
            database.collection("companyCodes").document(companyCode).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length() > 0)
            database.collection("companies").document(companyId).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());

        return com.google.android.gms.tasks.Tasks.whenAll(workerTask, userTask);
    }
"""
if old not in s: raise SystemExit("commitWorkerMembershipBatch anchor missing")
s=s.replace(old,new,1)

old="""    private void mirrorWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
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
new="""    private void mirrorWorkerMembership(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        if (user == null || worker == null) return;
        Map<String,Object> membership = normalizedWorkerMembership(user, worker, companyId, companyCode);
        database.collection("users").document(user.getUid())
            .set(membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyCode != null && companyCode.length() > 0)
            database.collection("companyCodes").document(companyCode).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());
        if (companyId != null && companyId.length() > 0)
            database.collection("companies").document(companyId).collection("members").document(user.getUid())
                .set(membership, com.google.firebase.firestore.SetOptions.merge());
    }
"""
if old not in s: raise SystemExit("mirrorWorkerMembership anchor missing")
s=s.replace(old,new,1)

anchor="""    private void showWorkerState(FirebaseUser user) {
"""
helper="""    private void restoreWorkerMembershipAfterReinstall(FirebaseUser user) {
        if (user == null) { showWorkerJoin(); return; }
        final String uid = user.getUid();
        database.collection("users").document(uid).get(com.google.firebase.firestore.Source.SERVER)
            .addOnCompleteListener(task -> {
                FirebaseUser active = auth.getCurrentUser();
                if (active == null || !uid.equals(active.getUid())) return;
                if (!task.isSuccessful() || task.getResult() == null || !task.getResult().exists()) {
                    showWorkerJoin();
                    workerJoinStatus.setText("કંપની કોડ નાખીને ફરી જોડાઓ");
                    return;
                }
                DocumentSnapshot profile = task.getResult();
                String role = safe(profile.getString("role"));
                String companyId = safe(profile.getString("companyId"));
                String companyName = safe(profile.getString("companyName"));
                String companyCode = safe(profile.getString("companyCode"));
                String mode = safe(profile.getString("mode"));
                if (!"worker".equals(role) || companyId.length() == 0) {
                    showWorkerJoin();
                    workerJoinStatus.setText("કંપની કોડ નાખીને ફરી જોડાઓ");
                    return;
                }
                if (!("hour".equals(mode) || "diamond".equals(mode))) mode = "diamond";
                final String fixedMode = mode;
                if (companyName.length() == 0) {
                    database.collection("companies").document(companyId).get(com.google.firebase.firestore.Source.SERVER)
                        .addOnCompleteListener(companyTask -> {
                            String name = "";
                            String code = companyCode;
                            if (companyTask.isSuccessful() && companyTask.getResult() != null && companyTask.getResult().exists()) {
                                name = safe(companyTask.getResult().getString("name"));
                                if (code.length() == 0) code = safe(companyTask.getResult().getString("code"));
                            }
                            finishWorkerMembershipRestore(active, profile, companyId, name, code, fixedMode);
                        });
                } else {
                    finishWorkerMembershipRestore(active, profile, companyId, companyName, companyCode, fixedMode);
                }
            });
    }

    private void finishWorkerMembershipRestore(FirebaseUser user, DocumentSnapshot profile, String companyId, String companyName, String companyCode, String mode) {
        if (user == null || companyId == null || companyId.length() == 0) { showWorkerJoin(); return; }
        currentCompanyId = companyId;
        currentCompanyName = companyName == null ? "" : companyName;
        currentCompanyCode = companyCode == null ? "" : companyCode;
        currentMode = ("hour".equals(mode) || "diamond".equals(mode)) ? mode : "diamond";

        getPreferences(MODE_PRIVATE).edit()
            .putString("worker_company_id", currentCompanyId)
            .putString("worker_company_name", currentCompanyName)
            .putString("worker_company_code", currentCompanyCode)
            .putString("worker_mode", currentMode)
            .putBoolean("worker_joined", true)
            .apply();

        Map<String,Object> worker = new HashMap<>();
        if (profile != null && profile.getData() != null) worker.putAll(profile.getData());
        worker.put("companyId", currentCompanyId);
        worker.put("bossUid", currentCompanyId);
        worker.put("companyName", currentCompanyName);
        worker.put("companyCode", currentCompanyCode);
        worker.put("mode", currentMode);
        worker.put("active", true);
        worker.put("removed", false);

        commitWorkerMembershipBatch(user, worker, currentCompanyId, currentCompanyCode)
            .addOnCompleteListener(t -> grantRole(user, "worker", currentMode));
    }

"""
if anchor not in s: raise SystemExit("showWorkerState insertion anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""                    } else showWorkerJoin();
                    return;
                }
"""
new="""                    } else restoreWorkerMembershipAfterReinstall(active);
                    return;
                }
"""
if old not in s: raise SystemExit("missing-worker restore anchor missing")
s=s.replace(old,new,1)

old="""                    currentCompanyId = null;
                    currentCompanyName = null;
                    currentCompanyCode = null;
                    showWorkerJoin();
                    workerJoinStatus.setText("કંપની કોડ નાખીને કંપનીમાં જોડાઓ");
                    return;
"""
new="""                    currentCompanyId = null;
                    currentCompanyName = null;
                    currentCompanyCode = null;
                    restoreWorkerMembershipAfterReinstall(active);
                    return;
"""
if old not in s: raise SystemExit("incomplete-worker restore anchor missing")
s=s.replace(old,new,1)

# If direct boss diary listener is denied/stale, immediately fall back to worker summary doc.
old="""                .addSnapshotListener((snap,error) -> {
                    FirebaseUser active = auth.getCurrentUser();
                    if (error != null || snap == null || active == null || !"boss".equals(currentRole)
                        || currentCompanyId == null || !currentCompanyId.equals(companyId)) return;
"""
new="""                .addSnapshotListener((snap,error) -> {
                    FirebaseUser active = auth.getCurrentUser();
                    if (error != null || snap == null) {
                        bossLiveEntrySummaries.remove(uid);
                        renderBossLiveDashboard();
                        return;
                    }
                    if (active == null || !"boss".equals(currentRole)
                        || currentCompanyId == null || !currentCompanyId.equals(companyId)) return;
"""
if old not in s: raise SystemExit("boss entry listener fallback anchor missing")
s=s.replace(old,new,1)


p.write_text(s)
print("v3.2.33 Hira/Kalak cross-device sync repair applied")
