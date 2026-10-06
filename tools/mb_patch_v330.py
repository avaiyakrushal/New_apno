from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

marker='''    private void showWorkerState(FirebaseUser user) {'''
helper=r'''    private void repairWorkerFromLocalMembership(FirebaseUser user, String companyId, String companyName, String companyCode, String mode) {
        if (user == null || companyId == null || companyId.length() == 0) return;
        String fixedMode = ("hour".equals(mode) || "diamond".equals(mode)) ? mode : "diamond";
        Map<String,Object> worker = new HashMap<>();
        worker.put("companyId", companyId);
        worker.put("bossUid", companyId);
        worker.put("companyName", companyName == null ? "" : companyName);
        worker.put("companyCode", companyCode == null ? "" : companyCode);
        worker.put("mode", fixedMode);
        worker.put("active", true);
        worker.put("removed", false);
        worker.put("uid", user.getUid());
        String display = safe(user.getDisplayName());
        if (display.length() > 0) worker.put("name", display);

        database.collection("workers").document(user.getUid())
            .set(worker, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> mirrorWorkerMembership(user, worker, companyId, companyCode));
        mirrorWorkerMembership(user, worker, companyId, companyCode);
    }

'''
if marker not in j:
    raise SystemExit('showWorkerState marker not found')
j=j.replace(marker,helper+marker,1)

old='''                if (error != null) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        grantRole(active, "worker", currentMode);
                    } else {
                        showWorkerJoin();
                        workerJoinStatus.setText("કોડ તપાસવામાં ભૂલ. ફરી પ્રયાસ કરો.");
                    }
                    return;
                }'''
new='''                if (error != null) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        repairWorkerFromLocalMembership(active, currentCompanyId, currentCompanyName, currentCompanyCode, currentMode);
                        grantRole(active, "worker", currentMode);
                    } else {
                        showWorkerJoin();
                        workerJoinStatus.setText("કોડ તપાસવામાં ભૂલ. ફરી પ્રયાસ કરો.");
                    }
                    return;
                }'''
if old not in j: raise SystemExit('listener error fallback block not found')
j=j.replace(old,new,1)

old='''                if (snapshot == null || !snapshot.exists()) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        grantRole(active, "worker", currentMode);
                    } else showWorkerJoin();
                    return;
                }'''
new='''                if (snapshot == null || !snapshot.exists()) {
                    if (localJoined && localCompanyId != null && localCompanyId.length() > 0) {
                        currentCompanyId = localCompanyId;
                        currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                        currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                        if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                        repairWorkerFromLocalMembership(active, currentCompanyId, currentCompanyName, currentCompanyCode, currentMode);
                        grantRole(active, "worker", currentMode);
                    } else showWorkerJoin();
                    return;
                }'''
if old not in j: raise SystemExit('missing snapshot fallback block not found')
j=j.replace(old,new,1)

needle='''                String snapshotCompanyName = safe(snapshot.getString("companyName"));
                String snapshotCompanyCode = safe(snapshot.getString("companyCode"));
                String snapshotCompanyId = safe(snapshot.getString("companyId"));
                boolean removed = Boolean.TRUE.equals(snapshot.getBoolean("removed"));'''
rep='''                String snapshotCompanyName = safe(snapshot.getString("companyName"));
                String snapshotCompanyCode = safe(snapshot.getString("companyCode"));
                String snapshotCompanyId = safe(snapshot.getString("companyId"));
                boolean removed = Boolean.TRUE.equals(snapshot.getBoolean("removed"));
                boolean localMembershipWins = localJoined && localCompanyId != null && localCompanyId.length() > 0 &&
                    ((localCompanyCode != null && localCompanyCode.length() > 0 && !localCompanyCode.equalsIgnoreCase(snapshotCompanyCode)) ||
                     !localCompanyId.equals(snapshotCompanyId));'''
if needle not in j: raise SystemExit('snapshot membership anchor not found')
j=j.replace(needle,rep,1)

needle='''                if (removed) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode").putBoolean("worker_joined", false).apply();
                    signOut();
                    return;
                }
                if (snapshotCompanyId.length() == 0 || snapshotCompanyName.length() == 0) {'''
rep='''                if (removed) {
                    prefs.edit().remove("worker_company_id").remove("worker_company_name").remove("worker_company_code").remove("worker_mode").putBoolean("worker_joined", false).apply();
                    signOut();
                    return;
                }
                if (localMembershipWins) {
                    currentCompanyId = localCompanyId;
                    currentCompanyName = localCompanyName == null ? "" : localCompanyName;
                    currentCompanyCode = localCompanyCode == null ? "" : localCompanyCode;
                    if ("hour".equals(localMode) || "diamond".equals(localMode)) currentMode = localMode;
                    if (!("hour".equals(currentMode) || "diamond".equals(currentMode))) currentMode = "diamond";
                    repairWorkerFromLocalMembership(active, currentCompanyId, currentCompanyName, currentCompanyCode, currentMode);
                    grantRole(active, "worker", currentMode);
                    return;
                }
                if (snapshotCompanyId.length() == 0 || snapshotCompanyName.length() == 0) {'''
if needle not in j: raise SystemExit('removed/missing company anchor not found')
j=j.replace(needle,rep,1)

java.write_text(j)
b=root/'app/build.gradle'
t=b.read_text()
t=re.sub(r'versionCode\s+\d+','versionCode 66',t,count=1)
t=re.sub(r"versionName\s+'[^']+'","versionName '3.2.8'",t,count=1)
b.write_text(t)
print('v3.2.8 self-healing worker membership repair applied')
