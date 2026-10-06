from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 79","versionCode 80").replace("versionName '3.2.21'","versionName '3.2.22'")
gradle.write_text(s)

html=root/"app/src/main/assets/app.html"
s=html.read_text()

# Remove every custom point button. Decimal point must come only from the phone keyboard.
s=s.replace('<button id="hourValueDot" type="button" class="choice rate-dot-hour">. પોઇન્ટ</button>','')
s=s.replace('rate-dot-hour','')
html.write_text(s)

js=root/"app/src/main/assets/app.js"
s=js.read_text()
old="""  const hourValueDot=$('#hourValueDot'); if(hourValueDot) hourValueDot.addEventListener('click',()=>{
    const el=$('#hourValue'); if(!el)return; let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,''); if(!t)t='0'; if(!t.includes('.'))t+='.'; el.value=t; try{el.focus();const p=el.value.length;el.setSelectionRange(p,p)}catch(_){}; el.dispatchEvent(new Event('input',{bubbles:true}));
  });

"""
s=s.replace(old,'')
js.write_text(s)

java=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=java.read_text()

# Add worker-user notification listener.
s=s.replace(
"    private ListenerRegistration notificationDirectListener;\n",
"    private ListenerRegistration notificationDirectListener;\n    private ListenerRegistration notificationUserListener;\n"
)

# Boss worker list: only the canonical workers collection renders. Member mirrors may be stale/partial.
old_watch="""    private void watchPendingWorkers(String companyId) {
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
"""
new_watch="""    private void refreshBossWorkersCanonical(String companyId) {
        if (companyId == null || companyId.length() == 0) return;
        database.collection("workers").whereEqualTo("companyId", companyId).get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadBossWorkersFallback(companyId);
            })
            .addOnFailureListener(e -> loadBossWorkersFallback(companyId));
    }

    private void watchPendingWorkers(String companyId) {
        clearBossWorkersListener();

        bossWorkersListener = database.collection("workers")
            .whereEqualTo("companyId", companyId)
            .addSnapshotListener((snapshots, error) -> {
                if (error != null || snapshots == null) {
                    refreshBossWorkersCanonical(companyId);
                    return;
                }
                List<DocumentSnapshot> docs = new ArrayList<>(snapshots.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else refreshBossWorkersCanonical(companyId);
            });

        // These mirrors are only change triggers. Never render their partial snapshots directly,
        // otherwise an old one-member mirror can overwrite the full worker list.
        bossMembersListener = database.collection("companies").document(companyId).collection("members")
            .addSnapshotListener((snapshots, error) -> {
                if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
            });
        if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
            bossCodeMembersListener = database.collection("companyCodes").document(currentCompanyCode).collection("members")
                .addSnapshotListener((snapshots, error) -> {
                    if (error == null && snapshots != null) refreshBossWorkersCanonical(companyId);
                });
        }

        refreshBossWorkersCanonical(companyId);
    }
"""
if old_watch not in s:
    raise SystemExit("boss worker watch block not found")
s=s.replace(old_watch,new_watch)

# Login should never sit forever on "processing": remove the unnecessary pre-read and route with a bounded fallback.
old_apply="""    private void applyPendingRoleAfterLogin() {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null) {
            showAuthState();
            return;
        }
        String selectedRole = pendingLoginRole;
        String selectedMode = pendingLoginMode;
        pendingLoginRole = null;
        pendingLoginMode = null;
        if (!("boss".equals(selectedRole) || "worker".equals(selectedRole))) {
            showAuthState();
            return;
        }
        database.collection("users").document(user.getUid()).get()
            .addOnSuccessListener(snapshot -> {
                saveRole(selectedRole, selectedMode);
            })
            .addOnFailureListener(e -> saveRole(selectedRole, selectedMode));
    }
"""
new_apply="""    private void applyPendingRoleAfterLogin() {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null) {
            showAuthState();
            return;
        }
        String selectedRole = pendingLoginRole;
        String selectedMode = pendingLoginMode;
        pendingLoginRole = null;
        pendingLoginMode = null;
        if (!("boss".equals(selectedRole) || "worker".equals(selectedRole))) {
            showAuthState();
            return;
        }
        saveRole(selectedRole, selectedMode);
    }
"""
if old_apply not in s:
    raise SystemExit("applyPendingRoleAfterLogin block not found")
s=s.replace(old_apply,new_apply)

old_save_role="""    private void saveRole(String role, String mode) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !("boss".equals(role) || "worker".equals(role))) return;
        String cleanMode = "boss".equals(role) ? "both" : (("hour".equals(mode) || "diamond".equals(mode)) ? mode : "both");
        Map<String,Object> data = new HashMap<>();
        data.put("role", role);
        data.put("mode", cleanMode);
        data.put("email", safe(user.getEmail()));
        data.put("googleName", safe(user.getDisplayName()));
        database.collection("users").document(user.getUid()).set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> routeSignedInUser(user));
    }
"""
new_save_role="""    private void continueAfterRoleSelection(FirebaseUser user, String role, String cleanMode) {
        FirebaseUser active = auth.getCurrentUser();
        if (active == null || user == null || !user.getUid().equals(active.getUid())) return;

        if ("boss".equals(role)) {
            currentRole = "boss";
            currentMode = "both";
            clearWorkerListener();
            showBossCompany(user);
            return;
        }

        currentRole = "worker";
        currentMode = cleanMode;
        clearBossWorkersListener();
        database.collection("users").document(user.getUid()).get()
            .addOnSuccessListener(snapshot -> {
                FirebaseUser stillActive = auth.getCurrentUser();
                if (stillActive == null || !user.getUid().equals(stillActive.getUid())) return;
                String first = safe(snapshot.getString("firstName"));
                String phone = safe(snapshot.getString("phone"));
                String birthday = safe(snapshot.getString("birthday"));
                if (first.length() == 0 || phone.length() == 0 || birthday.length() == 0) showWorkerProfile(user, snapshot);
                else showWorkerState(user);
            })
            .addOnFailureListener(e -> {
                hideAll();
                Object tag = workerProfile.getTag();
                if (tag instanceof ScrollView) ((ScrollView) tag).setVisibility(View.VISIBLE);
                profileFirstName.setText(safe(user.getDisplayName()));
                profileLastName.setText("");
                profilePhone.setText("");
                profileBirthday.setText("");
                workerProfileSave.setEnabled(true);
            });
    }

    private void saveRole(String role, String mode) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !("boss".equals(role) || "worker".equals(role))) return;
        String cleanMode = "boss".equals(role) ? "both" : (("hour".equals(mode) || "diamond".equals(mode)) ? mode : "diamond");
        Map<String,Object> data = new HashMap<>();
        data.put("role", role);
        data.put("mode", cleanMode);
        data.put("email", safe(user.getEmail()));
        data.put("googleName", safe(user.getDisplayName()));

        final java.util.concurrent.atomic.AtomicBoolean routed = new java.util.concurrent.atomic.AtomicBoolean(false);
        Runnable continueUi = () -> {
            if (routed.compareAndSet(false, true)) {
                signingIn = false;
                setLoginButtonsEnabled(true);
                if (loginStatus != null) loginStatus.setText("");
                continueAfterRoleSelection(user, role, cleanMode);
            }
        };

        database.collection("users").document(user.getUid())
            .set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnCompleteListener(task -> {
                if (!task.isSuccessful() && loginStatus != null) loginStatus.setText("માહિતી સેવ થવામાં મોડું છે; એપ ચાલુ રાખી છે…");
                continueUi.run();
            });

        if (login != null) login.postDelayed(continueUi, 2500);
    }
"""
if old_save_role not in s:
    raise SystemExit("saveRole block not found")
s=s.replace(old_save_role,new_save_role)

# Worker profile save gets a UI watchdog so successful auth doesn't require closing/reopening the app.
old_profile_tail="""        workerProfileSave.setEnabled(false);
        database.collection("users").document(user.getUid()).set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener(v -> { workerProfileSave.setEnabled(true); showWorkerState(user); })
            .addOnFailureListener(e -> { workerProfileSave.setEnabled(true); profileFirstName.setError("માહિતી સેવ થઈ નથી"); });
    }
"""
new_profile_tail="""        workerProfileSave.setEnabled(false);
        final java.util.concurrent.atomic.AtomicBoolean finished = new java.util.concurrent.atomic.AtomicBoolean(false);
        Runnable continueUi = () -> {
            if (finished.compareAndSet(false, true)) {
                workerProfileSave.setEnabled(true);
                showWorkerState(user);
            }
        };
        database.collection("users").document(user.getUid()).set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnCompleteListener(task -> {
                if (task.isSuccessful()) continueUi.run();
                else if (finished.compareAndSet(false, true)) {
                    workerProfileSave.setEnabled(true);
                    profileFirstName.setError("માહિતી સેવ થઈ નથી. ફરી પ્રયાસ કરો.");
                }
            });
        workerProfile.postDelayed(continueUi, 3000);
    }
"""
if old_profile_tail not in s:
    raise SystemExit("worker profile save block not found")
s=s.replace(old_profile_tail,new_profile_tail)

# Worker notification watchers must preserve worker-document notifications instead of clearing them on resume.
old_watch_notices="""    private void watchNotifications(String companyId) {
        clearNotificationListener();
        currentNotifications.clear();
        mergeCachedPushNotifications();
        if ("worker".equals(currentRole)) {
            watchWorkerNoticeSubcollections(currentCompanyCode, currentCompanyId);
            return;
        }
        if (companyId == null || companyId.length() == 0) { updateBossLatestNotification(); pushNotifications(); return; }
"""
new_watch_notices="""    private void watchNotifications(String companyId) {
        clearNotificationListener();
        if ("worker".equals(currentRole)) {
            // Do not clear here: latestNotice may have just arrived through workers/{uid}.
            mergeCachedPushNotifications();
            watchWorkerNoticeSubcollections(currentCompanyCode, currentCompanyId);
            FirebaseUser active = auth == null ? null : auth.getCurrentUser();
            if (active != null) {
                notificationUserListener = database.collection("users").document(active.getUid())
                    .addSnapshotListener((doc,error) -> {
                        if (error == null && doc != null && doc.exists()) consumeWorkerLatestNotice(doc);
                    });
            }
            pushNotifications();
            return;
        }
        currentNotifications.clear();
        mergeCachedPushNotifications();
        if (companyId == null || companyId.length() == 0) { updateBossLatestNotification(); pushNotifications(); return; }
"""
if old_watch_notices not in s:
    raise SystemExit("watchNotifications block not found")
s=s.replace(old_watch_notices,new_watch_notices)

# Clear the extra worker user listener.
s=s.replace(
"        if (notificationDirectListener != null) notificationDirectListener.remove(); notificationDirectListener = null;\n",
"        if (notificationDirectListener != null) notificationDirectListener.remove(); notificationDirectListener = null;\n        if (notificationUserListener != null) notificationUserListener.remove(); notificationUserListener = null;\n"
)

# Notification delivery: mirror to both workers/{uid} and users/{uid}; also membership mirrors.
old_worker_loop="""                            for (DocumentSnapshot workerDoc : workersSnap.getDocuments()) {
                                if (Boolean.TRUE.equals(workerDoc.getBoolean("removed"))) continue;
                                Map<String,Object> inbox = new HashMap<>();
                                inbox.put("latestNotice", workerLatest);
                                inbox.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                                database.collection("workers").document(workerDoc.getId())
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                            }
"""
new_worker_loop="""                            for (DocumentSnapshot workerDoc : workersSnap.getDocuments()) {
                                if (Boolean.TRUE.equals(workerDoc.getBoolean("removed"))) continue;
                                String workerUid = workerDoc.getId();
                                Map<String,Object> inbox = new HashMap<>();
                                inbox.put("latestNotice", workerLatest);
                                inbox.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

                                database.collection("workers").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                database.collection("users").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                database.collection("companies").document(currentCompanyId).collection("members").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
                                    database.collection("companyCodes").document(currentCompanyCode).collection("members").document(workerUid)
                                        .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                }
                            }
"""
if old_worker_loop not in s:
    raise SystemExit("notification worker mirror loop not found")
s=s.replace(old_worker_loop,new_worker_loop)

# Users collection fallback catches memberships mirrored there even if a legacy workers document is missing.
insert_after="""                    database.collection("workers").whereEqualTo("companyId", currentCompanyId).get()
                        .addOnSuccessListener(workersSnap -> {
                            if (workersSnap == null) return;
                            for (DocumentSnapshot workerDoc : workersSnap.getDocuments()) {
                                if (Boolean.TRUE.equals(workerDoc.getBoolean("removed"))) continue;
                                String workerUid = workerDoc.getId();
                                Map<String,Object> inbox = new HashMap<>();
                                inbox.put("latestNotice", workerLatest);
                                inbox.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

                                database.collection("workers").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                database.collection("users").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                database.collection("companies").document(currentCompanyId).collection("members").document(workerUid)
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
                                    database.collection("companyCodes").document(currentCompanyCode).collection("members").document(workerUid)
                                        .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                                }
                            }
                        });
"""
if insert_after not in s:
    raise SystemExit("notification delivery insertion point not found")
extra=insert_after+"""                    database.collection("users").whereEqualTo("companyId", currentCompanyId).get()
                        .addOnSuccessListener(usersSnap -> {
                            if (usersSnap == null) return;
                            for (DocumentSnapshot userDoc : usersSnap.getDocuments()) {
                                if (!"worker".equals(safe(userDoc.getString("role")))) continue;
                                if (Boolean.TRUE.equals(userDoc.getBoolean("removed"))) continue;
                                Map<String,Object> inbox = new HashMap<>();
                                inbox.put("latestNotice", workerLatest);
                                inbox.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                                database.collection("users").document(userDoc.getId())
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                            }
                        });
"""
s=s.replace(insert_after,extra)

java.write_text(s)
print("v3.2.22 complete regression fixes applied")
