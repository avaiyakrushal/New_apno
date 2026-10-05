from pathlib import Path
import re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
p=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
s=p.read_text()
# Boss dashboard: keep Hira and Office/Kalak workers strictly separate using two filter buttons.
old='''        if (!hourWorkers.isEmpty()) {
            TextView heading = sectionText("ઓફિસ / કલાક · " + hourWorkers.size());
            heading.setGravity(Gravity.START); bossWorkers.addView(heading, fullWrap());
            for (DocumentSnapshot worker : hourWorkers) addWorkerRow(worker, bossMonthSummary(worker, live, month));
        }
        if (!diamondWorkers.isEmpty()) {
            TextView heading = sectionText("હીરા કારીગરો · " + diamondWorkers.size());
            heading.setGravity(Gravity.START); bossWorkers.addView(heading, fullWrap());
            for (DocumentSnapshot worker : diamondWorkers) addWorkerRow(worker, bossMonthSummary(worker, live, month));
        }'''
new='''        LinearLayout filters = new LinearLayout(this);
        filters.setOrientation(LinearLayout.HORIZONTAL);
        Button diamondFilter = secondaryButton("હીરા કારીગર · " + diamondWorkers.size());
        Button hourFilter = secondaryButton("ઓફિસ / કલાક · " + hourWorkers.size());
        filters.addView(diamondFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        filters.addView(hourFilter, new LinearLayout.LayoutParams(0, -2, 1f));
        bossWorkers.addView(filters, fullWrap());
        LinearLayout filteredList = new LinearLayout(this);
        filteredList.setOrientation(LinearLayout.VERTICAL);
        bossWorkers.addView(filteredList, fullWrap());
        Runnable showDiamond = () -> {
            filteredList.removeAllViews();
            TextView heading = sectionText("હીરા કારીગરો · " + diamondWorkers.size());
            heading.setGravity(Gravity.START); filteredList.addView(heading, fullWrap());
            for (DocumentSnapshot worker : diamondWorkers) addWorkerRowTo(filteredList, worker, bossMonthSummary(worker, live, month));
        };
        Runnable showHours = () -> {
            filteredList.removeAllViews();
            TextView heading = sectionText("ઓફિસ / કલાક · " + hourWorkers.size());
            heading.setGravity(Gravity.START); filteredList.addView(heading, fullWrap());
            for (DocumentSnapshot worker : hourWorkers) addWorkerRowTo(filteredList, worker, bossMonthSummary(worker, live, month));
        };
        diamondFilter.setOnClickListener(v -> showDiamond.run());
        hourFilter.setOnClickListener(v -> showHours.run());
        showDiamond.run();'''
if old not in s: raise SystemExit('worker sections block not found')
s=s.replace(old,new,1)
# Allow worker cards to render into selected filtered container.
needle='''    private void addWorkerRow(DocumentSnapshot worker, Map<String,Object> overrideMonthData) {'''
rep='''    private void addWorkerRow(DocumentSnapshot worker, Map<String,Object> overrideMonthData) { addWorkerRowTo(bossWorkers, worker, overrideMonthData); }\n\n    private void addWorkerRowTo(LinearLayout target, DocumentSnapshot worker, Map<String,Object> overrideMonthData) {'''
if needle not in s: raise SystemExit('worker row method not found')
s=s.replace(needle,rep,1)
# Change only the card attachment inside the worker-row method.
start=s.index('    private void addWorkerRowTo(')
end=s.find('\n    private ',start+10)
chunk=s[start:end if end!=-1 else len(s)]
if 'bossWorkers.addView(card' not in chunk: raise SystemExit('worker card attachment not found')
chunk=chunk.replace('bossWorkers.addView(card', 'target.addView(card',1)
s=s[:start]+chunk+s[end if end!=-1 else len(s):]
p.write_text(s)
b=root/'app/build.gradle'; t=b.read_text(); t=re.sub(r'versionCode\s+\d+','versionCode 57',t,1); t=re.sub(r"versionName\s+'[^']+'","versionName '3.2.0'",t,1); b.write_text(t)
print('v3.2.0 separated boss Hira/Office worker views applied')
