/**
 * Opens the bundled dataset, assets/nomi.sqlite, once per app launch (NOMI-040).
 *
 * SQLite needs a writable file it can open by path, and the app package is neither, so the first
 * launch copies it into the app's database folder. The copy is named after the asset's hash, so an
 * app update with a new dataset gets a fresh copy instead of reusing the old one. dataset.web.ts
 * replaces this file on web.
 */

import { Asset } from "expo-asset";
import { importDatabaseFromAssetAsync, openDatabaseAsync, type SQLiteDatabase } from "expo-sqlite";

import { checkDataset, type Dataset } from "./db.ts";

// Built by pnpm db:fixture or pnpm db:copy (see README); in development, metro.config.js builds
// the fixture if it is missing.
const ASSET = require("../../assets/nomi.sqlite");

let opening: Promise<Dataset> | null = null;

async function openChecked(name: string): Promise<SQLiteDatabase> {
  const db = await openDatabaseAsync(name);
  try {
    await checkDataset(db);
    return db;
  } catch (error) {
    await db.closeAsync().catch(() => {});
    throw error;
  }
}

async function open(): Promise<Dataset> {
  // Reads the hash from the bundle's asset registry; nothing is downloaded or hashed here.
  const name = `nomi-${Asset.fromModule(ASSET).hash}.sqlite`;
  try {
    // Usually the copy from an earlier launch. Opening a missing file creates an empty database
    // (user_version 0), which fails the check, so the first launch falls through to the copy.
    return await openChecked(name);
  } catch {
    // Also covers a copy cut short (the app killed mid-copy), which still opens but fails the check.
    // importDatabaseFromAssetAsync is marked @hidden in expo-sqlite, but it is what
    // SQLiteProvider's assetSource uses. It resolves and copies the asset, so it only runs when needed.
    await importDatabaseFromAssetAsync(name, { assetId: ASSET, forceOverwrite: true });
    return openChecked(name);
  }
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
