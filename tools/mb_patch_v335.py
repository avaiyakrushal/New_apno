from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
html=root/'app/src/main/assets/app.html'
j=java.read_text()
h=html.read_text()

# v3.2.13: reliably auto-open the newest worker notice once per app session.
# Do not persist the "already opened" id across app restarts, because the worker
# should see the latest notice immediately when opening the app again.
marker='''    private void pushNotifications() {'''
helper='''    private String autoOpenedWorkerNoticeId = "";

    private void openWorkerNoticeWhenReady(org.json.JSONObject notice) {
        if (page == null || notice == null) return;
        final String payload = notice.toString();
        page.postDelayed(() -> {
            if (page == null || page.getVisibility() != View.VISIBLE) return;
            page.evaluateJavascript(
                "(function(){if(window.mbOpenWorkerNotice){window.mbOpenWorkerNotice(" + payload + ");return 'opened';}return 'not-ready';})()",
                value -> {
                    if (value != null && value.contains("not-ready")) {
                        page.postDelayed(() -> page.evaluateJavascript(
                            "window.mbOpenWorkerNotice && window.mbOpenWorkerNotice(" + payload + ");", null), 900);
                    }
                });
        }, 450);
    }

'''
if marker not in j: raise SystemExit('pushNotifications marker not found')
j=j.replace(marker,helper+marker,1)

old='''            if ("worker".equals(currentRole) && latestWorkerNotice != null) {
                String id = latestWorkerNotice.optString("id", "");
                android.content.SharedPreferences prefs = getPreferences(MODE_PRIVATE);
                String shown = prefs.getString("last_auto_open_notice_id", "");
                if (id.length() > 0 && !id.equals(shown)) {
                    prefs.edit().putString("last_auto_open_notice_id", id).apply();
                    page.evaluateJavascript("window.mbOpenWorkerNotice && window.mbOpenWorkerNotice(" + latestWorkerNotice.toString() + ");", null);
                }
            }'''
new='''            if ("worker".equals(currentRole) && latestWorkerNotice != null) {
                String id = latestWorkerNotice.optString("id", "");
                if (id.length() > 0 && !id.equals(autoOpenedWorkerNoticeId)) {
                    autoOpenedWorkerNoticeId = id;
                    openWorkerNoticeWhenReady(latestWorkerNotice);
                }
            }'''
if old not in j: raise SystemExit('old worker auto-open block not found')
j=j.replace(old,new,1)

# Reset per-session notice state whenever a worker role is granted so a fresh app/login
# immediately presents today's/latest notice.
needle='''    private void grantRole(FirebaseUser user, String role, String mode) {'''
rep='''    private void grantRole(FirebaseUser user, String role, String mode) {
        if ("worker".equals(role) && !"worker".equals(currentRole)) autoOpenedWorkerNoticeId = "";'''
if needle not in j: raise SystemExit('grantRole anchor not found')
j=j.replace(needle,rep,1)

# Make the in-app notice card explicit and date-forward.
old_js='''window.mbOpenWorkerNotice=n=>{
  openScreen('notifications');
  const worker=document.getElementById('workerNoticeList');
  if(!worker)return;
  const old=document.getElementById('latestWorkerNoticeBanner'); if(old)old.remove();
  const text=String(n?.text||'નવી સૂચના');
  const when=n?.createdAt?new Date(Number(n.createdAt)).toLocaleString('gu-IN'):'';
  const banner=document.createElement('div');
  banner.id='latestWorkerNoticeBanner';
  banner.className='notice latest-notice';
  banner.innerHTML='<div class="notice-head"><b>🔔 નવી સૂચના</b></div><div style="margin-top:8px;font-size:18px;font-weight:700"></div><div class="small" style="margin-top:8px"></div>';
  banner.children[1].textContent=text;
  banner.children[2].textContent=when?('મોકલ્યાનો સમય: '+when):'';
  worker.prepend(banner);
  banner.scrollIntoView({behavior:'smooth',block:'start'});
};'''
new_js='''window.mbOpenWorkerNotice=n=>{
  openScreen('notifications');
  const worker=document.getElementById('workerNoticeList');
  if(!worker)return false;
  const old=document.getElementById('latestWorkerNoticeBanner'); if(old)old.remove();
  const text=String(n?.text||'નવી સૂચના');
  const dt=n?.createdAt?new Date(Number(n.createdAt)):null;
  const when=dt?dt.toLocaleString('gu-IN'):'';
  const today=dt && new Date().toDateString()===dt.toDateString();
  const banner=document.createElement('div');
  banner.id='latestWorkerNoticeBanner';
  banner.className='notice latest-notice';
  banner.innerHTML='<div class="notice-head"><b></b></div><div style="margin-top:8px;font-size:18px;font-weight:700"></div><div class="small" style="margin-top:8px"></div>';
  banner.children[0].children[0].textContent=today?'🔔 આજની સૂચના':'🔔 નવી સૂચના';
  banner.children[1].textContent=text;
  banner.children[2].textContent=when?('તારીખ/સમય: '+when):'';
  worker.prepend(banner);
  banner.scrollIntoView({behavior:'smooth',block:'start'});
  return true;
};'''
if old_js not in h: raise SystemExit('mbOpenWorkerNotice JS block not found')
h=h.replace(old_js,new_js,1)

html.write_text(h)
java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 71', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.13'", b, count=1)
build.write_text(b)
print('v3.2.13 reliable worker notification auto-open applied')
