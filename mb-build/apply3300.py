from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 87","versionCode 100").replace("versionName '3.2.29'","versionName '3.3.0'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

# Canonical membership marker: one Firebase Auth UID = one worker/user/member document.
old='''        membership.put("uid", user.getUid());
        membership.put("role", "worker");
        membership.put("joined", true);
'''
new='''        membership.put("uid", user.getUid());
        membership.put("authUid", user.getUid());
        membership.put("schemaVersion", "3.3");
        membership.put("role", "worker");
        membership.put("joined", true);
'''
if old not in s: raise SystemExit("membership anchor missing")
s=s.replace(old,new,1)

# Every diary item carries canonical ownership/company metadata too.
old='''                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                m.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                DocumentReference ref = database.collection("diaryEntries").document(user.getUid()).collection("items").document(id);
'''
new='''                Map<String,Object> m = entryFromJson(o); m.put("id", id);
                m.put("ownerUid", user.getUid());
                m.put("authUid", user.getUid());
                m.put("schemaVersion", "3.3");
                if (currentCompanyId != null) m.put("companyId", currentCompanyId);
                if (currentCompanyCode != null) m.put("companyCode", currentCompanyCode);
                m.put("updatedAt", com.google.firebase.firestore.FieldValue.serverTimestamp());
                DocumentReference ref = database.collection("diaryEntries").document(user.getUid()).collection("items").document(id);
'''
if old not in s: raise SystemExit("entry anchor missing")
s=s.replace(old,new,1)

# Summary mirrors also identify their canonical owner.
old='''        update.put("summaryMonth",nowMonth);
        update.put("monthDiamonds",Math.round(diamonds));
'''
new='''        update.put("uid", uid);
        update.put("authUid", uid);
        update.put("schemaVersion", "3.3");
        update.put("summaryMonth",nowMonth);
        update.put("monthDiamonds",Math.round(diamonds));
'''
if old not in s: raise SystemExit("summary anchor missing")
s=s.replace(old,new,1)

p.write_text(s)
print("v3.3.0 clean canonical UID schema applied")
