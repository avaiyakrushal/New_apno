from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
html=root/'app/src/main/assets/app.html'
j=java.read_text()
h=html.read_text()

# Worker notifications: open the notification screen automatically for a newly received notice.
# It is shown only once per notice id on this device.
old='''    private void pushNotifications() {
        if (page == null || page.getVisibility() != View.VISIBLE) return;
        try {
            org.json.JSONArray arr = new org.json.JSONArray();
            for (Map<String,Object> m : currentNotifications) {
                org.json.JSONObject o = new org.json.JSONObject();
                o.put("id", String.valueOf(m.get("id") == null ? "" : m.get("id")));
                o.put("text", String.valueOf(m.get("text") == null ? "" : m.get("text")));
                o.put("imageBase64", String.valueOf(m.get("imageBase64") == null ? "" : m.get("imageBase64")));
                Object millis = m.get("createdAtMillis");
                o.put("createdAt", millis instanceof Number ? ((Number)millis).longValue() : 0L);
                arr.put(o);
            }
            page.evaluateJavascript("window.mbNotifications && window.mbNotifications(" + arr.toString() + ");", null);
        } catch (Exception ignored) {}
    }'''
new='''    private void pushNotifications() {
        if (page == null || page.getVisibility() != View.VISIBLE) return;
        try {
            org.json.JSONArray arr = new org.json.JSONArray();
            org.json.JSONObject latestWorkerNotice = null;
            long latestAt = Long.MIN_VALUE;
            for (Map<String,Object> m : currentNotifications) {
                org.json.JSONObject o = new org.json.JSONObject();
                o.put("id", String.valueOf(m.get("id") == null ? "" : m.get("id")));
                o.put("text", String.valueOf(m.get("text") == null ? "" : m.get("text")));
                o.put("imageBase64", String.valueOf(m.get("imageBase64") == null ? "" : m.get("imageBase64")));
                Object millis = m.get("createdAtMillis");
                long at = millis instanceof Number ? ((Number)millis).longValue() : 0L;
                o.put("createdAt", at);
                arr.put(o);
                if (latestWorkerNotice == null || at > latestAt) {
                    latestWorkerNotice = o;
                    latestAt = at;
                }
            }
            page.evaluateJavascript("window.mbNotifications && window.mbNotifications(" + arr.toString() + ");", null);

            if ("worker".equals(currentRole) && latestWorkerNotice != null) {
                String id = latestWorkerNotice.optString("id", "");
                android.content.SharedPreferences prefs = getPreferences(MODE_PRIVATE);
                String shown = prefs.getString("last_auto_open_notice_id", "");
                if (id.length() > 0 && !id.equals(shown)) {
                    prefs.edit().putString("last_auto_open_notice_id", id).apply();
                    page.evaluateJavascript("window.mbOpenWorkerNotice && window.mbOpenWorkerNotice(" + latestWorkerNotice.toString() + ");", null);
                }
            }
        } catch (Exception ignored) {}
    }'''
if old not in j: raise SystemExit('pushNotifications block not found')
j=j.replace(old,new,1)

# When an Android notification is tapped, open the in-app notifications page directly.
marker='''    @Override protected void onStart() {'''
helper='''    private void openNotificationsFromIntent(Intent intent) {
        if (intent == null || !intent.getBooleanExtra("open_notifications", false)) return;
        intent.removeExtra("open_notifications");
        if (page != null) {
            page.postDelayed(() -> {
                if (page.getVisibility() == View.VISIBLE)
                    page.evaluateJavascript("window.mbOpenNotificationsScreen && window.mbOpenNotificationsScreen();", null);
            }, 500);
        }
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        openNotificationsFromIntent(intent);
    }

'''
if marker not in j: raise SystemExit('onStart marker not found')
j=j.replace(marker,helper+marker,1)

# Also honor a notification tap when Activity is launched cold.
needle='''        routeSignedInUser(user);
    }

    @Override protected void onStart()'''
if needle in j:
    j=j.replace(needle,'''        routeSignedInUser(user);
        openNotificationsFromIntent(getIntent());
    }

    @Override protected void onStart()''',1)

java.write_text(j)

# In-app visual: directly open the notifications screen and show a prominent latest-notice card.
insert='''window.mbNoticeDeleted=(ok,message)=>{if(message)alert(message);};'''
replace='''window.mbOpenNotificationsScreen=()=>openScreen('notifications');
window.mbOpenWorkerNotice=n=>{
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
};
window.mbNoticeDeleted=(ok,message)=>{if(message)alert(message);};'''
if insert not in h: raise SystemExit('notification JS insertion point not found')
h=h.replace(insert,replace,1)

# Make the automatically opened notice stand out.
css_anchor='''.notice{'''
idx=h.find(css_anchor)
if idx < 0: raise SystemExit('notice css anchor not found')
# Add style near end of style block instead of rewriting existing .notice.
style='''.latest-notice{border:2px solid #b80f38;box-shadow:0 8px 22px rgba(184,15,56,.16);background:#fff8fa}.latest-notice .notice-head b{color:#a80d32}'''
style_end=h.find('</style>')
if style_end < 0: raise SystemExit('style end not found')
h=h[:style_end]+style+h[style_end:]

html.write_text(h)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 69', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.11'", b, count=1)
build.write_text(b)
print('v3.2.11 worker notification auto-open + direct notification screen applied')
