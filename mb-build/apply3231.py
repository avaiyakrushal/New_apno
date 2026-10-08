from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 88","versionCode 89").replace("versionName '3.2.30'","versionName '3.2.31'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

old="""    private WebView page;
    private WebView printing;
    private ValueCallback<Uri[]> chooserCallback;
"""
new="""    private WebView page;
    private WebView printing;
    private FrameLayout webLoadingOverlay;
    private TextView webLoadingStatus;
    private boolean webPageReady = false;
    private int webReloadAttempts = 0;
    private final android.os.Handler webUiHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable webLoadWatchdog = new Runnable() {
        @Override public void run() {
            FirebaseUser user = auth == null ? null : auth.getCurrentUser();
            if (user == null || page == null || page.getVisibility() != View.VISIBLE || webPageReady) return;
            String url = page.getUrl();
            boolean mainLoaded = url != null && url.startsWith("file:///android_asset/app.html");
            if (webReloadAttempts < 2) {
                webReloadAttempts++;
                showWebLoading(webReloadAttempts == 1 ? "ડાયરી તૈયાર થઈ રહી છે…" : "ફરીથી લોડ કરી રહ્યા છીએ…");
                page.stopLoading();
                if (mainLoaded) page.reload();
                else loadMainPage(user);
                webUiHandler.postDelayed(this, 4500L);
            } else {
                showWebLoading("ડેટા લોડ થઈ રહ્યો છે…");
            }
        }
    };
    private ValueCallback<Uri[]> chooserCallback;
"""
if old not in s: raise SystemExit("web fields anchor missing")
s=s.replace(old,new,1)

anchor="""    private static final SecureRandom RANDOM = new SecureRandom();

    @Override public void onCreate(Bundle state) {
"""
helpers="""    private static final SecureRandom RANDOM = new SecureRandom();

    private void createWebLoadingOverlay(FrameLayout root) {
        webLoadingOverlay = new FrameLayout(this);
        webLoadingOverlay.setBackgroundColor(0xfff4f1f3);

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(dp(28), dp(28), dp(28), dp(28));

        TextView mark = new TextView(this);
        mark.setText("◆");
        mark.setTextSize(48);
        mark.setTextColor(0xffa80d32);
        mark.setGravity(Gravity.CENTER);
        box.addView(mark, new LinearLayout.LayoutParams(-1, -2));

        TextView title = new TextView(this);
        title.setText("MB ડાયમંડ ડાયરી");
        title.setTextSize(23);
        title.setTextColor(0xff17243a);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(-1, -2);
        titleLp.topMargin = dp(8);
        box.addView(title, titleLp);

        webLoadingStatus = new TextView(this);
        webLoadingStatus.setText("ડાયરી તૈયાર થઈ રહી છે…");
        webLoadingStatus.setTextSize(14);
        webLoadingStatus.setTextColor(0xff6f7785);
        webLoadingStatus.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams statusLp = new LinearLayout.LayoutParams(-1, -2);
        statusLp.topMargin = dp(10);
        box.addView(webLoadingStatus, statusLp);

        FrameLayout.LayoutParams boxLp = new FrameLayout.LayoutParams(-1, -2);
        boxLp.gravity = Gravity.CENTER;
        webLoadingOverlay.addView(box, boxLp);
        webLoadingOverlay.setVisibility(View.GONE);
        root.addView(webLoadingOverlay, new FrameLayout.LayoutParams(-1, -1));
    }

    private void showWebLoading(String message) {
        if (webLoadingStatus != null && message != null) webLoadingStatus.setText(message);
        if (webLoadingOverlay != null) {
            webLoadingOverlay.setVisibility(View.VISIBLE);
            webLoadingOverlay.bringToFront();
        }
    }

    private void hideWebLoading() {
        webUiHandler.removeCallbacks(webLoadWatchdog);
        if (webLoadingOverlay != null) webLoadingOverlay.setVisibility(View.GONE);
    }

    private void scheduleWebLoadWatchdog() {
        webUiHandler.removeCallbacks(webLoadWatchdog);
        webUiHandler.postDelayed(webLoadWatchdog, 4500L);
    }

    private void loadMainPage(FirebaseUser user) {
        if (user == null || page == null) return;
        webPageReady = false;
        showWebLoading("ડાયરી તૈયાર થઈ રહી છે…");
        loadedUid = user.getUid();
        page.loadUrl("file:///android_asset/app.html?uid=" + Uri.encode(loadedUid));
        scheduleWebLoadWatchdog();
    }

    private boolean isMainWebPageLoaded() {
        if (page == null) return false;
        String url = page.getUrl();
        return url != null && url.startsWith("file:///android_asset/app.html");
    }

    @Override public void onCreate(Bundle state) {
"""
if anchor not in s: raise SystemExit("pre-onCreate anchor missing")
s=s.replace(anchor,helpers,1)

old="""        page = new WebView(this);
        page.getSettings().setJavaScriptEnabled(true);
"""
new="""        page = new WebView(this);
        page.setBackgroundColor(0xfff3f5f9);
        page.getSettings().setJavaScriptEnabled(true);
"""
if old not in s: raise SystemExit("page init anchor missing")
s=s.replace(old,new,1)

old="""        page.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                updateAccountLabel();
                updateRoleInPage();
                pushCloudEntries();
                pushCloudSettings();
                pushNotifications();
                pushWorkerProfileToPage();
                if (pendingBossWebScreen != null) {
                    String target = pendingBossWebScreen;
                    pendingBossWebScreen = null;
                    page.evaluateJavascript("(function(){var b=document.querySelector('[data-screen=\"" + target + "\"]');if(b)b.click();})();", null);
                }
            }
        });
"""
new="""        page.setWebViewClient(new WebViewClient() {
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                if (url != null && url.startsWith("file:///android_asset/app.html")) {
                    webPageReady = false;
                    showWebLoading("ડાયરી તૈયાર થઈ રહી છે…");
                    scheduleWebLoadWatchdog();
                }
            }

            @Override public void onPageFinished(WebView view, String url) {
                if (url != null && url.startsWith("file:///android_asset/app.html")) {
                    webPageReady = true;
                    webReloadAttempts = 0;
                    hideWebLoading();
                }
                updateAccountLabel();
                updateRoleInPage();
                pushCloudEntries();
                pushCloudSettings();
                pushNotifications();
                pushWorkerProfileToPage();
                if (pendingBossWebScreen != null) {
                    String target = pendingBossWebScreen;
                    pendingBossWebScreen = null;
                    page.evaluateJavascript("(function(){var b=document.querySelector('[data-screen=\"" + target + "\"]');if(b)b.click();})();", null);
                }
            }

            @Override public void onReceivedError(WebView view, android.webkit.WebResourceRequest request, android.webkit.WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request != null && request.isForMainFrame()) {
                    webPageReady = false;
                    showWebLoading("કનેક્શન/પેજ ફરી લોડ કરી રહ્યા છીએ…");
                    scheduleWebLoadWatchdog();
                }
            }
        });
"""
if old not in s: raise SystemExit("webviewclient block missing")
s=s.replace(old,new,1)

old="""        createPendingScreen(root);
        createAdminScreen(root);

        setContentView(root);
"""
new="""        createPendingScreen(root);
        createAdminScreen(root);
        createWebLoadingOverlay(root);

        setContentView(root);
"""
if old not in s: raise SystemExit("overlay add anchor missing")
s=s.replace(old,new,1)

old="""        if (page != null && page.getVisibility() == View.VISIBLE) {
            pushNotifications();
        }
    }
"""
new="""        if (page != null && page.getVisibility() == View.VISIBLE) {
            pushNotifications();
            FirebaseUser user = auth == null ? null : auth.getCurrentUser();
            if (user != null && (!isMainWebPageLoaded() || !webPageReady)) {
                loadMainPage(user);
            }
        }
    }
"""
if old not in s: raise SystemExit("onResume tail anchor missing")
s=s.replace(old,new,1)

old="""        hideAll();
        page.setVisibility(View.VISIBLE);
        if (!user.getUid().equals(loadedUid)) {
            loadedUid = user.getUid();
            page.loadUrl("file:///android_asset/app.html?uid=" + Uri.encode(loadedUid));
        } else {
            updateAccountLabel();
"""
new="""        hideAll();
        page.setVisibility(View.VISIBLE);
        if (!user.getUid().equals(loadedUid) || !isMainWebPageLoaded() || !webPageReady) {
            loadMainPage(user);
        } else {
            hideWebLoading();
            updateAccountLabel();
"""
if old not in s: raise SystemExit("grantRole page load anchor missing")
s=s.replace(old,new,1)

old="""    private void hideAll() {
        page.setVisibility(View.GONE);
        login.setVisibility(View.GONE);
"""
new="""    private void hideAll() {
        page.setVisibility(View.GONE);
        if (webLoadingOverlay != null) webLoadingOverlay.setVisibility(View.GONE);
        login.setVisibility(View.GONE);
"""
if old not in s: raise SystemExit("hideAll anchor missing")
s=s.replace(old,new,1)

old="""    @Override protected void onDestroy() {
        eventualSyncHandler.removeCallbacks(eventualSyncRunnable);
        eventualSyncHandler.removeCallbacksAndMessages(null);
        eventualSyncStarted = false;
"""
new="""    @Override protected void onDestroy() {
        webUiHandler.removeCallbacks(webLoadWatchdog);
        webUiHandler.removeCallbacksAndMessages(null);
        eventualSyncHandler.removeCallbacks(eventualSyncRunnable);
        eventualSyncHandler.removeCallbacksAndMessages(null);
        eventualSyncStarted = false;
"""
if old not in s: raise SystemExit("onDestroy anchor missing")
s=s.replace(old,new,1)

p.write_text(s)

# Gentle visual refresh without changing finalized report math/flows.
p=root/"app/src/main/assets/app.html"
s=p.read_text()
old=':root{font-family:system-ui,"Noto Sans Gujarati",sans-serif;color:#17243a;background:#f3f5f9}*{box-sizing:border-box}body{margin:0}header{background:#17243a;color:white;padding:20px 16px;display:flex;align-items:center;gap:12px}header b{font-size:22px}.logo{color:#ebc57e;font-size:28px}main{max-width:600px;margin:auto;padding:18px 14px 28px}.badge{font-size:12px;color:#9b1e3b;background:#fff1f3;padding:7px 10px;border-radius:20px;display:inline-block}.intro{margin:12px 0 18px;color:#536073}.panel{background:#fff;border:1px solid #e8ebf1;border-radius:18px;padding:18px;margin:12px 0;box-shadow:0 4px 20px #14243b08}h2{font-size:21px;margin:4px 0 14px}h3{font-size:17px;margin:0 0 13px}label{display:block;font-weight:650;margin:13px 0 6px}input,select{width:100%;font:inherit;padding:12px;border:1px solid #dce1e9;border-radius:11px;background:#fafbfd;color:#283346}.hint{font-size:12px;color:#718092;margin:6px 0 14px}.grid{display:grid;grid-template-columns:50px 1fr 1fr;gap:8px;align-items:center}.grid b{text-align:center}.grid input{text-align:center;min-width:0}.action{width:100%;background:#a80d32;color:white;font:bold 16px inherit;border:0;padding:15px;border-radius:13px;margin-top:16px}.actions{display:flex;gap:8px;flex-wrap:wrap}.choice{padding:10px 12px;border:1px solid #e3d8db;background:#fff;border-radius:12px;color:#9b1e3b;font-weight:650}.choice.on{background:#a80d32;color:#fff}.line{display:flex;justify-content:space-between;gap:8px;padding:9px 0;border-bottom:1px solid #edf0f4}.line:last-child{border:0}.green{color:#127654}.red{color:#a80d32}.small{font-size:13px;color:#718092}.screen{display:none}.screen.active{display:block}nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #e2e6ee;display:flex;justify-content:center;padding:6px max(8px,calc((100% - 600px)/2));box-shadow:0 -3px 20px #16243b12}nav button{flex:1;padding:8px 0;color:#687487;background:none;border:0;font-weight:700;font-size:13px}nav button.on{color:#a80d32}.report,.diamond-view{display:none}.report.active,.diamond-view.active{display:block}.note{background:#fff9e9;color:#73591f;border-radius:12px;padding:12px;font-size:13px}'
new=':root{font-family:system-ui,"Noto Sans Gujarati",sans-serif;color:#17243a;background:#f4f1f3}*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#f6f2f4 0,#f3f5f9 220px,#f3f5f9 100%);min-height:100vh}header{background:linear-gradient(135deg,#17243a 0%,#263954 58%,#8f1735 145%);color:white;padding:21px 16px 19px;display:flex;align-items:center;gap:12px;box-shadow:0 8px 28px #17243a22}header b{font-size:22px;letter-spacing:.2px}.logo{color:#f0cf8b;font-size:30px;text-shadow:0 2px 10px #0003}main{max-width:600px;margin:auto;padding:18px 14px 92px}.badge{font-size:12px;color:#8f1735;background:#fff3f6;border:1px solid #f1dfe5;padding:7px 11px;border-radius:20px;display:inline-block;font-weight:800}.intro{margin:12px 0 18px;color:#536073}.panel{background:#fff;border:1px solid #e7e4e8;border-radius:20px;padding:18px;margin:12px 0;box-shadow:0 8px 26px #14243b0b}h2{font-size:21px;margin:4px 0 14px;color:#17243a}h3{font-size:17px;margin:0 0 13px;color:#263954}label{display:block;font-weight:700;margin:13px 0 6px}input,select{width:100%;font:inherit;padding:12px;border:1px solid #d9dde5;border-radius:12px;background:#fbfcfd;color:#283346;outline:none;transition:.16s border,.16s box-shadow}input:focus,select:focus{border-color:#a80d32;box-shadow:0 0 0 3px #a80d3214}.hint{font-size:12px;color:#718092;margin:6px 0 14px}.grid{display:grid;grid-template-columns:50px 1fr 1fr;gap:8px;align-items:center}.grid b{text-align:center}.grid input{text-align:center;min-width:0}.action{width:100%;background:linear-gradient(135deg,#8f1735,#b51d47);color:white;font:bold 16px inherit;border:0;padding:15px;border-radius:14px;margin-top:16px;box-shadow:0 8px 18px #8f173526}.action:active{transform:translateY(1px)}.actions{display:flex;gap:8px;flex-wrap:wrap}.choice{padding:10px 12px;border:1px solid #e2d8dd;background:#fff;border-radius:13px;color:#8f1735;font-weight:700;box-shadow:0 2px 8px #14243b07}.choice.on{background:linear-gradient(135deg,#8f1735,#b51d47);color:#fff;border-color:transparent}.line{display:flex;justify-content:space-between;gap:8px;padding:10px 0;border-bottom:1px solid #edf0f4}.line:last-child{border:0}.green{color:#127654}.red{color:#a80d32}.small{font-size:13px;color:#718092}.screen{display:none}.screen.active{display:block;animation:mbFade .14s ease-out}@keyframes mbFade{from{opacity:.35;transform:translateY(3px)}to{opacity:1;transform:none}}nav{position:fixed;bottom:0;left:0;right:0;background:#fffffff2;backdrop-filter:blur(12px);border-top:1px solid #e2e6ee;display:flex;justify-content:center;padding:7px max(8px,calc((100% - 600px)/2)) calc(7px + env(safe-area-inset-bottom));box-shadow:0 -8px 24px #16243b12;z-index:40}nav button{flex:1;padding:9px 0;color:#687487;background:none;border:0;font-weight:750;font-size:13px;border-radius:12px}nav button.on{color:#8f1735;background:#fff1f5}.report,.diamond-view{display:none}.report.active,.diamond-view.active{display:block}.note{background:#fff9e9;color:#73591f;border:1px solid #f3e5ba;border-radius:14px;padding:12px;font-size:13px}'
if old not in s: raise SystemExit("base css anchor missing")
s=s.replace(old,new,1)
p.write_text(s)

print("v3.2.31 white-screen recovery + UI polish applied")
