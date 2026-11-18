# Install the Nomi demo on an iPhone

How to put the `demo/v1-path` build of Nomi on your own iPhone. It takes about 30 minutes the first time.

## What you need

- A Mac with the latest Xcode (from the App Store)
- An Apple ID (a free one works)
- An iPhone and a cable to the Mac
- [Node.js](https://nodejs.org) 20 or newer, [pnpm](https://pnpm.io/installation) and [uv](https://docs.astral.sh/uv/)

## 1. Get the code

```bash
git clone https://github.com/gt-big-data/nomi.git
cd nomi
git checkout demo/v1-path
pnpm install
```

## 2. Build the product database

The app looks up barcodes in `apps/mobile/assets/nomi.sqlite`, which isn't in git.

**Full dataset** (about 17,000 scorable products). From the repo root:

```bash
uv run pipeline fetch ndc
uv run pipeline fetch dailymed-otc
uv run pipeline ingest ndc
uv run pipeline ingest spl
uv run pipeline identity resolve
uv run pipeline build dataset
cd apps/mobile && pnpm db:copy
```

**Quick option** (only the 5 reference products: Aleve, Tylenol, NyQuil, Equate Allergy, ZzzQuil):

```bash
cd apps/mobile && pnpm db:fixture
```

## 3. Set up Xcode and the iPhone (once)

1. Open Xcode › Settings › Apple Accounts and sign in with your Apple ID.
2. On the iPhone, turn on Settings › Privacy & Security › Developer Mode, and restart when it asks.
3. Plug the iPhone into the Mac, unlock it, and tap **Trust** if it asks.

## 4. Build and install

From `apps/mobile`, with the iPhone plugged in and unlocked:

```bash
NOMI_IOS_BUNDLE_ID=com.yourname.nomi npx expo run:ios --device --configuration Release
```

- Replace `yourname` with something of your own. Free Apple IDs can't share an app ID.
- Pick your iPhone when it asks for a device.
- `Release` builds a standalone app that works away from the Mac.

## 5. Open it

The first time, iOS blocks the app. On the iPhone, go to Settings › General › VPN & Device Management, tap your Apple ID and tap **Trust**. Then open Nomi.

## Good to know

- **It expires after 7 days** with a free Apple ID. Run step 4 again to reinstall.
- **Your answers survive reinstalling.** To answer the setup questions again, open Profile › Answer again.
- **"Device unavailable" or "not paired" errors:** unplug the iPhone, plug it back in, unlock it, and try again. Opening Xcode › Window › Devices and Simulators can help it find the phone.
- **"No account for team" errors:** sign in to your Apple ID in Xcode (step 3.1), then try again.
