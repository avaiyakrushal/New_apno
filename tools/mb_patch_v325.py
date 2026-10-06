from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
html=root/'app/src/main/assets/app.html'
j=java.read_text()
h=html.read_text()

# Worker WebView decimal keyboard: do not use a restrictive pattern, because some Android
# keyboards interpret the pattern as digits-only and hide the decimal separator.
h=re.sub(r'(<div id="diamondRateGrid"[\s\S]*?</div>)',
         lambda m: re.sub(r' inputmode="decimal" pattern="\[0-9\]\*\[\.,\]\?\[0-9\]\*"', ' inputmode="decimal"', m.group(1)),
         h, count=1)
h=h.replace('<input id="hourRateInput" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" value="100">',
            '<input id="hourRateInput" type="text" inputmode="decimal" value="100">',1)
h=h.replace('<input id="hourValue" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" placeholder="જેમ કે 7.5">',
            '<input id="hourValue" type="text" inputmode="decimal" placeholder="જેમ કે 7.5">',1)
html.write_text(h)

# Boss worker loading: keep the realtime companyId query, but add progressively broader
# fallbacks so old worker documents (bossUid/companyCode) also appear in the list.
old=r'''    private void loadBossWorkersByCompanyCode(String companyId) {
        if (currentCompanyCode == null || currentCompanyCode.length() == 0) {
            renderBossWorkerDocuments(new ArrayList<>(), companyId);
            return;
        }
        database.collection("workers").whereEqualTo("companyCode", currentCompanyCode).get()
            .addOnSuccessListener(snap -> renderBossWorkerDocuments(new ArrayList<>(snap.getDocuments()), companyId))
            .addOnFailureListener(e -> renderBossWorkerDocuments(new ArrayList<>(), companyId));
    }
'''
new=r'''    private void loadAllWorkersFallback(String companyId) {
        database.collection("workers").get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> matches = new ArrayList<>();
                for (DocumentSnapshot worker : snap.getDocuments()) {
                    String workerCompanyId = safe(worker.getString("companyId"));
                    String workerBossUid = safe(worker.getString("bossUid"));
                    String workerCode = safe(worker.getString("companyCode"));
                    boolean sameCompany = companyId.equals(workerCompanyId) || companyId.equals(workerBossUid);
                    if (!sameCompany && currentCompanyCode != null && currentCompanyCode.length() > 0)
                        sameCompany = currentCompanyCode.equalsIgnoreCase(workerCode);
                    if (sameCompany) matches.add(worker);
                }
                renderBossWorkerDocuments(matches, companyId);
            })
            .addOnFailureListener(e -> renderBossWorkerDocuments(new ArrayList<>(), companyId));
    }

    private void loadBossWorkersByCompanyCode(String companyId) {
        if (currentCompanyCode == null || currentCompanyCode.length() == 0) {
            loadAllWorkersFallback(companyId);
            return;
        }
        database.collection("workers").whereEqualTo("companyCode", currentCompanyCode).get()
            .addOnSuccessListener(snap -> {
                List<DocumentSnapshot> docs = new ArrayList<>(snap.getDocuments());
                if (!docs.isEmpty()) renderBossWorkerDocuments(docs, companyId);
                else loadAllWorkersFallback(companyId);
            })
            .addOnFailureListener(e -> loadAllWorkersFallback(companyId));
    }
'''
if old not in j: raise SystemExit('loadBossWorkersByCompanyCode block not found')
j=j.replace(old,new,1)

# Selected department button must itself stay red; the other button must stay white.
marker='''    private void renderBossDepartment(LinearLayout target, String mode, List<DocumentSnapshot> workers, Map<String,Map<String,Object>> live, String month) {'''
helper=r'''    private void styleBossDepartmentButtons(Button diamondFilter, Button hourFilter, boolean diamondSelected) {
        Button selected = diamondSelected ? diamondFilter : hourFilter;
        Button other = diamondSelected ? hourFilter : diamondFilter;
        selected.setTextColor(0xffffffff);
        selected.setBackgroundTintList(ColorStateList.valueOf(0xffa80d32));
        other.setTextColor(0xff9b1e3b);
        other.setBackgroundTintList(ColorStateList.valueOf(0xffffffff));
        selected.setEnabled(true);
        other.setEnabled(true);
    }

'''
if marker not in j: raise SystemExit('renderBossDepartment marker not found')
j=j.replace(marker,helper+marker,1)

old=r'''        Runnable showDiamond = () -> {
            diamondFilter.setEnabled(false); hourFilter.setEnabled(true);
            renderBossDepartment(filteredList, "diamond", diamondWorkers, live, month);
        };
        Runnable showHours = () -> {
            hourFilter.setEnabled(false); diamondFilter.setEnabled(true);
            renderBossDepartment(filteredList, "hour", hourWorkers, live, month);
        };'''
new=r'''        Runnable showDiamond = () -> {
            styleBossDepartmentButtons(diamondFilter, hourFilter, true);
            renderBossDepartment(filteredList, "diamond", diamondWorkers, live, month);
        };
        Runnable showHours = () -> {
            styleBossDepartmentButtons(diamondFilter, hourFilter, false);
            renderBossDepartment(filteredList, "hour", hourWorkers, live, month);
        };'''
if old not in j: raise SystemExit('department button runnable block not found')
j=j.replace(old,new,1)

# Do not lose legacy workers from both lists. New workers already have hour/diamond mode;
# older records are placed by their monthly data, with diamond as the final safe fallback.
old=r'''            String mode = safe(worker.getString("mode"));
            if ("hour".equals(mode)) hourWorkers.add(worker);
            else if ("diamond".equals(mode)) diamondWorkers.add(worker);
            else legacyWorkers.add(worker);
'''
new=r'''            String mode = safe(worker.getString("mode"));
            if ("hour".equals(mode)) hourWorkers.add(worker);
            else if ("diamond".equals(mode)) diamondWorkers.add(worker);
            else {
                Map<String,Object> legacySummary = bossMonthSummary(worker, live, month);
                if (mapNumber(legacySummary, "hours") > 0d) hourWorkers.add(worker);
                else diamondWorkers.add(worker);
                legacyWorkers.add(worker);
            }
'''
if old not in j: raise SystemExit('worker mode classification block not found')
j=j.replace(old,new,1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
b=re.sub(r'versionCode\s+\d+', 'versionCode 62', b, count=1)
b=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.4'", b, count=1)
build.write_text(b)
print('v3.2.4 boss full worker lists, selected department color, and worker decimal keyboard patch applied')
