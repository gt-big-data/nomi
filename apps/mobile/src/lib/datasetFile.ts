/**
 * Opens the app's copy of the dataset, copying the bundled one over it when it is missing or bad
 * (NOMI-040). dataset.ts passes in expo-sqlite; the tests pass in node:sqlite.
 */

import { checkDataset, type Dataset } from "./db.ts";

export interface DatasetFile<D extends Dataset> {
  /** The copy's file name, nomi-<asset hash>.sqlite. */
  name: string;
  /** Opens the copy. A missing file opens as an empty database. */
  open(): Promise<D & { closeAsync(): Promise<void> }>;
  /** Copies the bundled dataset over the copy. */
  copy(): Promise<void>;
  /** The names of the files in the database folder. */
  list(): Promise<string[]>;
  /** Deletes a database in that folder. */
  remove(name: string): Promise<void>;
}

const COPY_NAME = /^nomi-.+\.sqlite$/;

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

/** Deletes copies of earlier datasets, which an app update leaves behind. */
async function removeOldCopies<D extends Dataset>(file: DatasetFile<D>): Promise<void> {
  try {
    for (const name of await file.list()) {
      if (name !== file.name && COPY_NAME.test(name)) {
        await file.remove(name);
      }
    }
  } catch (error) {
    // The next launch tries again; the open copy works either way.
    console.warn("Couldn't remove an old dataset copy:", error);
  }
}

async function openOrCopyOnce<D extends Dataset>(file: DatasetFile<D>): Promise<D> {
  try {
    // Usually the copy from an earlier launch. Opening a missing file creates an empty database
    // (user_version 0), which fails the check, so the first launch falls through to the copy.
    return await openChecked(file);
  } catch (cause) {
    // Also covers a copy cut short (the app killed mid-copy), which still opens but fails the check.
    try {
      await file.copy();
      return await openChecked(file);
    } catch (error) {
      // cause says why the copy was needed.
      throw new Error(`Couldn't open or copy the dataset: ${(error as Error).message}`, { cause });
    }
  }
}

export async function openOrCopy<D extends Dataset>(file: DatasetFile<D>): Promise<D> {
  const db = await openOrCopyOnce(file);
  await removeOldCopies(file);
  return db;
}
