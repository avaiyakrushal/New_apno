from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 87","versionCode 88").replace("versionName '3.2.29'","versionName '3.2.30'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

old="""    @Override protected void onResume() {
        super.onResume();
        mergeCachedPushNotifications();
        if ("worker".equals(currentRole) && currentCompanyId != null && currentCompanyId.length() > 0) {
            watchNotifications(currentCompanyId);
        }
        if (page != null && page.getVisibility() == View.VISIBLE) {
            pushNotifications();
        }
    }
"""
new="""    @Override protected void onResume() {
        super.onResume();
        mergeCachedPushNotifications();
        if ("worker".equals(currentRole) && currentCompanyId != null && currentCompanyId.length() > 0) {
            watchNotifications(currentCompanyId);
        }
        if (auth != null && auth.getCurrentUser() != null) {
            startEventualSyncLoop();
            eventualSyncHandler.post(this::runEventualSyncNow);
        }
        if (page != null && page.getVisibility() == View.VISIBLE) {
            pushNotifications();
        }
    }
"""
if old not in s: raise SystemExit("onResume block not found")
s=s.replace(old,new,1)

old="""    @Override protected void onDestroy() {
        clearWorkerListener();
        clearBossWorkersListener();
        clearCloudListeners();
"""
new="""    @Override protected void onDestroy() {
        eventualSyncHandler.removeCallbacks(eventualSyncRunnable);
        eventualSyncHandler.removeCallbacksAndMessages(null);
        eventualSyncStarted = false;
        clearWorkerListener();
        clearBossWorkersListener();
        clearCloudListeners();
"""
if old not in s: raise SystemExit("onDestroy block not found")
s=s.replace(old,new,1)

p.write_text(s)
print("v3.2.30 resume + 30-minute guaranteed fallback sync applied")
