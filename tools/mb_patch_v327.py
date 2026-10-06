from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

old=r'''    private void watchNotifications(String companyId) {
        clearNotificationListener();
        currentNotifications.clear();
        if (companyId == null || companyId.length() == 0) { updateBossLatestNotification(); pushNotifications(); return; }
        notificationListener = database.collection("notifications").whereEqualTo("companyId", companyId).limit(50)
            .addSnapshotListener((snap, error) -> {
                if (error != null || snap == null) return;
                currentNotifications.clear();
                for (QueryDocumentSnapshot d : snap) {
                    Map<String,Object> n = new HashMap<>(d.getData());
                    n.put("id", d.getId());
                    if (d.getTimestamp("createdAt") != null) n.put("createdAtMillis", d.getTimestamp("createdAt").toDate().getTime());
                    currentNotifications.add(n);
                }
                updateBossLatestNotification();
                pushNotifications();
            });
    }
'''
new=r'''    private long noticeMillis(Map<String,Object> item) {
        Object raw = item == null ? null : item.get("createdAtMillis");
        return raw instanceof Number ? ((Number) raw).longValue() : 0L;
    }

    private void mirrorCurrentBossNoticesToCompanyCode() {
        if (!"boss".equals(currentRole) || currentCompanyCode == null || currentCompanyCode.length() == 0) return;
        List<Map<String,Object>> ordered = new ArrayList<>();
        for (Map<String,Object> item : currentNotifications) ordered.add(new HashMap<>(item));
        ordered.sort((a,b) -> Long.compare(noticeMillis(a), noticeMillis(b)));
        int from = Math.max(0, ordered.size() - 20);
        List<Map<String,Object>> feed = new ArrayList<>();
        Map<String,Object> latest = null;
        for (int i=from; i<ordered.size(); i++) {
            Map<String,Object> src = ordered.get(i);
            Map<String,Object> out = new HashMap<>();
            out.put("id", String.valueOf(src.get("id") == null ? "" : src.get("id")));
            out.put("text", String.valueOf(src.get("text") == null ? "" : src.get("text")));
            out.put("createdAtMillis", noticeMillis(src));
            String image = String.valueOf(src.get("imageBase64") == null ? "" : src.get("imageBase64"));
            out.put("hasImage", image.length() > 0);
            feed.add(out);
            latest = new HashMap<>(out);
            if (image.length() > 0) latest.put("imageBase64", image);
        }
        Map<String,Object> shared = new HashMap<>();
        shared.put("noticeFeed", feed);
        if (latest != null) shared.put("latestNotice", latest);
        else shared.put("latestNotice", com.google.firebase.firestore.FieldValue.delete());
        shared.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        database.collection("companyCodes").document(currentCompanyCode)
            .set(shared, com.google.firebase.firestore.SetOptions.merge());
    }

    private void watchWorkerSharedNotifications(String companyCode) {
        notificationListener = database.collection("companyCodes").document(companyCode)
            .addSnapshotListener((doc, error) -> {
                if (error != null || doc == null || !doc.exists()) return;
                currentNotifications.clear();
                Map<String,Object> latest = null;
                Object latestRaw = doc.get("latestNotice");
                if (latestRaw instanceof Map) latest = new HashMap<>((Map<String,Object>) latestRaw);
                String latestId = latest == null ? "" : String.valueOf(latest.get("id") == null ? "" : latest.get("id"));
                Object raw = doc.get("noticeFeed");
                if (raw instanceof List) {
                    for (Object one : (List<?>) raw) {
                        if (!(one instanceof Map)) continue;
                        Map<String,Object> n = new HashMap<>((Map<String,Object>) one);
                        String id = String.valueOf(n.get("id") == null ? "" : n.get("id"));
                        if (latest != null && id.equals(latestId)) {
                            String image = String.valueOf(latest.get("imageBase64") == null ? "" : latest.get("imageBase64"));
                            if (image.length() > 0) n.put("imageBase64", image);
                        }
                        currentNotifications.add(n);
                    }
                }
                currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                pushNotifications();
            });
    }

    private void watchNotifications(String companyId) {
        clearNotificationListener();
        currentNotifications.clear();
        if ("worker".equals(currentRole) && currentCompanyCode != null && currentCompanyCode.length() > 0) {
            watchWorkerSharedNotifications(currentCompanyCode);
            return;
        }
        if (companyId == null || companyId.length() == 0) { updateBossLatestNotification(); pushNotifications(); return; }
        notificationListener = database.collection("notifications").whereEqualTo("companyId", companyId).limit(50)
            .addSnapshotListener((snap, error) -> {
                if (error != null || snap == null) return;
                currentNotifications.clear();
                for (QueryDocumentSnapshot d : snap) {
                    Map<String,Object> n = new HashMap<>(d.getData());
                    n.put("id", d.getId());
                    if (d.getTimestamp("createdAt") != null) n.put("createdAtMillis", d.getTimestamp("createdAt").toDate().getTime());
                    currentNotifications.add(n);
                }
                currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                updateBossLatestNotification();
                mirrorCurrentBossNoticesToCompanyCode();
                pushNotifications();
            });
    }
'''
if old not in j:
    raise SystemExit('watchNotifications block not found')
j=j.replace(old,new,1)

needle='''            Map<String, Object> codeData = new HashMap<>();
            codeData.put("companyId", user.getUid());
            codeData.put("companyName", name);'''
rep='''            Map<String, Object> codeData = new HashMap<>();
            codeData.put("companyId", user.getUid());
            codeData.put("bossUid", user.getUid());
            codeData.put("companyName", name);'''
if needle not in j:
    raise SystemExit('company code creation block not found')
j=j.replace(needle,rep,1)

java.write_text(j)
b=root/'app/build.gradle'
t=b.read_text()
t=re.sub(r'versionCode\s+\d+','versionCode 64',t,1)
t=re.sub(r"versionName\s+'[^']+'","versionName '3.2.6'",t,1)
b.write_text(t)
print('v3.2.6 shared boss-worker notification connectivity patch applied')
