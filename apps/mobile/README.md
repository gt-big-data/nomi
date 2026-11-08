# apps/mobile

The Nomi consumer app: Expo (React Native, TypeScript), opening straight to the camera.

Created in NOMI-011. Planned layout:

```
src/
  app/           expo-router screens: scanner, result, compare, onboarding, profiles, search
  components/    Shared UI components built from the Figma library (NOMI-027)
  lib/           Barcode parser (NOMI-007), database access (NOMI-040)
  scoring/       On-device scoring engine: term-table lookups and sums (NOMI-060)
  storage/       Encrypted on-device profile storage (NOMI-039)
assets/
  nomi.sqlite    Bundled dataset (generated, not committed)
```

Rules for this app:

- No health data leaves the device (ADR-0002). Profiles, conditions and scan history are stored
  encrypted locally, and no analytics or crash-reporting SDK may receive them.
- No modeling logic in the app. The scoring engine only looks up and adds values the pipeline exported.
- Barcodes are read on the device with Google ML Kit, so scanning works offline (NOMI-011).
- Uses a development build (camera and ML Kit libraries don't run in Expo Go).

## Barcode scanning

**Library:** [react-native-vision-camera](https://github.com/mrousavy/react-native-vision-camera) with
`react-native-vision-camera-barcode-scanner`. We chose it because it uses Google ML Kit on both iOS and Android, so
scanning runs on-device and works offline. `expo-camera` uses Apple's scanner on iOS instead of ML Kit.

## Build and run

### iPhone (needs a Mac with Xcode)

1. Install the latest Xcode.
2. In Xcode, open Settings → Accounts, sign in with your Apple ID (a free one works), click "Manage Certificates",
   then click + → "Apple Development".
3. On the iPhone, turn on Settings → Privacy & Security → Developer Mode.
4. Plug in and unlock the iPhone. Run `pnpm install` from the repo root, then from `apps/mobile` run:

   ```bash
   npx expo run:ios --device
   ```

5. On the iPhone, open Settings → General → VPN & Device Management and trust your Apple ID.

With a free Apple ID, the app expires after 7 days. Run step 4 again to reinstall it.

Free Apple IDs can't share a bundle identifier. If Xcode says `org.gtbigdata.nomi` is unavailable, pick
your own and pass it in step 4, for example `NOMI_IOS_BUNDLE_ID=com.yourname.nomi npx expo run:ios --device`.
Don't commit it.

### Android

1. Install [Android Studio](https://developer.android.com/studio) and let it install the Android SDK.
2. On the phone, turn on Developer options (tap Settings → About phone → Build number seven times), then
   turn on USB debugging.
3. Plug in the phone and accept the debugging prompt. Run `pnpm install` from the repo root, then from
   `apps/mobile` run:

   ```bash
   npx expo run:android --device
   ```

### Checks

From the repo root, `pnpm typecheck` type-checks the app and `pnpm test` runs the barcode parser tests
(NOMI-007). CI runs both.

## Design

- **Figma library:** [Nomi Library](https://www.figma.com/design/wNvJ7Nwq6MEIUqKeHWHEd9) has the light and dark
  color tokens (including score tier colors), the type and spacing scales, the core components, and an accessibility
  checks page (NOMI-012).
- **Screens:** [Nomi Demo Prototype](https://www.figma.com/design/xay5w9vFOvEeJU6a6rzzp8) has every screen,
  with notes and data callouts (NOMI-013).

### Add the library to a Figma file

1. Open the Assets tab.
2. Click the Libraries (book) icon.
3. Turn on "Nomi Library".

### Publish library changes

You need edit access to the library file.

1. Open the Assets tab and click the Libraries (book) icon. You can also click the dropdown arrow next to the
   file name and choose "Publish library".
2. Click "Publish".
3. Add a short note about what changed and click "Publish" again.

### Accept library changes in your file

1. When updates are waiting, the Libraries icon shows a blue badge. Click it.
2. Open the "Updates" tab and turn on "Show updates for all pages".
3. Click "Update all", or "Update" next to a single component to take just that one.
