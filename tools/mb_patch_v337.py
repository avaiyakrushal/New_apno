from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
manifest=root/'app/src/main/AndroidManifest.xml'
service=root/'app/src/main/java/com/example/diamonddiary/WorkerNoticeService.java'
j=java.read_text()
m=manifest.read_text()

# Start a no-billing Firestore foreground listener for worker notices.
marker='''    private void grantRole(FirebaseUser user, String role, String mode) {'''
helper='''    private void updateWorkerNoticeService(FirebaseUser user, String role) {
        Intent intent = new Intent(this, WorkerNoticeService.class);
        if (!"worker".equals(role) || user == null) {
            stopService(intent);
            return;
        }
        intent.putExtra("uid", user.getUid());
        intent.putExtra("company_id", currentCompanyId == null ? "" : currentCompanyId);
        intent.putExtra("company_code", currentCompanyCode == null ? "" : currentCompanyCode);
        intent.putExtra("company_name", currentCompanyName == null ? "" : currentCompanyName);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(intent);
            else startService(intent);
        } catch (Exception ignored) {}
    }

'''
if marker not in j: raise SystemExit('grantRole marker not found')
j=j.replace(marker,helper+marker,1)

needle='''        currentRole = role;
        currentMode = mode;
        if ("boss".equals(role)) currentCompanyId = user.getUid();
        startCloudSync(user);'''
rep='''        currentRole = role;
        currentMode = mode;
        if ("boss".equals(role)) currentCompanyId = user.getUid();
        updateWorkerNoticeService(user, role);
        startCloudSync(user);'''
if needle not in j: raise SystemExit('grantRole service anchor not found')
j=j.replace(needle,rep,1)

needle='''    private void signOut() {
        clearWorkerListener();'''
rep='''    private void signOut() {
        try { stopService(new Intent(this, WorkerNoticeService.class)); } catch (Exception ignored) {}
        clearWorkerListener();'''
if needle not in j: raise SystemExit('signOut anchor not found')
j=j.replace(needle,rep,1)

java.write_text(j)

# Manifest: foreground remote-messaging service so notices still arrive when app is in background.
if 'android.permission.FOREGROUND_SERVICE' not in m:
    m=m.replace('<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
                '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_REMOTE_MESSAGING" />',1)
svc='''        <service android:name=".WorkerNoticeService" android:exported="false" android:foregroundServiceType="remoteMessaging" />\n'''
if '.WorkerNoticeService' not in m:
    anchor='''        <service android:name=".DiaryMessagingService" android:exported="false">'''
    if anchor not in m: raise SystemExit('messaging service manifest anchor not found')
    m=m.replace(anchor,svc+anchor,1)
manifest.write_text(m)

service.write_text(r'''package com.example.diamonddiary;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.IBinder;

import androidx.annotation.Nullable;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.ListenerRegistration;

import java.util.Map;

public class WorkerNoticeService extends Service {
    private static final String SERVICE_CHANNEL = "mbdd_notice_listener";
    private static final String NOTICE_CHANNEL = "mbdd_company_notices";
    private static final int SERVICE_NOTIFICATION_ID = 4101;

    private final FirebaseFirestore db = FirebaseFirestore.getInstance();
    private ListenerRegistration codeListener;
    private ListenerRegistration companyListener;
    private ListenerRegistration workerListener;
    private String uid = "";
    private String companyCode = "";
    private String companyId = "";
    private String companyName = "";

    @Override public void onCreate() {
        super.onCreate();
        createChannels();
        startForeground(SERVICE_NOTIFICATION_ID, serviceNotification());
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            uid = clean(intent.getStringExtra("uid"));
            companyCode = clean(intent.getStringExtra("company_code"));
            companyId = clean(intent.getStringExtra("company_id"));
            companyName = clean(intent.getStringExtra("company_name"));
        }
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) { stopSelf(); return START_NOT_STICKY; }
        if (uid.length() == 0) uid = user.getUid();
        attachWorkerRemovalListener();
        if (companyCode.length() == 0 || companyId.length() == 0) {
            db.collection("users").document(uid).get().addOnSuccessListener(this::applyMembershipAndListen)
                .addOnFailureListener(e -> startNoticeListeners());
        } else startNoticeListeners();
        return START_STICKY;
    }

    private void applyMembershipAndListen(DocumentSnapshot d) {
        if (d != null && d.exists()) {
            if (companyCode.length() == 0) companyCode = clean(d.getString("companyCode"));
            if (companyId.length() == 0) companyId = clean(d.getString("companyId"));
            if (companyName.length() == 0) companyName = clean(d.getString("companyName"));
        }
        startNoticeListeners();
    }

    private void attachWorkerRemovalListener() {
        if (workerListener != null) workerListener.remove();
        if (uid.length() == 0) return;
        workerListener = db.collection("workers").document(uid).addSnapshotListener((doc,error) -> {
            if (error != null || doc == null || !doc.exists()) return;
            if (Boolean.TRUE.equals(doc.getBoolean("removed"))) stopSelf();
        });
    }

    private void startNoticeListeners() {
        clearNoticeListeners();
        if (companyCode.length() > 0) {
            codeListener = db.collection("companyCodes").document(companyCode).addSnapshotListener((doc,error) -> {
                if (error == null && doc != null && doc.exists()) handleLatest(doc.get("latestNotice"));
            });
        }
        if (companyId.length() > 0) {
            companyListener = db.collection("companies").document(companyId).addSnapshotListener((doc,error) -> {
                if (error == null && doc != null && doc.exists()) handleLatest(doc.get("latestNotice"));
            });
        }
    }

    @SuppressWarnings("unchecked")
    private void handleLatest(Object raw) {
        if (!(raw instanceof Map)) return;
        Map<String,Object> n = (Map<String,Object>) raw;
        String id = String.valueOf(n.get("id") == null ? "" : n.get("id"));
        String text = String.valueOf(n.get("text") == null ? "" : n.get("text")).trim();
        String cname = String.valueOf(n.get("companyName") == null ? "" : n.get("companyName")).trim();
        long at = 0L;
        Object millis = n.get("createdAtMillis");
        if (millis instanceof Number) at = ((Number) millis).longValue();
        if (id.length() == 0) id = text + "@" + at;
        if (text.length() == 0) text = "નવી સૂચના આવી છે";

        SharedPreferences p = getSharedPreferences("mb_worker_notice_service", MODE_PRIVATE);
        String last = p.getString("last_notice_id", "");
        if (id.equals(last)) return;
        p.edit().putString("last_notice_id", id).apply();
        showNotice(id, cname.length() > 0 ? cname : (companyName.length() > 0 ? companyName : "MB ડાયમંડ ડાયરી"), text, at);
    }

    private void showNotice(String id, String title, String text, long at) {
        Intent open = new Intent(this, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        open.putExtra("open_notifications", true);
        open.putExtra("notice_id", id);
        open.putExtra("notice_text", text);
        open.putExtra("notice_created_at", at);
        PendingIntent pending = PendingIntent.getActivity(this, id.hashCode(), open,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
            ? new Notification.Builder(this, NOTICE_CHANNEL)
            : new Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(new Notification.BigTextStyle().bigText(text))
            .setAutoCancel(true)
            .setContentIntent(pending)
            .setPriority(Notification.PRIORITY_HIGH);
        ((NotificationManager)getSystemService(NOTIFICATION_SERVICE))
            .notify((id.hashCode() & 0x7fffffff) % 100000 + 5000, b.build());
    }

    private Notification serviceNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent p = PendingIntent.getActivity(this, 4101, open,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
            ? new Notification.Builder(this, SERVICE_CHANNEL)
            : new Notification.Builder(this);
        return b.setSmallIcon(android.R.drawable.ic_popup_reminder)
            .setContentTitle("MB ડાયમંડ ડાયરી")
            .setContentText("શેઠની સૂચનાઓ માટે સેવા ચાલુ છે")
            .setOngoing(true)
            .setContentIntent(p)
            .setPriority(Notification.PRIORITY_MIN)
            .build();
    }

    private void createChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager nm = (NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        NotificationChannel service = new NotificationChannel(
            SERVICE_CHANNEL, "સૂચના સેવા", NotificationManager.IMPORTANCE_MIN);
        service.setDescription("કારીગરને શેઠની સૂચના તરત પહોંચાડવા માટે");
        nm.createNotificationChannel(service);
        NotificationChannel notices = new NotificationChannel(
            NOTICE_CHANNEL, "કંપની સૂચનાઓ", NotificationManager.IMPORTANCE_HIGH);
        notices.setDescription("શેઠ તરફથી આવતી સૂચનાઓ");
        nm.createNotificationChannel(notices);
    }

    private void clearNoticeListeners() {
        if (codeListener != null) { codeListener.remove(); codeListener = null; }
        if (companyListener != null) { companyListener.remove(); companyListener = null; }
    }

    private static String clean(String s) { return s == null ? "" : s.trim(); }

    @Override public void onDestroy() {
        clearNoticeListeners();
        if (workerListener != null) { workerListener.remove(); workerListener = null; }
        super.onDestroy();
    }

    @Nullable @Override public IBinder onBind(Intent intent) { return null; }
}
''')

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 73', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.15'", b, count=1)
build.write_text(b)
print('v3.2.15 background worker notification service applied')
