from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 100","versionCode 101").replace("versionName '3.3.0'","versionName '3.3.1'")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

# Modern login screen while keeping all role/login behavior identical.
start=s.index("    private void createLoginScreen(FrameLayout root) {")
end=s.index("    private void beginRoleLogin(", start)
new=r'''    private void createLoginScreen(FrameLayout root) {
        login = baseScreen();
        login.setGravity(Gravity.CENTER);

        TextView diamondMark = titleText("◆");
        diamondMark.setTextSize(44);
        diamondMark.setTextColor(0xffc89a4b);
        login.addView(diamondMark, fullWrap());

        TextView title = titleText("MB ડાયમંડ ડાયરી");
        title.setPadding(0, dp(4), 0, 0);
        login.addView(title, fullWrap());

        TextView subtitle = bodyText("એક જ એકાઉન્ટ · એક જ ઓળખ · લાઇવ ડાયરી");
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setTextColor(0xff7a8494);
        subtitle.setPadding(0, dp(8), 0, dp(20));
        login.addView(subtitle, fullWrap());

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(18), dp(18), dp(18));
        card.setBackground(roundedBackground(0xffffffff, 0xffe7e3e7, 22));
        card.setElevation(dp(3));

        TextView choose = sectionText("તમારી ભૂમિકા પસંદ કરો");
        choose.setGravity(Gravity.CENTER);
        choose.setPadding(0, 0, 0, dp(6));
        card.addView(choose, fullWrap());

        TextView helper = bodyText("પછી એ જ Google accountથી તમારો data પાછો મળશે");
        helper.setGravity(Gravity.CENTER);
        helper.setTextSize(13);
        helper.setTextColor(0xff7a8494);
        helper.setPadding(0, 0, 0, dp(8));
        card.addView(helper, fullWrap());

        bossLoginButton = primaryButton("શેઠ");
        bossLoginButton.setOnClickListener(v -> beginRoleLogin("boss", "both"));
        card.addView(bossLoginButton, fullWrap());

        hourLoginButton = secondaryButton("ઓફિસ · કલાકનું કામ");
        hourLoginButton.setOnClickListener(v -> beginRoleLogin("worker", "hour"));
        card.addView(hourLoginButton, fullWrap());

        diamondLoginButton = secondaryButton("હીરા · કારીગર");
        diamondLoginButton.setOnClickListener(v -> beginRoleLogin("worker", "diamond"));
        card.addView(diamondLoginButton, fullWrap());

        workerLoginButton = hourLoginButton;
        loginButton = bossLoginButton;

        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(-1, -2);
        cardLp.topMargin = dp(4);
        login.addView(card, cardLp);

        loginStatus = bodyText("");
        loginStatus.setGravity(Gravity.CENTER);
        loginStatus.setTextSize(13);
        loginStatus.setTextColor(0xff7a8494);
        loginStatus.setPadding(0, dp(16), 0, 0);
        login.addView(loginStatus, fullWrap());

        TextView version = bodyText("Clean Sync · v3.3.1");
        version.setGravity(Gravity.CENTER);
        version.setTextSize(12);
        version.setTextColor(0xff9aa2ae);
        version.setPadding(0, dp(18), 0, 0);
        login.addView(version, fullWrap());

        root.addView(login, new FrameLayout.LayoutParams(-1, -1));
    }

'''
s=s[:start]+new+s[end:]

# Modern post-login role selection, same actions.
start=s.index("    private void createRoleChoiceScreen(FrameLayout root) {")
end=s.index("    private void createWorkerProfileScreen(", start)
new=r'''    private void createRoleChoiceScreen(FrameLayout root) {
        roleChoice = baseScreen();
        roleChoice.setGravity(Gravity.CENTER);

        TextView mark = titleText("◆");
        mark.setTextSize(40);
        mark.setTextColor(0xffc89a4b);
        roleChoice.addView(mark, fullWrap());
        roleChoice.addView(titleText("MB ડાયમંડ ડાયરી"), fullWrap());

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(18), dp(18), dp(18));
        card.setBackground(roundedBackground(0xffffffff, 0xffe7e3e7, 22));
        card.setElevation(dp(3));

        TextView title = sectionText("કામનો પ્રકાર પસંદ કરો");
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(6));
        card.addView(title, fullWrap());

        TextView hint = bodyText("આ પસંદગી પછી પણ તમારા Firebase UIDમાં ફેરફાર નહીં થાય");
        hint.setGravity(Gravity.CENTER);
        hint.setTextSize(13);
        hint.setTextColor(0xff7a8494);
        hint.setPadding(0, 0, 0, dp(8));
        card.addView(hint, fullWrap());

        Button boss = primaryButton("શેઠ");
        boss.setOnClickListener(v -> saveRole("boss", "both"));
        card.addView(boss, fullWrap());

        Button office = secondaryButton("ઓફિસ · કલાકનું કામ");
        office.setOnClickListener(v -> saveRole("worker", "hour"));
        card.addView(office, fullWrap());

        Button diamond = secondaryButton("હીરા · કારીગર");
        diamond.setOnClickListener(v -> saveRole("worker", "diamond"));
        card.addView(diamond, fullWrap());

        Button logout = secondaryButton("લોગ આઉટ");
        logout.setOnClickListener(v -> signOut());
        card.addView(logout, fullWrap());

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin = dp(18);
        roleChoice.addView(card, lp);

        root.addView(roleChoice, new FrameLayout.LayoutParams(-1, -1));
        roleChoice.setVisibility(View.GONE);
    }

'''
s=s[:start]+new+s[end:]

old=r'''    private LinearLayout baseScreen() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(dp(24), dp(30), dp(24), dp(30));
        layout.setBackgroundColor(0xfff3f5f9);
        return layout;
    }
'''
new=r'''    private LinearLayout baseScreen() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(dp(22), dp(32), dp(22), dp(32));
        layout.setBackgroundColor(0xfff6f3f5);
        return layout;
    }
'''
if old not in s: raise SystemExit("baseScreen anchor missing")
s=s.replace(old,new,1)

old=r'''    private TextView titleText(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(25);
        view.setTextColor(0xff17243a);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setGravity(Gravity.CENTER);
        return view;
    }
'''
new=r'''    private TextView titleText(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(27);
        view.setTextColor(0xff17243a);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setGravity(Gravity.CENTER);
        return view;
    }
'''
if old not in s: raise SystemExit("titleText anchor missing")
s=s.replace(old,new,1)

old=r'''    private Button primaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xffffffff);
        button.setTextSize(15);
        button.setAllCaps(false);
        button.setBackgroundTintList(ColorStateList.valueOf(0xffa80d32));
        LinearLayout.LayoutParams p = fullWrap();
        p.topMargin = dp(12);
        button.setLayoutParams(p);
        return button;
    }
'''
new=r'''    private Button primaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xffffffff);
        button.setTextSize(15);
        button.setTypeface(Typeface.DEFAULT_BOLD);
        button.setAllCaps(false);
        button.setMinHeight(dp(54));
        button.setPadding(dp(14), dp(12), dp(14), dp(12));
        button.setBackground(roundedBackground(0xffb20f3b, 0xffb20f3b, 15));
        button.setElevation(dp(2));
        LinearLayout.LayoutParams p = fullWrap();
        p.topMargin = dp(12);
        button.setLayoutParams(p);
        return button;
    }
'''
if old not in s: raise SystemExit("primaryButton anchor missing")
s=s.replace(old,new,1)

old=r'''    private Button secondaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xff9b1e3b);
        button.setTextSize(15);
        button.setAllCaps(false);
        button.setBackgroundTintList(ColorStateList.valueOf(0xffffffff));
        LinearLayout.LayoutParams p = fullWrap();
        p.topMargin = dp(10);
        button.setLayoutParams(p);
        return button;
    }
'''
new=r'''    private Button secondaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xff8f1735);
        button.setTextSize(15);
        button.setTypeface(Typeface.DEFAULT_BOLD);
        button.setAllCaps(false);
        button.setMinHeight(dp(52));
        button.setPadding(dp(14), dp(12), dp(14), dp(12));
        button.setBackground(roundedBackground(0xffffffff, 0xffe5dce1, 15));
        button.setElevation(dp(1));
        LinearLayout.LayoutParams p = fullWrap();
        p.topMargin = dp(10);
        button.setLayoutParams(p);
        return button;
    }
'''
if old not in s: raise SystemExit("secondaryButton anchor missing")
s=s.replace(old,new,1)

p.write_text(s)

# Refresh WebView styling only; keep data/report logic untouched.
p=root/"app/src/main/assets/app.html"
s=p.read_text()
s=s.replace("background:#f3f5f9","background:#f6f3f5")
s=s.replace("header{background:#17243a;","header{background:linear-gradient(135deg,#17243a,#263954 72%,#8f1735);")
s=s.replace("border-radius:18px","border-radius:20px")
s=s.replace("box-shadow:0 4px 20px #14243b08","box-shadow:0 8px 26px #14243b0b")
s=s.replace("background:#a80d32;color:white","background:#b20f3b;color:white")
p.write_text(s)

print("v3.3.1 modern UI applied without changing clean UID/sync logic")
