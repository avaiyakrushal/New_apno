from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

# Bump version after v3.2.18 patch
gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 76","versionCode 77").replace("versionName '3.2.18'","versionName '3.2.19'")
gradle.write_text(s)

# Restore date/time on every notification card and dashboard preview.
html=root/"app/src/main/assets/app.html"
s=html.read_text()
old="""window.mbNotifications = list => {
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const items=(list||[]).slice().sort((a,b)=>Number(b.createdAt||0)-Number(a.createdAt||0));
  const render=(bossMode)=>items.length?items.map(n=>{
    const img=n.imageBase64?`<img alt="સૂચના ફોટો" src="data:image/jpeg;base64,${n.imageBase64}">`:'';
    const when=n.createdAt?new Date(Number(n.createdAt)).toLocaleString('gu-IN'):'';
    const del=bossMode&&n.id?`<button class="notice-delete" data-delete-notice="${esc(n.id)}" type="button">🗑 કાઢો</button>`:'';
    return `<div class="notice"><div class="notice-head"><b>${esc(n.text||'ફોટો સૂચના')}</b>${del}</div>${img}${when?`<div class="small" style="margin-top:7px">${esc(when)}</div>`:''}</div>`;
  }).join(''):'<p class="small">હજુ કોઈ સૂચના નથી.</p>';
"""
new="""window.mbNotifications = list => {
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const noticeMs=n=>Number((n&&((n.createdAt??n.createdAtMillis)))||0);
  const noticeWhen=n=>{
    const ms=noticeMs(n); if(!ms)return '';
    const d=new Date(ms); if(Number.isNaN(d.getTime()))return '';
    const date=d.toLocaleDateString('gu-IN');
    const time=d.toLocaleTimeString('gu-IN',{hour:'2-digit',minute:'2-digit'});
    return `તારીખ: ${date} • સમય: ${time}`;
  };
  const items=(list||[]).slice().sort((a,b)=>noticeMs(b)-noticeMs(a));
  const render=(bossMode)=>items.length?items.map(n=>{
    const img=n.imageBase64?`<img alt="સૂચના ફોટો" src="data:image/jpeg;base64,${n.imageBase64}">`:'';
    const when=noticeWhen(n);
    const del=bossMode&&n.id?`<button class="notice-delete" data-delete-notice="${esc(n.id)}" type="button">🗑 કાઢો</button>`:'';
    return `<div class="notice"><div class="notice-head"><b>${esc(n.text||'ફોટો સૂચના')}</b>${del}</div>${img}${when?`<div class="small" style="margin-top:7px;font-weight:700">${esc(when)}</div>`:''}</div>`;
  }).join(''):'<p class="small">હજુ કોઈ સૂચના નથી.</p>';
"""
if old not in s:
    raise SystemExit("notification render block not found")
s=s.replace(old,new)

s=s.replace(
"      if(previewTime) previewTime.textContent=latest.createdAt?new Date(Number(latest.createdAt)).toLocaleString('gu-IN'):'';",
"      if(previewTime) previewTime.textContent=noticeWhen(latest);"
)

old2="""  const dt=n?.createdAt?new Date(Number(n.createdAt)):null;
  const when=dt?dt.toLocaleString('gu-IN'):'';
  const today=dt && new Date().toDateString()===dt.toDateString();
"""
new2="""  const ms=Number((n&&((n.createdAt??n.createdAtMillis)))||0);
  const dt=ms?new Date(ms):null;
  const when=dt && !Number.isNaN(dt.getTime())?('તારીખ: '+dt.toLocaleDateString('gu-IN')+' • સમય: '+dt.toLocaleTimeString('gu-IN',{hour:'2-digit',minute:'2-digit'})):'';
  const today=dt && !Number.isNaN(dt.getTime()) && new Date().toDateString()===dt.toDateString();
"""
if old2 not in s:
    raise SystemExit("worker notice banner time block not found")
s=s.replace(old2,new2)
s=s.replace("  banner.children[2].textContent=when?('તારીખ/સમય: '+when):'';","  banner.children[2].textContent=when;")
html.write_text(s)

# Make Java always expose both timestamp keys, and make delete remove mirrored copies too.
java=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=java.read_text()
s=s.replace(
"""                Object millis = m.get("createdAtMillis");
                o.put("createdAt", millis instanceof Number ? ((Number)millis).longValue() : 0L);
                arr.put(o);
""",
"""                Object millis = m.get("createdAtMillis");
                long noticeTime = millis instanceof Number ? ((Number)millis).longValue() : 0L;
                o.put("createdAt", noticeTime);
                o.put("createdAtMillis", noticeTime);
                arr.put(o);
"""
)

old_delete="""    private void deleteNotificationFromWeb(String id) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !"boss".equals(currentRole) || id == null || !id.matches("[A-Za-z0-9_-]{1,128}")) return;
        final String uid = user.getUid();
        database.collection("notifications").document(id).get().addOnSuccessListener(doc -> {
            if (!doc.exists()) { page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'સૂચના મળી નથી')", null); return; }
            String companyId = safe(doc.getString("companyId"));
            String senderUid = safe(doc.getString("senderUid"));
            if (!uid.equals(companyId) || !uid.equals(senderUid)) {
                page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'આ સૂચના ડિલીટ કરવાની પરવાનગી નથી')", null);
                return;
            }
            doc.getReference().delete()
                .addOnSuccessListener(v -> page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(true,'સૂચના ડિલીટ થઈ ગઈ')", null))
                .addOnFailureListener(e -> page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'સૂચના ડિલીટ થઈ નથી')", null));
        }).addOnFailureListener(e -> page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'સૂચના ચેક થઈ નથી')", null));
    }
"""
new_delete="""    private void deleteNotificationFromWeb(String id) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !"boss".equals(currentRole) || id == null || !id.matches("[A-Za-z0-9_-]{1,128}")) return;
        final String uid = user.getUid();
        database.collection("notifications").document(id).get().addOnSuccessListener(doc -> {
            if (!doc.exists()) {
                // Root copy may already be gone. Still remove mirrored copies and local card.
                if (currentCompanyCode != null && currentCompanyCode.length() > 0)
                    database.collection("companyCodes").document(currentCompanyCode).collection("notices").document(id).delete();
                if (currentCompanyId != null && currentCompanyId.length() > 0)
                    database.collection("companies").document(currentCompanyId).collection("notices").document(id).delete();
                for (int i=currentNotifications.size()-1;i>=0;i--) {
                    Object raw=currentNotifications.get(i).get("id");
                    if (id.equals(String.valueOf(raw == null ? "" : raw))) currentNotifications.remove(i);
                }
                mirrorCurrentBossNoticesToCompanyCode();
                pushNotifications();
                page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(true,'સૂચના ડિલીટ થઈ ગઈ')", null);
                return;
            }

            String companyId = safe(doc.getString("companyId"));
            String senderUid = safe(doc.getString("senderUid"));
            boolean sameCompany = currentCompanyId == null || currentCompanyId.length() == 0 || currentCompanyId.equals(companyId);
            if (!uid.equals(senderUid) || !sameCompany) {
                page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'આ સૂચના ડિલીટ કરવાની પરવાનગી નથી')", null);
                return;
            }

            doc.getReference().delete().addOnSuccessListener(v -> {
                if (currentCompanyCode != null && currentCompanyCode.length() > 0)
                    database.collection("companyCodes").document(currentCompanyCode).collection("notices").document(id).delete();
                if (currentCompanyId != null && currentCompanyId.length() > 0)
                    database.collection("companies").document(currentCompanyId).collection("notices").document(id).delete();

                for (int i=currentNotifications.size()-1;i>=0;i--) {
                    Object raw=currentNotifications.get(i).get("id");
                    if (id.equals(String.valueOf(raw == null ? "" : raw))) currentNotifications.remove(i);
                }

                // Refresh both shared "latest notice" locations so deleted notices cannot reappear.
                mirrorCurrentBossNoticesToCompanyCode();
                if (currentCompanyId != null && currentCompanyId.length() > 0) {
                    Map<String,Object> update = new HashMap<>();
                    if (currentNotifications.isEmpty()) {
                        update.put("latestNotice", com.google.firebase.firestore.FieldValue.delete());
                    } else {
                        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                        Map<String,Object> src = currentNotifications.get(0);
                        Map<String,Object> latest = new HashMap<>();
                        latest.put("id", String.valueOf(src.get("id") == null ? "" : src.get("id")));
                        latest.put("text", String.valueOf(src.get("text") == null ? "" : src.get("text")));
                        latest.put("imageBase64", String.valueOf(src.get("imageBase64") == null ? "" : src.get("imageBase64")));
                        latest.put("createdAtMillis", noticeMillis(src));
                        latest.put("companyId", currentCompanyId);
                        latest.put("companyCode", currentCompanyCode == null ? "" : currentCompanyCode);
                        update.put("latestNotice", latest);
                    }
                    database.collection("companies").document(currentCompanyId)
                        .set(update, com.google.firebase.firestore.SetOptions.merge());
                }

                pushNotifications();
                page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(true,'સૂચના ડિલીટ થઈ ગઈ')", null);
            }).addOnFailureListener(e ->
                page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'સૂચના ડિલીટ થઈ નથી')", null));
        }).addOnFailureListener(e ->
            page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(false,'સૂચના ચેક થઈ નથી')", null));
    }
"""
if old_delete not in s:
    raise SystemExit("delete notification block not found")
s=s.replace(old_delete,new_delete)
java.write_text(s)

print("v3.2.19 notification time/delete fixes applied")
