/**
 * Opens the app's copy of the dataset, copying the bundled one over it when it is missing or bad
 * (NOMI-040). dataset.ts passes in expo-sqlite; the tests pass in node:sqlite.
 */

import { checkDataset, type Dataset } from "./db.ts";

export interface DatasetFile<D extends Dataset> {
  /** Opens the copy. A missing file opens as an empty database. */
  open(): Promise<D & { closeAsync(): Promise<void> }>;
  /** Copies the bundled dataset over the copy. */
  copy(): Promise<void>;
}

async function openChecked<D extends Dataset>(file: DatasetFile<D>): Promise<D> {
  const db = await file.open();
  try {
    await checkDataset(db);
    return db;
  } catch (error) {
    await db.closeAsync().catch(() => {});
    throw error;
  }
}

export async function openOrCopy<D extends Dataset>(file: DatasetFile<D>): Promise<D> {
  try {
    // Usually the copy from an earlier launch. Opening a missing file creates an empty database
    // (user_version 0), which fails the check, so the first launch falls through to the copy.
    return await openChecked(file);
  } catch {
    // Also covers a copy cut short (the app killed mid-copy), which still opens but fails the check.
    await file.copy();
    return openChecked(file);
  }
}
