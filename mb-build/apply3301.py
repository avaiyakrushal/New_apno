from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 100","versionCode 101").replace("versionName '3.3.0'","versionName '3.3.1'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

# Add a compact Firebase error formatter for visible diagnostics instead of silently continuing.
anchor='''    private static String safe(String s) { return s == null ? "" : s; }
'''
helper='''    private static String safe(String s) { return s == null ? "" : s; }

    private String firebaseError(Throwable e) {
        if (e == null) return "અજ્ઞાત Firebase error";
        String msg = e.getMessage() == null ? "" : e.getMessage();
        if (e instanceof com.google.firebase.firestore.FirebaseFirestoreException) {
            com.google.firebase.firestore.FirebaseFirestoreException fe =
                (com.google.firebase.firestore.FirebaseFirestoreException) e;
            return fe.getCode().name() + (msg.length() > 0 ? " · " + msg : "");
        }
        return e.getClass().getSimpleName() + (msg.length() > 0 ? " · " + msg : "");
    }
'''
if anchor not in s: raise SystemExit("safe() anchor missing")
s=s.replace(anchor,helper,1)

# Role save must actually reach Firestore before routing. v3.3.0 deliberately continued even on failure.
old='''        database.collection("users").document(user.getUid())
            .set(data, com.google.firebase.firestore.SetOptions.merge())
            .addOnCompleteListener(task -> {
                if (!task.isSuccessful() && loginStatus != null) loginStatus.setText("માહિતી સેવ થવામાં મોડું છે; એપ ચાલુ રાખી છે…");
                continueUi.run();
            });
'''
new='''        data.put("uid", user.getUid());
        data.put("authUid", user.getUid());
        data.put("schemaVersion", "3.3");
        data.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

        database.enableNetwork().addOnCompleteListener(networkTask ->
            database.collection("users").document(user.getUid())
                .set(data, com.google.firebase.firestore.SetOptions.merge())
                .addOnSuccessListener(v -> continueUi.run())
                .addOnFailureListener(e -> {
                    signingIn = false;
                    setLoginButtonsEnabled(true);
                    String message = "Firebaseમાં role સેવ થયું નથી: " + firebaseError(e);
                    if (loginStatus != null) loginStatus.setText(message);
                    android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                    showRoleChoice();
                })
        );
'''
if old not in s: raise SystemExit("saveRole write block missing")
s=s.replace(old,new,1)

# Replace company create flow with server-first and server-verified write.
start=s.find("    private void createCompany() {")
end=s.find("    private void shareCompany() {", start)
if start < 0 or end < 0: raise SystemExit("company flow boundaries missing")
new_block=r'''    private void createCompany() {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !"boss".equals(currentRole)) return;
        String name = bossCompanyInput.getText().toString().trim();
        if (name.length() < 2) {
            bossCompanyInput.setError("કંપનીનું નામ લખો");
            return;
        }
        if (name.length() > 80) name = name.substring(0, 80);
        createCompanyButton.setEnabled(false);
        final String finalName = name;

        database.enableNetwork().addOnCompleteListener(networkTask ->
            database.collection("companies").document(user.getUid())
                .get(com.google.firebase.firestore.Source.SERVER)
                .addOnSuccessListener(existing -> {
                    if (existing != null && existing.exists()) {
                        currentCompanyName = safe(existing.getString("name"));
                        currentCompanyCode = safe(existing.getString("code"));
                        createCompanyButton.setEnabled(true);
                        showBossCompanyInfo(user);
                        android.widget.Toast.makeText(this, "આ accountની કંપની પહેલેથી Firebaseમાં છે.", android.widget.Toast.LENGTH_SHORT).show();
                    } else {
                        createCompanyWithFreshCode(user, finalName, 0);
                    }
                })
                .addOnFailureListener(e -> {
                    createCompanyButton.setEnabled(true);
                    String message = "Firebase server ચેક થઈ શક્યો નથી: " + firebaseError(e);
                    bossCompanyInput.setError(message);
                    android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                })
        );
    }

    private void createCompanyWithFreshCode(FirebaseUser user, String name, int attempt) {
        if (attempt >= 6) {
            createCompanyButton.setEnabled(true);
            bossCompanyInput.setError("નવો company code બનાવી શકાયો નથી. ફરી પ્રયાસ કરો.");
            return;
        }

        String alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        StringBuilder codeBuilder = new StringBuilder(6);
        for (int i = 0; i < 6; i++) codeBuilder.append(alphabet.charAt(RANDOM.nextInt(alphabet.length())));
        String code = codeBuilder.toString();
        DocumentReference companyRef = database.collection("companies").document(user.getUid());
        DocumentReference codeRef = database.collection("companyCodes").document(code);
        DocumentReference userRef = database.collection("users").document(user.getUid());

        codeRef.get(com.google.firebase.firestore.Source.SERVER).addOnSuccessListener(codeSnapshot -> {
            if (codeSnapshot.exists()) {
                createCompanyWithFreshCode(user, name, attempt + 1);
                return;
            }

            Map<String,Object> company = new HashMap<>();
            company.put("name", name);
            company.put("companyName", name);
            company.put("code", code);
            company.put("companyCode", code);
            company.put("companyId", user.getUid());
            company.put("bossUid", user.getUid());
            company.put("ownerUid", user.getUid());
            company.put("schemaVersion", "3.3");
            company.put("active", true);
            company.put("createdAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
            company.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

            Map<String,Object> codeData = new HashMap<>();
            codeData.put("companyId", user.getUid());
            codeData.put("bossUid", user.getUid());
            codeData.put("ownerUid", user.getUid());
            codeData.put("companyName", name);
            codeData.put("name", name);
            codeData.put("code", code);
            codeData.put("schemaVersion", "3.3");
            codeData.put("active", true);
            codeData.put("createdAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
            codeData.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

            Map<String,Object> bossUser = new HashMap<>();
            bossUser.put("uid", user.getUid());
            bossUser.put("authUid", user.getUid());
            bossUser.put("role", "boss");
            bossUser.put("mode", "both");
            bossUser.put("companyId", user.getUid());
            bossUser.put("bossUid", user.getUid());
            bossUser.put("companyName", name);
            bossUser.put("companyCode", code);
            bossUser.put("schemaVersion", "3.3");
            bossUser.put("email", safe(user.getEmail()));
            bossUser.put("googleName", safe(user.getDisplayName()));
            bossUser.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());

            com.google.firebase.firestore.WriteBatch batch = database.batch();
            batch.set(companyRef, company, com.google.firebase.firestore.SetOptions.merge());
            batch.set(codeRef, codeData, com.google.firebase.firestore.SetOptions.merge());
            batch.set(userRef, bossUser, com.google.firebase.firestore.SetOptions.merge());

            batch.commit()
                .addOnSuccessListener(v -> verifyCompanyOnServer(user, name, code, companyRef, codeRef))
                .addOnFailureListener(e -> {
                    createCompanyButton.setEnabled(true);
                    String message = "કંપની Firebaseમાં સેવ થઈ નથી: " + firebaseError(e);
                    bossCompanyInput.setError(message);
                    android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                });
        }).addOnFailureListener(e -> {
            createCompanyButton.setEnabled(true);
            String message = "Company code server પર ચેક થઈ શક્યો નથી: " + firebaseError(e);
            bossCompanyInput.setError(message);
            android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
        });
    }

    private void verifyCompanyOnServer(
        FirebaseUser user,
        String name,
        String code,
        DocumentReference companyRef,
        DocumentReference codeRef
    ) {
        companyRef.get(com.google.firebase.firestore.Source.SERVER).addOnSuccessListener(companySnap -> {
            if (companySnap == null || !companySnap.exists()) {
                createCompanyButton.setEnabled(true);
                String message = "Company write પછી Firebase serverમાં company document મળ્યો નથી.";
                bossCompanyInput.setError(message);
                android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                return;
            }

            codeRef.get(com.google.firebase.firestore.Source.SERVER).addOnSuccessListener(codeSnap -> {
                createCompanyButton.setEnabled(true);
                if (codeSnap == null || !codeSnap.exists()) {
                    String message = "Company બની છે, પણ company code serverમાં સેવ થયો નથી.";
                    bossCompanyInput.setError(message);
                    android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                    return;
                }

                String savedBoss = safe(codeSnap.getString("bossUid"));
                String savedCompany = safe(codeSnap.getString("companyId"));
                if (!user.getUid().equals(savedBoss) || !user.getUid().equals(savedCompany)) {
                    String message = "Company code mapping mismatch મળી. ફરી બનાવશો નહીં.";
                    bossCompanyInput.setError(message);
                    android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
                    return;
                }

                currentCompanyId = user.getUid();
                currentCompanyName = safe(companySnap.getString("name"));
                if (currentCompanyName.length() == 0) currentCompanyName = name;
                currentCompanyCode = safe(companySnap.getString("code"));
                if (currentCompanyCode.length() == 0) currentCompanyCode = code;
                showBossCompanyInfo(user);
                android.widget.Toast.makeText(this, "કંપની Firebase serverમાં ચકાસીને સેવ થઈ ગઈ.", android.widget.Toast.LENGTH_SHORT).show();
            }).addOnFailureListener(e -> {
                createCompanyButton.setEnabled(true);
                String message = "Company code verify ન થયું: " + firebaseError(e);
                bossCompanyInput.setError(message);
                android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
            });
        }).addOnFailureListener(e -> {
            createCompanyButton.setEnabled(true);
            String message = "Company server verify ન થઈ: " + firebaseError(e);
            bossCompanyInput.setError(message);
            android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show();
        });
    }

'''
s=s[:start]+new_block+s[end:]

p.write_text(s)
print("v3.3.1 server-verified role/company writes applied")
