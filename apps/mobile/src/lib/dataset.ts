/**
 * Opens the bundled dataset, assets/nomi.sqlite, once per app launch (NOMI-040).
 *
 * SQLite needs a writable file it can open by path, and the app package is neither, so the first
 * launch copies it into the app's database folder. The copy is named after the asset's hash, so an
 * app update with a new dataset gets a fresh copy instead of reusing the old one. dataset.web.ts
 * replaces this file on web.
 */

import { Asset } from "expo-asset";
import { importDatabaseFromAssetAsync, openDatabaseAsync } from "expo-sqlite";

import { openOrCopy } from "./datasetFile.ts";
import type { Dataset } from "./db.ts";

// Built by pnpm db:fixture or pnpm db:copy (see README); in development, metro.config.js builds
// the fixture if it is missing.
const ASSET = require("../../assets/nomi.sqlite");

let opening: Promise<Dataset> | null = null;

function open(): Promise<Dataset> {
  // Reads the hash from the bundle's asset registry; nothing is downloaded or hashed here.
  const name = `nomi-${Asset.fromModule(ASSET).hash}.sqlite`;
  return openOrCopy({
    open: () => openDatabaseAsync(name),
    // importDatabaseFromAssetAsync is marked @hidden in expo-sqlite, but it is what
    // SQLiteProvider's assetSource uses. It resolves and copies the asset, so it only runs when needed.
    copy: () => importDatabaseFromAssetAsync(name, { assetId: ASSET, forceOverwrite: true }),
  });
}

/** The open dataset. Safe to call on every scan: it opens the file only once. */
export function openDataset(): Promise<Dataset> {
  if (!opening) {
    opening = open().catch((error) => {
      // Let the next call try again.
      opening = null;
      throw error;
    });
  }
  return opening;
}
