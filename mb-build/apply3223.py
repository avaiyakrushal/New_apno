from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

gradle=root/"app/build.gradle"
s=gradle.read_text()
s=s.replace("versionCode 80","versionCode 81").replace("versionName '3.2.22'","versionName '3.2.23'")
gradle.write_text(s)

html=root/"app/src/main/assets/app.html"
s=html.read_text()

old='<div id="diamondRateGrid" class="grid rate-grid-simple"><b>ગ્રેડ</b><b>દર ₹</b><b>A</b><input type="text" inputmode="decimal" value="40"><b>B</b><input type="text" inputmode="decimal" value="50"><b>C</b><input type="text" inputmode="decimal" value="60"><b>D</b><input type="text" inputmode="decimal" value="70"><b>E</b><input type="text" inputmode="decimal" value="80"><b>F</b><input type="text" inputmode="decimal" value="90"><b>G</b><input type="text" inputmode="decimal" value="100"></div>'
new='<div id="diamondRateGrid" class="grid rate-grid-point"><b>ગ્રેડ</b><b>દર ₹</b><b>પોઇન્ટ</b><b>A</b><input type="text" inputmode="decimal" value="40"><button type="button" class="rate-dot">.</button><b>B</b><input type="text" inputmode="decimal" value="50"><button type="button" class="rate-dot">.</button><b>C</b><input type="text" inputmode="decimal" value="60"><button type="button" class="rate-dot">.</button><b>D</b><input type="text" inputmode="decimal" value="70"><button type="button" class="rate-dot">.</button><b>E</b><input type="text" inputmode="decimal" value="80"><button type="button" class="rate-dot">.</button><b>F</b><input type="text" inputmode="decimal" value="90"><button type="button" class="rate-dot">.</button><b>G</b><input type="text" inputmode="decimal" value="100"><button type="button" class="rate-dot">.</button></div>'
if old not in s: raise SystemExit("diamond rate grid not found")
s=s.replace(old,new)

oldh='<div id="hourRateSettings" class="panel"><h3>કલાકનો દર</h3><label>એક કલાકનો દર ₹</label><input id="hourRateInput" type="text" inputmode="decimal" value="100"><p class="hint">દશાંશ દર માટે મોબાઇલ કીબોર્ડનો . ઉપયોગ કરો, જેમ કે 101.15. કલાક/ઓફિસ કામ પસંદ કરેલા કારીગર માટે આ દર સેવ થશે.</p><button id="saveHourRate" class="action" type="button">કલાકનો દર સેવ કરો</button></div>'
newh='<div id="hourRateSettings" class="panel"><h3>કલાકનો દર</h3><label>એક કલાકનો દર ₹</label><input id="hourRateInput" type="text" inputmode="decimal" value="100"><button id="hourRateDot" type="button" class="choice rate-point-button">. પોઇન્ટ ઉમેરો</button><p class="hint">દશાંશ દર માટે ઉપરનો પોઇન્ટ બટન અથવા મોબાઇલ કીબોર્ડનો . ઉપયોગ કરો, જેમ કે 101.15.</p><button id="saveHourRate" class="action" type="button">કલાકનો દર સેવ કરો</button></div>'
if oldh not in s: raise SystemExit("hour rate settings block not found")
s=s.replace(oldh,newh)

oldv='<label>કામના કલાક</label><input id="hourValue" type="text" inputmode="decimal" placeholder="જેમ કે 7.5"><label>એક કલાકનો સેવ કરેલો દર ₹</label>'
newv='<label>કામના કલાક</label><input id="hourValue" type="text" inputmode="decimal" placeholder="જેમ કે 7.5"><button id="hourValueDot" type="button" class="choice rate-point-button">. પોઇન્ટ ઉમેરો</button><label>એક કલાકનો સેવ કરેલો દર ₹</label>'
if oldv not in s: raise SystemExit("hour value block not found")
s=s.replace(oldv,newv)

s=s.replace('.rate-grid-simple{grid-template-columns:60px minmax(0,1fr)!important}', '.rate-grid-simple{grid-template-columns:60px minmax(0,1fr)!important}.rate-grid-point{grid-template-columns:52px minmax(0,1fr) 76px!important;align-items:center}.rate-dot{min-height:42px;border:1px solid #d8dee8;border-radius:10px;background:#fff;color:#9b1e3b;font-weight:900;font-size:22px}.rate-point-button{margin:7px 0 9px!important;padding:9px 12px!important}')
html.write_text(s)

js=root/"app/src/main/assets/app.js"
s=js.read_text()

s=s.replace("const e=entries.find(x=>x.id===id);if(!e)return; editHourId=id; pendingHourId=id;", "const sid=String(id);const e=entries.find(x=>x.type==='hour'&&String(x.id)===sid);if(!e)return; editHourId=String(e.id); pendingHourId=String(e.id);")
s=s.replace("const e=entries.find(x=>x.id===id&&x.type==='hour'); if(!e)return;", "const sid=String(id);const e=entries.find(x=>x.type==='hour'&&String(x.id)===sid); if(!e)return;")
s=s.replace("if(editHourId===id){editHourId=null;pendingHourId=null;editHourRate=null;clearHourValues();detectHourExisting();}", "if(String(editHourId||'')===String(id)){editHourId=null;pendingHourId=null;editHourRate=null;clearHourValues();detectHourExisting();}")

old_edit="""    if(editHourId){
      const oldHours=entries.filter(e=>e.type==='hour'&&e.date===date), oldWithdrawals=entries.filter(e=>e.type==='withdrawal'&&e.source==='hour'&&e.date===date);
      markDeletedIds([...oldHours,...oldWithdrawals].map(e=>e.id));
      [...oldHours,...oldWithdrawals].forEach(e=>{try{window.Android?.deleteEntry(e.id)}catch(_){}});
      entries=entries.filter(e=>!((e.type==='hour'&&e.date===date)||(e.type==='withdrawal'&&e.source==='hour'&&e.date===date)));
      const ts=Date.now(),savedRate=(Number(editHourRate)>0?Number(editHourRate):Number(hourRate));const items=[{id:`h-${ts}`,type:'hour',date,hours,rate:savedRate,amount:hours*savedRate}];if(withdrawal)items.push({id:`wh-${ts}`,type:'withdrawal',source:'hour',date,amount:withdrawal});
      entries.push(...items);persistLocal();try{window.Android?.syncEntries(JSON.stringify(items))}catch(_){};renderReports();alert('ફેરફાર સેવ થયા');
    } else {
"""
new_edit="""    if(editHourId){
      const original=entries.find(e=>e.type==='hour'&&String(e.id)===String(editHourId));
      if(!original){editHourId=null;detectHourExisting();alert('એડિટ માટેની જૂની કલાક એન્ટ્રી મળી નથી. ફરી યાદીમાંથી એડિટ દબાવો.');return}
      const originalDate=original.date;
      const oldHours=entries.filter(e=>e.type==='hour'&&String(e.id)===String(original.id));
      const oldWithdrawals=entries.filter(e=>e.type==='withdrawal'&&e.source==='hour'&&e.date===originalDate);
      markDeletedIds([...oldHours,...oldWithdrawals].map(e=>e.id));
      [...oldHours,...oldWithdrawals].forEach(e=>{try{window.Android?.deleteEntry(e.id)}catch(_){}});
      entries=entries.filter(e=>!((e.type==='hour'&&String(e.id)===String(original.id))||(e.type==='withdrawal'&&e.source==='hour'&&e.date===originalDate)));
      const ts=Date.now(),savedRate=(Number(editHourRate)>0?Number(editHourRate):Number(hourRate));const items=[{id:`h-${ts}`,type:'hour',date,hours,rate:savedRate,amount:hours*savedRate}];if(withdrawal)items.push({id:`wh-${ts}`,type:'withdrawal',source:'hour',date,amount:withdrawal});
      entries.push(...items);persistLocal();try{window.Android?.syncEntries(JSON.stringify(items))}catch(_){};renderReports();renderEntryLists();alert('ફેરફાર સેવ થયા');
    } else {
"""
if old_edit not in s: raise SystemExit("hour edit save branch not found")
s=s.replace(old_edit,new_edit)

needle="""  const saveDiamondRates=$('#saveDiamondRates');
"""
point_js="""  $$('#diamondRateGrid .rate-dot').forEach(btn=>btn.addEventListener('click',()=>insertDecimalPoint(btn.previousElementSibling)));
  const hourRateDot=$('#hourRateDot'); if(hourRateDot) hourRateDot.addEventListener('click',()=>insertDecimalPoint($('#hourRateInput')));
  const hourValueDot=$('#hourValueDot'); if(hourValueDot) hourValueDot.addEventListener('click',()=>{
    const el=$('#hourValue'); if(!el)return;
    let t=String(el.value||'').replace(',', '.').replace(/[^0-9.]/g,''); if(!t)t='0'; if(!t.includes('.'))t+='.'; el.value=t;
    try{el.focus();const p=el.value.length;el.setSelectionRange(p,p)}catch(_){}; el.dispatchEvent(new Event('input',{bubbles:true}));
  });

"""
if needle not in s: raise SystemExit("point js insertion point not found")
s=s.replace(needle,point_js+needle)
js.write_text(s)

java=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=java.read_text()

s=s.replace("    private ListenerRegistration notificationUserListener;
", "    private ListenerRegistration notificationUserListener;
    private long bossWorkerRenderRevision = 0L;
    private final Set<String> deletedNoticeIds = new HashSet<>();
")

old="""    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
        String month = currentMonthKey();
        renderBossWorkers(docs, null, month);
        refreshBossDashboardFromEntries(docs, companyId, month);
    }
"""
new="""    private void renderBossWorkerDocuments(List<DocumentSnapshot> docs, String companyId) {
        String month = currentMonthKey();
        List<DocumentSnapshot> stable = new ArrayList<>(docs);
        stable.sort((a,b) -> Long.compare(workerJoinedMillis(b), workerJoinedMillis(a)));
        long revision = ++bossWorkerRenderRevision;
        renderBossWorkers(stable, null, month);
        refreshBossDashboardFromEntries(stable, companyId, month, revision);
    }

    private long workerJoinedMillis(DocumentSnapshot worker) {
        if (worker == null) return 0L;
        Timestamp t = worker.getTimestamp("joinedAt");
        if (t != null) return t.toDate().getTime();
        return 0L;
    }
"""
if old not in s: raise SystemExit("renderBossWorkerDocuments block not found")
s=s.replace(old,new)
s=s.replace("private void refreshBossDashboardFromEntries(List<DocumentSnapshot> workers, String companyId, String month) {", "private void refreshBossDashboardFromEntries(List<DocumentSnapshot> workers, String companyId, String month, long revision) {")
s=s.replace('if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId)) return;
                        renderBossWorkers(workers, live, month);', 'if (active == null || !"boss".equals(currentRole) || currentCompanyId == null || !companyId.equals(currentCompanyId) || revision != bossWorkerRenderRevision) return;
                        renderBossWorkers(workers, live, month);')

old_filters="""        LinearLayout filters = new LinearLayout(this);
        filters.setOrientation(LinearLayout.HORIZONTAL);
        Button diamondFilter = primaryButton("હીરા ડિપાર્ટમેન્ટ");
        Button hourFilter = secondaryButton("કલાક ડિપાર્ટમેન્ટ");
        filters.addView(diamondFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        filters.addView(hourFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        bossWorkers.addView(filters, fullWrap());
        LinearLayout filteredList = new LinearLayout(this);
        filteredList.setOrientation(LinearLayout.VERTICAL);
        bossWorkers.addView(filteredList, fullWrap());
        Runnable showDiamond = () -> {
            styleBossDepartmentButtons(diamondFilter, hourFilter, true);
            renderBossDepartment(filteredList, "diamond", diamondWorkers, live, month);
        };
        Runnable showHours = () -> {
            styleBossDepartmentButtons(diamondFilter, hourFilter, false);
            renderBossDepartment(filteredList, "hour", hourWorkers, live, month);
        };
        diamondFilter.setOnClickListener(v -> showDiamond.run());
        hourFilter.setOnClickListener(v -> showHours.run());
        showDiamond.run();
"""
new_filters="""        LinearLayout filters = new LinearLayout(this);
        filters.setOrientation(LinearLayout.HORIZONTAL);
        Button allFilter = primaryButton("બધા");
        Button diamondFilter = secondaryButton("હીરા");
        Button hourFilter = secondaryButton("કલાક");
        filters.addView(allFilter, new LinearLayout.LayoutParams(0, -2, 0.8f));
        filters.addView(diamondFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        filters.addView(hourFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        bossWorkers.addView(filters, fullWrap());
        LinearLayout filteredList = new LinearLayout(this);
        filteredList.setOrientation(LinearLayout.VERTICAL);
        bossWorkers.addView(filteredList, fullWrap());
        Runnable showAll = () -> {
            styleBossWorkerFilters(allFilter, diamondFilter, hourFilter, allFilter);
            renderBossDepartment(filteredList, "all", documents, live, month);
        };
        Runnable showDiamond = () -> {
            styleBossWorkerFilters(allFilter, diamondFilter, hourFilter, diamondFilter);
            renderBossDepartment(filteredList, "diamond", diamondWorkers, live, month);
        };
        Runnable showHours = () -> {
            styleBossWorkerFilters(allFilter, diamondFilter, hourFilter, hourFilter);
            renderBossDepartment(filteredList, "hour", hourWorkers, live, month);
        };
        allFilter.setOnClickListener(v -> showAll.run());
        diamondFilter.setOnClickListener(v -> showDiamond.run());
        hourFilter.setOnClickListener(v -> showHours.run());
        showAll.run();
"""
if old_filters not in s: raise SystemExit("boss filter block not found")
s=s.replace(old_filters,new_filters)

old_style="""    private void styleBossDepartmentButtons(Button diamondFilter, Button hourFilter, boolean diamondSelected) {
        Button selected = diamondSelected ? diamondFilter : hourFilter;
        Button other = diamondSelected ? hourFilter : diamondFilter;
        selected.setTextColor(0xffffffff);
        selected.setBackgroundTintList(ColorStateList.valueOf(0xffa80d32));
        other.setTextColor(0xff9b1e3b);
        other.setBackgroundTintList(ColorStateList.valueOf(0xffffffff));
        selected.setEnabled(true);
        other.setEnabled(true);
    }
"""
new_style="""    private void styleBossWorkerFilters(Button all, Button diamond, Button hour, Button selected) {
        Button[] buttons = new Button[]{all, diamond, hour};
        for (Button button : buttons) {
            boolean on = button == selected;
            button.setTextColor(on ? 0xffffffff : 0xff9b1e3b);
            button.setBackgroundTintList(ColorStateList.valueOf(on ? 0xffa80d32 : 0xffffffff));
            button.setEnabled(true);
        }
    }
"""
if old_style not in s: raise SystemExit("boss filter style block not found")
s=s.replace(old_style,new_style)

s=s.replace('TextView title = sectionText(("diamond".equals(mode) ? "હીરા ડિપાર્ટમેન્ટ" : "કલાક ડિપાર્ટમેન્ટ") + " · " + workers.size() + " કારીગર");', 'String sectionName = "all".equals(mode) ? "બધા કારીગર" : ("diamond".equals(mode) ? "હીરા ડિપાર્ટમેન્ટ" : "કલાક ડિપાર્ટમેન્ટ");
        TextView title = sectionText(sectionName + " · " + workers.size() + " કારીગર");')
s=s.replace('if ("diamond".equals(mode)) workText = "કુલ કામ: " + pieces + " નંગ";
        else {', 'if ("all".equals(mode)) {
            String h = String.format(Locale.US, "%.2f", hours); if (h.endsWith(".00")) h = h.substring(0, h.length()-3);
            workText = "હીરા: " + pieces + " નંગ  ·  કલાક: " + h;
        } else if ("diamond".equals(mode)) workText = "કુલ કામ: " + pieces + " નંગ";
        else {')

s=s.replace('worker.put("removed", false);
                    database.collection("workers")', 'worker.put("removed", false);
                    worker.put("joinedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                    database.collection("workers")')

anchor="""    private void upsertSharedNotification(Map<String,Object> incoming) {
"""
helpers="""    private void rememberDeletedNotice(String id) {
        if (id == null || id.length() == 0) return;
        deletedNoticeIds.add(id);
        getSharedPreferences("mb_notice_deletes", MODE_PRIVATE).edit().putBoolean(id, true).apply();
        for (int i=currentNotifications.size()-1;i>=0;i--) {
            String existing = String.valueOf(currentNotifications.get(i).get("id") == null ? "" : currentNotifications.get(i).get("id"));
            if (id.equals(existing)) currentNotifications.remove(i);
        }
    }

    private boolean isNoticeDeleted(String id) {
        if (id == null || id.length() == 0) return false;
        return deletedNoticeIds.contains(id) || getSharedPreferences("mb_notice_deletes", MODE_PRIVATE).getBoolean(id, false);
    }

    private void absorbDeletedNoticeIds(Object raw) {
        if (!(raw instanceof List)) return;
        boolean changed = false;
        for (Object one : (List<?>) raw) {
            String id = String.valueOf(one == null ? "" : one);
            if (id.length() > 0 && deletedNoticeIds.add(id)) {
                getSharedPreferences("mb_notice_deletes", MODE_PRIVATE).edit().putBoolean(id, true).apply();
                changed = true;
            }
        }
        if (changed) {
            for (int i=currentNotifications.size()-1;i>=0;i--) {
                String id = String.valueOf(currentNotifications.get(i).get("id") == null ? "" : currentNotifications.get(i).get("id"));
                if (isNoticeDeleted(id)) currentNotifications.remove(i);
            }
            pushNotifications();
        }
    }

    private void markNoticeDeletedForCompany(String id) {
        if (id == null || id.length() == 0) return;
        Map<String,Object> mark = new HashMap<>();
        mark.put("deletedNoticeIds", com.google.firebase.firestore.FieldValue.arrayUnion(id));
        mark.put("noticeUpdatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
        if (currentCompanyId != null && currentCompanyId.length() > 0)
            database.collection("companies").document(currentCompanyId).set(mark, com.google.firebase.firestore.SetOptions.merge());
        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            database.collection("companyCodes").document(currentCompanyCode).set(mark, com.google.firebase.firestore.SetOptions.merge());
    }

    private void postWorkerSystemNotificationIfNew(Map<String,Object> notice) {
        if (!"worker".equals(currentRole) || notice == null) return;
        String id = String.valueOf(notice.get("id") == null ? "" : notice.get("id"));
        if (id.length() == 0 || isNoticeDeleted(id)) return;
        try {
            android.content.SharedPreferences prefs = getSharedPreferences("mb_worker_notice_state", MODE_PRIVATE);
            if (id.equals(prefs.getString("last_system_notice_id", ""))) return;
            String title = currentCompanyName == null || currentCompanyName.trim().isEmpty() ? "MB ડાયમંડ ડાયરી" : currentCompanyName;
            String body = String.valueOf(notice.get("text") == null ? "નવી સૂચના આવી છે" : notice.get("text"));
            android.app.NotificationManager manager = (android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);
            String channelId = "mbdd_company_notices";
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                android.app.NotificationChannel channel = new android.app.NotificationChannel(channelId, "કંપની સૂચનાઓ", android.app.NotificationManager.IMPORTANCE_HIGH);
                manager.createNotificationChannel(channel);
            }
            Intent open = new Intent(this, MainActivity.class);
            open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            open.putExtra("open_notifications", true);
            android.app.PendingIntent pending = android.app.PendingIntent.getActivity(this, 323, open, android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_IMMUTABLE);
            android.app.Notification.Builder builder = android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O ? new android.app.Notification.Builder(this, channelId) : new android.app.Notification.Builder(this);
            builder.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body).setStyle(new android.app.Notification.BigTextStyle().bigText(body)).setAutoCancel(true).setContentIntent(pending).setPriority(android.app.Notification.PRIORITY_HIGH);
            manager.notify((int)(System.currentTimeMillis() & 0x7fffffff), builder.build());
            prefs.edit().putString("last_system_notice_id", id).apply();
        } catch (Exception ignored) {}
    }

"""
if anchor not in s: raise SystemExit("upsert anchor not found")
s=s.replace(anchor,helpers+anchor)

s=s.replace('        if (id.length() == 0) return;
        for (int i=0; i<currentNotifications.size(); i++) {', '        if (id.length() == 0 || isNoticeDeleted(id)) return;
        for (int i=0; i<currentNotifications.size(); i++) {',1)
s=s.replace('for (DocumentSnapshot d : snap.getDocuments()) upsertSharedNotification(sharedNoticeFromDocument(d));', 'for (DocumentSnapshot d : snap.getDocuments()) { Map<String,Object> n=sharedNoticeFromDocument(d); String id=String.valueOf(n.get("id") == null ? "" : n.get("id")); if(!isNoticeDeleted(id)) upsertSharedNotification(n); }')

s=s.replace("""                    Object raw = doc.get("latestNotice");
                    if (raw instanceof Map) {
                        Map<String,Object> n = new HashMap<>((Map<String,Object>)raw);
                        upsertSharedNotification(n);
                        currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                        pushNotifications();
                    }
""","""                    absorbDeletedNoticeIds(doc.get("deletedNoticeIds"));
                    Object raw = doc.get("latestNotice");
                    if (raw instanceof Map) {
                        Map<String,Object> n = new HashMap<>((Map<String,Object>)raw);
                        String noticeId = String.valueOf(n.get("id") == null ? "" : n.get("id"));
                        if (!isNoticeDeleted(noticeId)) {
                            upsertSharedNotification(n);
                            currentNotifications.sort((a,b) -> Long.compare(noticeMillis(b), noticeMillis(a)));
                            pushNotifications();
                            postWorkerSystemNotificationIfNew(n);
                        }
                    }
""")

s=s.replace("""                    n.put("id", d.getId());
                    if (d.getTimestamp("createdAt") != null) n.put("createdAtMillis", d.getTimestamp("createdAt").toDate().getTime());
                    currentNotifications.add(n);
""","""                    n.put("id", d.getId());
                    if (isNoticeDeleted(d.getId())) continue;
                    if (d.getTimestamp("createdAt") != null) n.put("createdAtMillis", d.getTimestamp("createdAt").toDate().getTime());
                    currentNotifications.add(n);
""")

old_end="""                mirrorCurrentBossNoticesToCompanyCode();
                pushNotifications();
            });
    }
"""
new_end="""                mirrorCurrentBossNoticesToCompanyCode();
                pushNotifications();
            });
        notificationCompanyListener = database.collection("companies").document(companyId)
            .addSnapshotListener((doc,error) -> { if (error == null && doc != null && doc.exists()) absorbDeletedNoticeIds(doc.get("deletedNoticeIds")); });
        if (currentCompanyCode != null && currentCompanyCode.length() > 0) {
            notificationCodeListener = database.collection("companyCodes").document(currentCompanyCode)
                .addSnapshotListener((doc,error) -> { if (error == null && doc != null && doc.exists()) absorbDeletedNoticeIds(doc.get("deletedNoticeIds")); });
        }
    }
"""
pos=s.find(old_end, s.find("private void watchNotifications"))
if pos<0: raise SystemExit("watchNotifications tail not found")
s=s[:pos]+new_end+s[pos+len(old_end):]

start=s.find("    private void deleteNotificationFromWeb(String id) {")
end=s.find("    private String monthKeyForEntryDate",start)
if start<0 or end<0: raise SystemExit("deleteNotificationFromWeb boundaries not found")
new_delete="""    private void deleteNotificationFromWeb(String id) {
        FirebaseUser user = auth.getCurrentUser();
        if (user == null || !"boss".equals(currentRole) || id == null || !id.matches("[A-Za-z0-9_-]{1,128}")) return;

        rememberDeletedNotice(id);
        markNoticeDeletedForCompany(id);
        updateBossLatestNotification();
        mirrorCurrentBossNoticesToCompanyCode();
        pushNotifications();
        page.evaluateJavascript("window.mbNoticeDeleted && window.mbNoticeDeleted(true,'સૂચના ડિલીટ થઈ ગઈ')", null);

        database.collection("notifications").document(id).delete();
        if (currentCompanyCode != null && currentCompanyCode.length() > 0)
            database.collection("companyCodes").document(currentCompanyCode).collection("notices").document(id).delete();
        if (currentCompanyId != null && currentCompanyId.length() > 0)
            database.collection("companies").document(currentCompanyId).collection("notices").document(id).delete();

        final String companyId = currentCompanyId == null ? "" : currentCompanyId;
        final String companyCode = currentCompanyCode == null ? "" : currentCompanyCode;
        if (companyId.length() > 0) {
            database.collection("workers").whereEqualTo("companyId", companyId).get().addOnSuccessListener(snap -> {
                for (DocumentSnapshot worker : snap.getDocuments()) {
                    Object raw = worker.get("latestNotice");
                    if (raw instanceof Map) {
                        String latestId = String.valueOf(((Map<?,?>)raw).get("id") == null ? "" : ((Map<?,?>)raw).get("id"));
                        if (id.equals(latestId)) database.collection("workers").document(worker.getId()).update("latestNotice", com.google.firebase.firestore.FieldValue.delete());
                    }
                    database.collection("users").document(worker.getId()).set(java.util.Collections.singletonMap("deletedNoticeIds", com.google.firebase.firestore.FieldValue.arrayUnion(id)), com.google.firebase.firestore.SetOptions.merge());
                    database.collection("workers").document(worker.getId()).set(java.util.Collections.singletonMap("deletedNoticeIds", com.google.firebase.firestore.FieldValue.arrayUnion(id)), com.google.firebase.firestore.SetOptions.merge());
                    database.collection("companies").document(companyId).collection("members").document(worker.getId()).set(java.util.Collections.singletonMap("deletedNoticeIds", com.google.firebase.firestore.FieldValue.arrayUnion(id)), com.google.firebase.firestore.SetOptions.merge());
                    if (companyCode.length() > 0) database.collection("companyCodes").document(companyCode).collection("members").document(worker.getId()).set(java.util.Collections.singletonMap("deletedNoticeIds", com.google.firebase.firestore.FieldValue.arrayUnion(id)), com.google.firebase.firestore.SetOptions.merge());
                }
            });
        }
    }

"""
s=s[:start]+new_delete+s[end:]
java.write_text(s)

print("v3.2.23 fixes applied")
