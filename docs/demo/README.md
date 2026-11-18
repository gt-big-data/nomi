# Running the Nomi demo

How to present Nomi from the `demo/v1-path` build. To put the app on a phone first, see
[apps/mobile/INSTALL.md](../../apps/mobile/INSTALL.md).

## Before you present

- **Install a Release build with the full dataset** (INSTALL.md, step 2, "Full dataset"). The quick fixture
  only knows the five reference products, so store brands like Good Neighbor and CVS won't be found.
- **Answer the setup questions** on the phone once, so the first scan opens straight to a score.
- **Bring boxes to scan.** These work on the current build:

  | Product | Barcode |
  | --- | --- |
  | Tylenol Extra Strength | 350580449059 |
  | Aleve Liquid Gels | 302806080201 |
  | Vicks NyQuil Cold and Flu | 369423995165 |
  | Equate Allergy Relief | 379903297108 |
  | ZzzQuil Nighttime Sleep-Aid | 384126316048 |
  | Good Neighbor Pharmacy acetaminophen | 346122312783 |
  | CVS Health Extra Strength Acetaminophen 500 mg | 050428164181 |

- **Charge the phone and turn the brightness up.** Scanning works offline, so Wi-Fi doesn't matter.

## The walkthrough (about 3 minutes)

1. **Open Nomi.** It opens to the camera. The pill at the top says who it's scoring for.
2. **Scan Tylenol.** Hold the barcode inside the rounded frame. The result shows a score out of 100, a
   tier word and how many risks took points off.
3. **Tap a row under "Why this score".** A sheet slides up with the reason, the quote from the FDA label and
   the source. If the source has a link icon, tap it to open the label. Drag the sheet down to close it.
4. **Switch who will take it.** Use the switcher under the score (you, Adult, 65+, Child). The score changes
   with the person. Some products say **Do not use** for some people, and then the screen offers only
   "Scan again".
5. **Tap "I take this".** Then tap Home (top left on the camera). The product is listed under Taking.
6. **Scan a store brand** (Good Neighbor or CVS) to show that it isn't limited to name brands.

Points worth saying out loud:

- Everything runs on the phone. No account, no internet, and no health answers leave the device.
- Every point taken off links back to a public source (FDA labels, FAERS).
- Scores marked **Preliminary** come from rubric v0 and haven't been reviewed by a pharmacist yet.

## If something goes wrong

- **The camera won't read a box:** tap **Type a barcode** at the bottom of the camera and either type the
  numbers or pick one of the reference products. It goes through the same lookup as a real scan.
- **"Not found" for a real medicine:** the box's barcode isn't in the dataset yet. Some store brands print
  a store code instead of the drug code. Use one of the barcodes in the table above.
- **The app won't open:** a free Apple ID build expires after 7 days. Reinstall (INSTALL.md, step 4) the
  day before.
- **Home has old scans in it:** only successful scans are saved there. Deleting and reinstalling the app
  clears Home and your answers.

## Shortcut for screenshots

With the phone plugged in, open any result directly from the Mac:

```bash
xcrun devicectl device process launch --terminate-existing --device <device id> --payload-url "nomi://result?barcode=350580449059" <bundle id>
```

`xcrun devicectl list devices` shows the device id. The bundle id is the one you built with.
