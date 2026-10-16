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
- Uses a development build (`react-native-vision-camera` does not run in Expo Go).
