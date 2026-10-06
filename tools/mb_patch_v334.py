from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

# Keep worker contact details (mobile + birthday) mirrored into the worker/company records.
# This fixes Sheth cards showing "—" after membership self-heal.
old=r'''    private void repairWorkerFromLocalMembership(FirebaseUser user, String companyId, String companyName, String companyCode, String mode) {
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
new=r'''    private void writeWorkerMembershipWithProfile(FirebaseUser user, Map<String,Object> worker, String companyId, String companyCode) {
        if (user == null || worker == null) return;
        database.collection("workers").document(user.getUid())
            .set(worker, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> mirrorWorkerMembership(user, worker, companyId, companyCode));
        mirrorWorkerMembership(user, worker, companyId, companyCode);
    }

    private void repairWorkerFromLocalMembership(FirebaseUser user, String companyId, String companyName, String companyCode, String mode) {
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

        database.collection("users").document(user.getUid()).get()
            .addOnSuccessListener(profile -> {
                String first = safe(profile.getString("firstName"));
                String last = safe(profile.getString("lastName"));
                String name = safe(profile.getString("name"));
                if (name.length() == 0) name = (first + " " + last).trim();
                if (name.length() == 0) name = safe(user.getDisplayName());
                if (name.length() > 0) worker.put("name", name);
                worker.put("firstName", first);
                worker.put("lastName", last);
                worker.put("phone", safe(profile.getString("phone")));
                worker.put("birthday", safe(profile.getString("birthday")));
                writeWorkerMembershipWithProfile(user, worker, companyId, companyCode);
            })
            .addOnFailureListener(e -> {
                String display = safe(user.getDisplayName());
                if (display.length() > 0) worker.put("name", display);
                writeWorkerMembershipWithProfile(user, worker, companyId, companyCode);
            });
    }
'''
if old not in j: raise SystemExit('repairWorkerFromLocalMembership block not found')
j=j.replace(old,new,1)

# Existing worker document can also be missing contact details; repair them from users/{uid}.
needle='''                currentMode = mode;
                prefs.edit().putString("worker_company_id", currentCompanyId).putString("worker_company_name", currentCompanyName)
                    .putString("worker_company_code", currentCompanyCode).putString("worker_mode", mode).putBoolean("worker_joined", true).apply();
                Map<String,Object> repair = new HashMap<>();'''
rep='''                currentMode = mode;
                prefs.edit().putString("worker_company_id", currentCompanyId).putString("worker_company_name", currentCompanyName)
                    .putString("worker_company_code", currentCompanyCode).putString("worker_mode", mode).putBoolean("worker_joined", true).apply();
                String existingPhone = safe(snapshot.getString("phone"));
                String existingBirthday = safe(snapshot.getString("birthday"));
                if (existingPhone.length() == 0 || existingBirthday.length() == 0) {
                    database.collection("users").document(active.getUid()).get().addOnSuccessListener(profile -> {
                        Map<String,Object> contactFix = new HashMap<>();
                        String first = safe(profile.getString("firstName"));
                        String last = safe(profile.getString("lastName"));
                        String name = safe(profile.getString("name"));
                        if (name.length() == 0) name = (first + " " + last).trim();
                        if (name.length() > 0) contactFix.put("name", name);
                        contactFix.put("firstName", first);
                        contactFix.put("lastName", last);
                        contactFix.put("phone", safe(profile.getString("phone")));
                        contactFix.put("birthday", safe(profile.getString("birthday")));
                        contactFix.put("companyId", currentCompanyId);
                        contactFix.put("bossUid", currentCompanyId);
                        contactFix.put("companyName", currentCompanyName);
                        contactFix.put("companyCode", currentCompanyCode);
                        contactFix.put("mode", currentMode);
                        contactFix.put("active", true);
                        contactFix.put("removed", false);
                        database.collection("workers").document(active.getUid()).set(contactFix, com.google.firebase.firestore.SetOptions.merge());
                        mirrorWorkerMembership(active, contactFix, currentCompanyId, currentCompanyCode);
                    });
                }
                Map<String,Object> repair = new HashMap<>();'''
if needle not in j: raise SystemExit('existing contact repair anchor not found')
j=j.replace(needle,rep,1)

# Saving/editing profile while already joined must update Sheth-visible worker/membership records too.
old=r'''        database.collection("users").document(user.getUid()).set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> { workerProfileSave.setEnabled(true); showWorkerState(user); })
            .addOnFailureListener(e -> { workerProfileSave.setEnabled(true); profileFirstName.setError("માહિતી સેવ થઈ નથી"); });'''
new=r'''        database.collection("users").document(user.getUid()).set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> {
                workerProfileSave.setEnabled(true);
                android.content.SharedPreferences prefs = getPreferences(MODE_PRIVATE);
                String cid = prefs.getString("worker_company_id", "");
                String cname = prefs.getString("worker_company_name", "");
                String ccode = prefs.getString("worker_company_code", "");
                String cmode = prefs.getString("worker_mode", currentMode == null ? "" : currentMode);
                if (prefs.getBoolean("worker_joined", false) && cid != null && cid.length() > 0) {
                    Map<String,Object> workerProfile = new HashMap<>(data);
                    workerProfile.put("companyId", cid);
                    workerProfile.put("bossUid", cid);
                    workerProfile.put("companyName", cname == null ? "" : cname);
                    workerProfile.put("companyCode", ccode == null ? "" : ccode);
                    workerProfile.put("mode", ("hour".equals(cmode) || "diamond".equals(cmode)) ? cmode : "diamond");
                    workerProfile.put("active", true);
                    workerProfile.put("removed", false);
                    writeWorkerMembershipWithProfile(user, workerProfile, cid, ccode);
                }
                showWorkerState(user);
            })
            .addOnFailureListener(e -> { workerProfileSave.setEnabled(true); profileFirstName.setError("માહિતી સેવ થઈ નથી"); });'''
if old not in j: raise SystemExit('saveWorkerProfile success block not found')
j=j.replace(old,new,1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 70', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.12'", b, count=1)
build.write_text(b)
print('v3.2.12 worker mobile/birthday profile sync applied')
