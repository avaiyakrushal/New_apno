# Apno Android

Apno is an original social app prototype with its own A logo and teal and gold welcome screen.

## What works
- Explore local preview without sign in
- Write, edit captions, and delete up to 50 text, photo, or video posts stored on this device
- Search local post captions, like, save, and share posts; add and remove up to 50 local comments per post
- Create, open, and delete room previews on this device
- Navigate Party, Game, Discover, Messages, and Me tabs. Party has Hot, Event, Date, Music, and Game filters for locally created rooms; Discover lists those same local rooms.
- Set a local profile name and bio, choose a gallery photo, see local post count, and receive a local preview ID

Google, Facebook, and phone sign in are placeholders. Games and online messaging are not connected. Rooms do not transmit audio or connect people. Do not distribute this preview as a functioning social network.

## Build on GitHub without a computer
The repository includes `.github/workflows/android.yml`. On a push or manual workflow run, GitHub Actions builds a debug APK and stores it in the `apno-debug-apk` artifact. The GitHub mobile app is for viewing the repository; APK artifacts may require opening GitHub in a mobile browser. An Actions run is needed to confirm this build succeeds.

Android Gradle Plugin 8.11.0, Gradle 8.13, JDK 17, compile SDK 34, minimum Android 6.0. No service credentials or private keys are included.

Photo and video posts can be selected from the Android document picker and kept locally on this device. Videos open in an installed video player. Existing plain-text posts remain readable. Shared media availability depends on the selected receiving app.
