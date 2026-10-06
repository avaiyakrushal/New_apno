from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'mbbuild')
java=root/'app/src/main/java/com/example/diamonddiary/MainActivity.java'
j=java.read_text()

# Add legacy Google Sign-In fallback imports. Credential Manager can fail on some Android/OEM builds.
anchor='''import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;
import com.google.firebase.auth.FirebaseAuth;'''
rep='''import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;
import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.firebase.auth.FirebaseAuth;'''
if anchor not in j: raise SystemExit('google import anchor not found')
j=j.replace(anchor,rep,1)

anchor='''    private static final int FILE_CHOOSE = 93;

    private FirebaseAuth auth;'''
rep='''    private static final int FILE_CHOOSE = 93;
    private static final int GOOGLE_SIGN_IN = 94;

    private FirebaseAuth auth;'''
if anchor not in j: raise SystemExit('request code anchor not found')
j=j.replace(anchor,rep,1)

old=r'''    private void signIn() {
        if (signingIn) return;
        signingIn = true;
        setLoginButtonsEnabled(false);
        loginStatus.setText("Google લોગીન ખૂલી રહ્યું છે…");
        GetGoogleIdOption option = new GetGoogleIdOption.Builder()
            .setFilterByAuthorizedAccounts(false)
            .setServerClientId(getString(R.string.default_web_client_id))
            .build();
        GetCredentialRequest request = new GetCredentialRequest.Builder()
            .addCredentialOption(option).build();
        credentials.getCredentialAsync(this, request, new CancellationSignal(),
            Executors.newSingleThreadExecutor(), new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                @Override public void onResult(GetCredentialResponse response) {
                    Credential credential = response.getCredential();
                    if (!(credential instanceof CustomCredential) ||
                        !GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
                        runOnUiThread(() -> signInError("Google એકાઉન્ટ પસંદ થઈ શક્યું નથી"));
                        return;
                    }
                    try {
                        String token = GoogleIdTokenCredential.createFrom(credential.getData()).getIdToken();
                        runOnUiThread(() -> auth.signInWithCredential(GoogleAuthProvider.getCredential(token, null))
                            .addOnCompleteListener(MainActivity.this, task -> {
                                signingIn = false;
                                setLoginButtonsEnabled(true);
                                if (task.isSuccessful()) applyPendingRoleAfterLogin();
                                else signInError("લોગીન નિષ્ફળ ગયું. ફરી પ્રયાસ કરો.");
                            }));
                    } catch (Exception e) {
                        runOnUiThread(() -> signInError("Google લોગીન પૂર્ણ થઈ શક્યું નથી"));
                    }
                }
                @Override public void onError(GetCredentialException e) {
                    runOnUiThread(() -> signInError("લોગીન રદ થયું અથવા Google એકાઉન્ટ મળ્યું નથી"));
                }
            });
    }
'''
new=r'''    private void firebaseSignInWithGoogleToken(String token) {
        if (token == null || token.trim().length() == 0) {
            signInError("Google token મળ્યો નથી. ફરી પ્રયાસ કરો.");
            return;
        }
        auth.signInWithCredential(GoogleAuthProvider.getCredential(token, null))
            .addOnCompleteListener(MainActivity.this, task -> {
                signingIn = false;
                setLoginButtonsEnabled(true);
                if (task.isSuccessful()) applyPendingRoleAfterLogin();
                else signInError("Google લોગીન નિષ્ફળ ગયું. ફરી પ્રયાસ કરો.");
            });
    }

    private void startLegacyGoogleSignIn() {
        try {
            loginStatus.setText("Google એકાઉન્ટ પસંદ કરો…");
            GoogleSignInOptions options = new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                .requestIdToken(getString(R.string.default_web_client_id))
                .requestEmail()
                .build();
            GoogleSignInClient client = GoogleSignIn.getClient(this, options);
            startActivityForResult(client.getSignInIntent(), GOOGLE_SIGN_IN);
        } catch (Exception e) {
            signInError("Google લોગીન ખૂલી શક્યું નથી. ફરી પ્રયાસ કરો.");
        }
    }

    private void signIn() {
        if (signingIn) return;

        // Re-use a valid Firebase session. Role buttons must not force a new Google chooser
        // every time an already signed-in worker switches into hour/diamond mode.
        if (auth.getCurrentUser() != null) {
            setLoginButtonsEnabled(true);
            applyPendingRoleAfterLogin();
            return;
        }

        signingIn = true;
        setLoginButtonsEnabled(false);
        loginStatus.setText("Google લોગીન ખૂલી રહ્યું છે…");
        GetGoogleIdOption option = new GetGoogleIdOption.Builder()
            .setFilterByAuthorizedAccounts(false)
            .setServerClientId(getString(R.string.default_web_client_id))
            .build();
        GetCredentialRequest request = new GetCredentialRequest.Builder()
            .addCredentialOption(option).build();
        credentials.getCredentialAsync(this, request, new CancellationSignal(),
            Executors.newSingleThreadExecutor(), new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                @Override public void onResult(GetCredentialResponse response) {
                    Credential credential = response.getCredential();
                    if (!(credential instanceof CustomCredential) ||
                        !GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
                        runOnUiThread(() -> startLegacyGoogleSignIn());
                        return;
                    }
                    try {
                        String token = GoogleIdTokenCredential.createFrom(credential.getData()).getIdToken();
                        runOnUiThread(() -> firebaseSignInWithGoogleToken(token));
                    } catch (Exception e) {
                        runOnUiThread(() -> startLegacyGoogleSignIn());
                    }
                }
                @Override public void onError(GetCredentialException e) {
                    // Some devices/OEM credential providers return no credential even when a
                    // Google account is present. Fall back to the Play Services sign-in intent.
                    runOnUiThread(() -> startLegacyGoogleSignIn());
                }
            });
    }
'''
if old not in j: raise SystemExit('signIn block not found')
j=j.replace(old,new,1)

old=r'''    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == FILE_CHOOSE && chooserCallback != null) {
            Uri[] resultUris = WebChromeClient.FileChooserParams.parseResult(result, data);
            lastChosenFileUri = (resultUris != null && resultUris.length > 0) ? resultUris[0] : null;
            chooserCallback.onReceiveValue(resultUris);
            chooserCallback = null;
        }
    }
'''
new=r'''    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == GOOGLE_SIGN_IN) {
            try {
                GoogleSignInAccount account = GoogleSignIn.getSignedInAccountFromIntent(data).getResult(ApiException.class);
                String token = account == null ? null : account.getIdToken();
                firebaseSignInWithGoogleToken(token);
            } catch (ApiException e) {
                signInError("Google લોગીન થઈ શક્યું નથી (" + e.getStatusCode() + "). ફરી પ્રયાસ કરો.");
            } catch (Exception e) {
                signInError("Google લોગીન પૂર્ણ થઈ શક્યું નથી. ફરી પ્રયાસ કરો.");
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
'''
if old not in j: raise SystemExit('onActivityResult block not found')
j=j.replace(old,new,1)

java.write_text(j)

build=root/'app/build.gradle'
b=build.read_text()
dep="    implementation 'com.google.android.gms:play-services-auth:21.2.0'\n"
if dep not in b:
    b=b.replace("    implementation 'com.google.android.libraries.identity.googleid:googleid:1.1.1'\n",
                "    implementation 'com.google.android.libraries.identity.googleid:googleid:1.1.1'\n"+dep)
b=re.sub(r'versionCode\s+\d+','versionCode 67',b,count=1)
b=re.sub(r"versionName\s+'[^']+'","versionName '3.2.9'",b,count=1)
build.write_text(b)
print('v3.2.9 robust Google login fallback applied')
