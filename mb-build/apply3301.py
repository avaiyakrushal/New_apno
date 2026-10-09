from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "project")

p=root/"app/build.gradle"
s=p.read_text()
s=s.replace("versionCode 100","versionCode 101").replace("versionName '3.3.0'","versionName '3.3.1'")
if "com.google.android.gms:play-services-auth" not in s:
    s=s.replace("    implementation 'com.google.android.libraries.identity.googleid:googleid:1.1.1'\n",
                "    implementation 'com.google.android.libraries.identity.googleid:googleid:1.1.1'\n    implementation 'com.google.android.gms:play-services-auth:21.3.0'\n")
p.write_text(s)

p=root/"app/src/main/java/com/example/diamonddiary/MainActivity.java"
s=p.read_text()

# Imports for legacy Google Sign-In fallback.
imp="""import com.google.firebase.auth.GoogleAuthProvider;
"""
newimp="""import com.google.firebase.auth.GoogleAuthProvider;
import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.android.gms.tasks.Task;
"""
if imp not in s: raise SystemExit("auth import anchor missing")
s=s.replace(imp,newimp,1)

old="""    private FirebaseAuth auth;
    private FirebaseFirestore database;
    private CredentialManager credentials;
"""
new="""    private FirebaseAuth auth;
    private FirebaseFirestore database;
    private CredentialManager credentials;
    private GoogleSignInClient legacyGoogleSignInClient;
    private static final int RC_GOOGLE_SIGN_IN = 7401;
"""
if old not in s: raise SystemExit("auth fields anchor missing")
s=s.replace(old,new,1)

# Initialize fallback client after credential manager init.
old="""        credentials = CredentialManager.create(this);
"""
new="""        credentials = CredentialManager.create(this);
        GoogleSignInOptions legacyOptions = new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(getString(R.string.default_web_client_id))
            .requestEmail()
            .build();
        legacyGoogleSignInClient = GoogleSignIn.getClient(this, legacyOptions);
"""
if old not in s: raise SystemExit("credential init anchor missing")
s=s.replace(old,new,1)

# Replace Credential Manager signIn with fallback-aware flow.
start=s.index("    private void signIn() {")
end=s.index("    private void applyPendingRoleAfterLogin() {", start)
newblock=r'''    private void signIn() {
        if (signingIn) return;
        signingIn = true;
        setLoginButtonsEnabled(false);
        loginStatus.setText("Google લોગીન ખૂલી રહ્યું છે…");

        GetGoogleIdOption option = new GetGoogleIdOption.Builder()
            .setFilterByAuthorizedAccounts(false)
            .setServerClientId(getString(R.string.default_web_client_id))
            .build();

        GetCredentialRequest request = new GetCredentialRequest.Builder()
            .addCredentialOption(option)
            .build();

        credentials.getCredentialAsync(
            this,
            request,
            new CancellationSignal(),
            Executors.newSingleThreadExecutor(),
            new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                @Override public void onResult(GetCredentialResponse response) {
                    Credential credential = response.getCredential();
                    if (!(credential instanceof CustomCredential)
                        || !GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
                        runOnUiThread(() -> startLegacyGoogleSignIn("Credential Manager account મળ્યું નથી"));
                        return;
                    }

                    try {
                        String token = GoogleIdTokenCredential.createFrom(credential.getData()).getIdToken();
                        runOnUiThread(() -> firebaseSignInWithGoogleToken(token, "Credential Manager"));
                    } catch (Exception e) {
                        runOnUiThread(() -> startLegacyGoogleSignIn("Google token વાંચી શકાયું નથી"));
                    }
                }

                @Override public void onError(GetCredentialException e) {
                    final String reason = e == null ? "Credential Manager error" :
                        e.getClass().getSimpleName() + (e.getMessage() == null ? "" : ": " + e.getMessage());
                    runOnUiThread(() -> startLegacyGoogleSignIn(reason));
                }
            }
        );
    }

    private void startLegacyGoogleSignIn(String credentialReason) {
        if (legacyGoogleSignInClient == null) {
            signInError("Google Sign-In તૈયાર નથી. " + credentialReason);
            return;
        }
        loginStatus.setText("બીજી Google login રીતથી પ્રયાસ થઈ રહ્યો છે…");
        try {
            // Clear a stale cached account so a fresh chooser is shown.
            legacyGoogleSignInClient.signOut().addOnCompleteListener(task -> {
                try {
                    startActivityForResult(legacyGoogleSignInClient.getSignInIntent(), RC_GOOGLE_SIGN_IN);
                } catch (Exception e) {
                    signInError("Google login ખૂલી શક્યું નથી: " + e.getClass().getSimpleName());
                }
            });
        } catch (Exception e) {
            signInError("Google login fallback શરૂ થઈ શક્યું નથી: " + e.getClass().getSimpleName());
        }
    }

    private void firebaseSignInWithGoogleToken(String token, String source) {
        if (token == null || token.trim().length() == 0) {
            signInError("Google ID token મળ્યો નથી");
            return;
        }
        auth.signInWithCredential(GoogleAuthProvider.getCredential(token, null))
            .addOnCompleteListener(MainActivity.this, task -> {
                signingIn = false;
                setLoginButtonsEnabled(true);
                if (task.isSuccessful()) {
                    loginStatus.setText(source + "થી Google login સફળ");
                    applyPendingRoleAfterLogin();
                } else {
                    String detail = task.getException() == null ? "" :
                        " · " + task.getException().getClass().getSimpleName() +
                        (task.getException().getMessage() == null ? "" : ": " + task.getException().getMessage());
                    signInError("Firebase Google login નિષ્ફળ" + detail);
                }
            });
    }

'''
s=s[:start]+newblock+s[end:]

# Extend onActivityResult for legacy Google sign-in.
old="""    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == FILE_CHOOSE && chooserCallback != null) {
            Uri[] resultUris = WebChromeClient.FileChooserParams.parseResult(result, data);
            lastChosenFileUri = (resultUris != null && resultUris.length > 0) ? resultUris[0] : null;
            chooserCallback.onReceiveValue(resultUris);
            chooserCallback = null;
        }
    }
"""
new="""    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);

        if (request == RC_GOOGLE_SIGN_IN) {
            Task<GoogleSignInAccount> task = GoogleSignIn.getSignedInAccountFromIntent(data);
            try {
                GoogleSignInAccount account = task.getResult(ApiException.class);
                String token = account == null ? null : account.getIdToken();
                firebaseSignInWithGoogleToken(token, "Google Sign-In");
            } catch (ApiException e) {
                signInError("Google Sign-In error code: " + e.getStatusCode());
            } catch (Exception e) {
                signInError("Google Sign-In error: " + e.getClass().getSimpleName());
            }
            return;
        }

        if (request == FILE_CHOOSE && chooserCallback != null) {
            Uri[] resultUris = WebChromeClient.FileChooserParams.parseResult(result, data);
            lastChosenFileUri = (resultUris != null && resultUris.length > 0) ? resultUris[0] : null;
            chooserCallback.onReceiveValue(resultUris);
            chooserCallback = null;
        }
    }
"""
if old not in s: raise SystemExit("onActivityResult anchor missing")
s=s.replace(old,new,1)

p.write_text(s)
print("v3.3.1 Google login fallback + diagnostics applied")
