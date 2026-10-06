from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

needle='''        Map<String,Object> n = new HashMap<>();
        n.put("companyId", currentCompanyId);'''
rep='''        final String sharedText = clean;
        final String sharedImage = image;
        Map<String,Object> n = new HashMap<>();
        n.put("companyId", currentCompanyId);'''
if needle not in j:
    raise SystemExit('notification final-copy anchor not found')
j=j.replace(needle,rep,1)

needle='''                shared.put("text", clean);
                shared.put("imageBase64", image);'''
rep='''                shared.put("text", sharedText);
                shared.put("imageBase64", sharedImage);'''
if needle not in j:
    raise SystemExit('notification lambda text/image anchor not found')
j=j.replace(needle,rep,1)

java.write_text(j)
print('v3.2.7 notification lambda compile fix applied')
