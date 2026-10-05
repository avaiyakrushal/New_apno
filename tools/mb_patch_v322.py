from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
p=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
s=p.read_text()

# v3.2.2: worker joins directly and remains signed in. Only an explicit boss removal
# may sign the worker out. A transient/missing snapshot must not bounce the worker
# back to the company-code login screen.
s=s.replace('''                } else if (Boolean.TRUE.equals(snapshot.getBoolean("active"))) {''','''                } else if (Boolean.TRUE.equals(snapshot.getBoolean("active"))) {''',1)

# Persist the company/mode immediately after successful direct join so auth/profile
# refreshes can restore the same worker dashboard instead of showing join again.
needle='''                            currentCompanyName = companyName;
                            currentCompanyId = companyId;
                            currentMode = joinMode;
                            grantRole(user, "worker", joinMode);'''
replacement='''                            currentCompanyName = companyName;
                            currentCompanyId = companyId;
                            currentMode = joinMode;
                            getPreferences(MODE_PRIVATE).edit()
                                    .putString("worker_company_id", companyId)
                                    .putString("worker_company_name", companyName)
                                    .putString("worker_mode", joinMode)
                                    .putBoolean("worker_joined", true)
                                    .apply();
                            grantRole(user, "worker", joinMode);'''
if needle not in s: raise SystemExit('direct join success block not found')
s=s.replace(needle,replacement,1)

# Explicit removal clears persisted membership before sign-out.
needle='''                if (removed) {
                    signOut();
                    return;'''
replacement='''                if (removed) {
                    getPreferences(MODE_PRIVATE).edit()
                            .remove("worker_company_id")
                            .remove("worker_company_name")
                            .remove("worker_mode")
                            .putBoolean("worker_joined", false)
                            .apply();
                    signOut();
                    return;'''
if needle not in s: raise SystemExit('removed worker logout block not found')
s=s.replace(needle,replacement,1)

p.write_text(s)
b=root/'app/build.gradle'
t=b.read_text()
t=re.sub(r'versionCode\s+\d+','versionCode 59',t,1)
t=re.sub(r"versionName\s+'[^']+'","versionName '3.2.2'",t,1)
b.write_text(t)
print('MB Diamond Diary v3.2.2 persistent worker membership patch applied')
