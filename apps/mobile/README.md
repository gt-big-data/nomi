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
