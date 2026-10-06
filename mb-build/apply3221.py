from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 78","versionCode 79").replace("versionName '3.2.20'","versionName '3.2.21'")
gradle.write_text(s)

html=root/"app/src/main/assets/app.html"
s=html.read_text()

# Keep rate setting clean: no custom side point button; decimals come from the phone keyboard.
s=s.replace('<p class="hint">પૈસા/પોઇન્ટ માટે દશાંશ લખી શકો: 30.15 અથવા 30,15</p>',
            '<p class="hint">દશાંશ ભાવ માટે મોબાઇલ કીબોર્ડનો . ઉપયોગ કરો, જેમ કે 30.15</p>')
s=s.replace('<p class="hint">દશાંશ દર પણ ચાલશે, જેમ કે 101.15. કલાક/ઓફિસ કામ પસંદ કરેલા કારીગર માટે આ દર સેવ થશે.</p>',
            '<p class="hint">દશાંશ દર માટે મોબાઇલ કીબોર્ડનો . ઉપયોગ કરો, જેમ કે 101.15. કલાક/ઓફિસ કામ પસંદ કરેલા કારીગર માટે આ દર સેવ થશે.</p>')
# Remove unused styles for old custom point controls in rate settings.
s=s.replace('.rate-dot-hour{margin:8px 0 4px;padding:8px 14px;font-size:15px}.rate-grid-simple{grid-template-columns:60px minmax(0,1fr)!important}',
            '.rate-grid-simple{grid-template-columns:60px minmax(0,1fr)!important}')
html.write_text(s)

java=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=java.read_text()

# Add helper that keeps each worker's own document as a reliable in-app notification inbox.
anchor='''    private void registerPushToken(FirebaseUser user) {
        if (user == null) return;
'''
helper='''    private void registerWorkerPushToken(FirebaseUser user) {
        if (user == null) return;
        FirebaseMessaging.getInstance().getToken().addOnSuccessListener(token -> {
            if (token == null || token.trim().length() == 0) return;
            Map<String,Object> update = new HashMap<>();
            update.put("fcmToken", token);
            update.put("fcmUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
            database.collection("workers").document(user.getUid()).get().addOnSuccessListener(doc -> {
                if (doc != null && doc.exists()) {
                    database.collection("workers").document(user.getUid())
                        .set(update, com.google.firebase.firestore.SetOptions.merge());
                }
            });
        });
    }

'''
if helper.strip() not in s:
    s=s.replace(anchor,helper+anchor)

# When worker role is granted, mirror token to workers/{uid}; older push backends often read token there.
s=s.replace(
'''        currentRole = role;
        currentMode = mode;
        if ("boss".equals(role)) currentCompanyId = user.getUid();
        startCloudSync(user);
''',
'''        currentRole = role;
        currentMode = mode;
        if ("boss".equals(role)) currentCompanyId = user.getUid();
        if ("worker".equals(role)) registerWorkerPushToken(user);
        startCloudSync(user);
''')

# Consume a mirrored latestNotice directly from workers/{uid}, which is already the worker's live membership listener.
insert_before='''    private void showWorkerState(FirebaseUser user) {
'''
consumer='''    @SuppressWarnings("unchecked")
    private void consumeWorkerLatestNotice(DocumentSnapshot snapshot) {
        if (snapshot == null || !snapshot.exists()) return;
        Object raw = snapshot.get("latestNotice");
        if (!(raw instanceof Map)) return;
        Map<String,Object> notice = new HashMap<>((Map<String,Object>) raw);
        String id = String.valueOf(notice.get("id") == null ? "" : notice.get("id"));
        if (id.length() == 0) return;
        upsertSharedNotification(notice);
        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
        pushNotifications();

        try {
            android.content.SharedPreferences prefs = getSharedPreferences("mb_worker_notice_state", MODE_PRIVATE);
            String lastId = prefs.getString("last_system_notice_id", "");
            if (!id.equals(lastId)) {
                String title = currentCompanyName == null || currentCompanyName.trim().isEmpty() ? "MB ડાયમંડ ડાયરી" : currentCompanyName;
                String body = String.valueOf(notice.get("text") == null ? "નવી સૂચના આવી છે" : notice.get("text"));
                android.app.NotificationManager manager = (android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);
                String channelId = "mbdd_company_notices";
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                    android.app.NotificationChannel channel = new android.app.NotificationChannel(channelId, "કંપની સૂચનાઓ", android.app.NotificationManager.IMPORTANCE_HIGH);
                    channel.setDescription("શેઠ તરફથી આવતી MB Diamond Diary સૂચનાઓ");
                    manager.createNotificationChannel(channel);
                }
                android.content.Intent open = new android.content.Intent(this, MainActivity.class);
                open.addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP | android.content.Intent.FLAG_ACTIVITY_SINGLE_TOP);
                open.putExtra("open_notifications", true);
                android.app.PendingIntent pending = android.app.PendingIntent.getActivity(this, 321, open,
                    android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_IMMUTABLE);
                android.app.Notification.Builder builder = android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O
                    ? new android.app.Notification.Builder(this, channelId)
                    : new android.app.Notification.Builder(this);
                builder.setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(title)
                    .setContentText(body)
                    .setStyle(new android.app.Notification.BigTextStyle().bigText(body))
                    .setAutoCancel(true)
                    .setContentIntent(pending)
                    .setPriority(android.app.Notification.PRIORITY_HIGH);
                manager.notify((int)(System.currentTimeMillis() & 0x7fffffff), builder.build());
                prefs.edit().putString("last_system_notice_id", id).apply();
            }
        } catch (Exception ignored) {}
    }

'''
if consumer.strip() not in s:
    s=s.replace(insert_before,consumer+insert_before)

# Feed latestNotice before any membership routing returns.
needle='''                if (snapshot == null || !snapshot.exists()) {
'''
if 'consumeWorkerLatestNotice(snapshot);' not in s:
    s=s.replace(needle,'''                if (snapshot != null && snapshot.exists()) consumeWorkerLatestNotice(snapshot);
                if (snapshot == null || !snapshot.exists()) {
''',1)

# Add companyCode + createdAtMillis to root notification too, so both old/new backend triggers can resolve company.
s=s.replace(
'''        n.put("companyId", currentCompanyId);
        n.put("companyName", currentCompanyName == null ? "" : currentCompanyName);
        n.put("senderUid", user.getUid());
        n.put("text", clean);
        n.put("imageBase64", image);
        n.put("createdAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
''',
'''        long rootNow = System.currentTimeMillis();
        n.put("companyId", currentCompanyId);
        n.put("companyCode", currentCompanyCode == null ? "" : currentCompanyCode);
        n.put("companyName", currentCompanyName == null ? "" : currentCompanyName);
        n.put("senderUid", user.getUid());
        n.put("text", clean);
        n.put("imageBase64", image);
        n.put("createdAtMillis", rootNow);
        n.put("createdAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
''')

# Mirror each sent notice directly to active workers' own documents.
marker='''                if (currentCompanyId != null && currentCompanyId.length() > 0) {
                    database.collection("companies").document(currentCompanyId).collection("notices").document(ref.getId())
                        .set(shared, com.google.firebase.firestore.SetOptions.merge());
                    Map<String,Object> latest = new HashMap<>(shared); latest.remove("createdAt");
                    database.collection("companies").document(currentCompanyId)
                        .set(java.util.Collections.singletonMap("latestNotice", latest), com.google.firebase.firestore.SetOptions.merge());
                }
                lastChosenFileUri = null;
'''
replacement='''                if (currentCompanyId != null && currentCompanyId.length() > 0) {
                    database.collection("companies").document(currentCompanyId).collection("notices").document(ref.getId())
                        .set(shared, com.google.firebase.firestore.SetOptions.merge());
                    Map<String,Object> latest = new HashMap<>(shared); latest.remove("createdAt");
                    database.collection("companies").document(currentCompanyId)
                        .set(java.util.Collections.singletonMap("latestNotice", latest), com.google.firebase.firestore.SetOptions.merge());

                    final Map<String,Object> workerLatest = new HashMap<>(latest);
                    String workerImage = String.valueOf(workerLatest.get("imageBase64") == null ? "" : workerLatest.get("imageBase64"));
                    if (workerImage.length() > 350000) {
                        workerLatest.remove("imageBase64");
                        workerLatest.put("hasImage", true);
                    }
                    database.collection("workers").whereEqualTo("companyId", currentCompanyId).get()
                        .addOnSuccessListener(workersSnap -> {
                            if (workersSnap == null) return;
                            for (DocumentSnapshot workerDoc : workersSnap.getDocuments()) {
                                if (Boolean.TRUE.equals(workerDoc.getBoolean("removed"))) continue;
                                Map<String,Object> inbox = new HashMap<>();
                                inbox.put("latestNotice", workerLatest);
                                inbox.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                                database.collection("workers").document(workerDoc.getId())
                                    .set(inbox, com.google.firebase.firestore.SetOptions.merge());
                            }
                        });
                }
                lastChosenFileUri = null;
'''
if marker not in s:
    raise SystemExit("send notification mirror insertion point not found")
s=s.replace(marker,replacement)

java.write_text(s)

# Keep FCM token mirrored into an existing worker document when Android rotates the token.
svc=root/"app/src/main/java/com/example/diamonddiary/DiaryMessagingService.java"
s=svc.read_text()
old='''        FirebaseFirestore.getInstance().collection("users").document(user.getUid())
            .set(update, com.google.firebase.firestore.SetOptions.merge());
'''
new='''        FirebaseFirestore db = FirebaseFirestore.getInstance();
        db.collection("users").document(user.getUid())
            .set(update, com.google.firebase.firestore.SetOptions.merge());
        db.collection("workers").document(user.getUid()).get().addOnSuccessListener(doc -> {
            if (doc != null && doc.exists()) {
                db.collection("workers").document(user.getUid())
                    .set(update, com.google.firebase.firestore.SetOptions.merge());
            }
        });
'''
if old not in s:
    raise SystemExit("FCM token update block not found")
s=s.replace(old,new)
svc.write_text(s)

print("v3.2.21 notification delivery and rate-setting cleanup applied")
