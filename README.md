# Apno Android prototype (version 0.3)

This source project has a white five-tab home screen modeled on the supplied layout references. Party offers local posts and room previews. Discover lists those local rooms. Game has a working single-player dice roll; other game cards are explicit placeholders. Messages awaits account and online chat integration. Profile has editable name, bio and gallery photo, a local party room list, and working bottom navigation.

Google, Facebook and mobile sign-in remain unconnected. Rooms do not send audio. This is not yet an online social app. Existing locally saved posts and profile settings use the same preferences as version 0.1.

Older APKs do not contain these changes. Build this source with the GitHub Actions workflow in `.github/workflows/android.yml` to obtain a new APK. A successful workflow run and an on-device check are still required.
