# MB Diamond Diary v3.2.2 — FINAL scope

Implementation/build must preserve the already-finalized report screens, report calculations, report layout and PDF design.

1. Login role page: Sheth / Office-Kalak / Hira-Karigar.
2. Sheth Hira dashboard: Hira workers only; real saved-entry totals (pieces and amount) plus worker-wise name, mobile, birthday and totals. No zero placeholders when real data exists.
3. Sheth Office/Kalak dashboard: Office/Kalak workers only; real saved-entry totals (hours and amount) plus worker-wise name, mobile, birthday and totals. Never mix with Hira.
4. Direct company join: valid Sheth/company code joins immediately. Remove request/accept approval flow.
5. Sheth remove: Remove available in both worker sections. Removed worker is disconnected and forced to sign out to login; must re-login/rejoin to regain access.
6. Super Admin: only maniyajitesh56@gmail.com. Show only total Companies, total Workers/persons, total Users. Do not show Hira/Kalak breakdown, reports or worker personal details.

Existing decimal rate behavior remains required for both Hira A-G rates and Kalak rate using the mobile decimal keyboard (examples 30.15 and 101.15).

Build gate: do not call APK final until all six items are implemented/verified and Firebase-compatible signing/login verification passes.
