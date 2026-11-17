// Runs openOrCopy on real files with node:sqlite, in place of expo-sqlite and the bundled asset.
import assert from "node:assert/strict";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { test, type TestContext } from "node:test";

import { buildDataset, referenceProducts } from "../../scripts/fixture.mts";
import { openOrCopy } from "./datasetFile.ts";

const NAME = "nomi-new.sqlite";

/** A database folder, and a bundled dataset outside it. */
function folders(t: TestContext) {
  const dir = mkdtempSync(join(tmpdir(), "nomi-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const bundled = join(dir, "bundled.sqlite");
  const db = new DatabaseSync(bundled);
  buildDataset(db, referenceProducts(), "test");
  db.close();
  const databases = join(dir, "SQLite");
  mkdirSync(databases);
  return { bundled, databases, copy: join(databases, NAME) };
}

function edit(path: string, sql: string) {
  const db = new DatabaseSync(path);
  db.exec(sql);
  db.close();
}

/** openOrCopy's file, counting copies. copy() runs instead of the bundled copy when given. */
function file(
  { bundled, databases, copy: path }: ReturnType<typeof folders>,
  copy = () => copyFileSync(bundled, path),
) {
  const opened: DatabaseSync[] = [];
  const result = {
    name: NAME,
    copies: 0,
    opened,
    async open() {
      const db = new DatabaseSync(path);
      opened.push(db);
      return {
        async getAllAsync<T>(sql: string, params: (string | number)[]) {
          return db.prepare(sql).all(...params) as unknown as T[];
        },
        async closeAsync() {
          db.close();
        },
      };
    },
    async copy() {
      result.copies++;
      copy();
    },
    async list() {
      return readdirSync(databases);
    },
    async remove(name: string) {
      rmSync(join(databases, name));
    },
  };
  return result;
}

test("copies the bundled dataset when there is no copy yet", async (t) => {
  const paths = folders(t);
  const f = file(paths);
  await openOrCopy(f);
  assert.equal(f.copies, 1);
  assert.ok(existsSync(paths.copy));
});

test("opens an earlier copy without copying again", async (t) => {
  const paths = folders(t);
  copyFileSync(paths.bundled, paths.copy);
  const f = file(paths);
  await openOrCopy(f);
  assert.equal(f.copies, 0);
});

test("copies again over a copy that fails the check, and closes it first", async (t) => {
  const paths = folders(t);
  edit(paths.copy, "PRAGMA user_version = 99");
  const f = file(paths);
  await openOrCopy(f);
  assert.equal(f.copies, 1);
  assert.equal(f.opened[0].isOpen, false);
});

test("deletes the copies of earlier datasets, and nothing else", async (t) => {
  const paths = folders(t);
  for (const name of ["nomi-old.sqlite", "nomi-older.sqlite", "other.sqlite"]) {
    writeFileSync(join(paths.databases, name), "");
  }
  await openOrCopy(file(paths));
  assert.deepEqual(readdirSync(paths.databases).sort(), [NAME, "other.sqlite"]);
});

test("fails when the bundled dataset fails the check too", async (t) => {
  const paths = folders(t);
  edit(paths.bundled, "DELETE FROM meta");
  const f = file(paths);
  await assert.rejects(openOrCopy(f), /meta rows/);
  assert.ok(f.opened.every((db) => !db.isOpen));
});

test("fails when the copy fails, with why it was copying", async (t) => {
  const paths = folders(t);
  const f = file(paths, () => {
    throw new Error("disk full");
  });
  await assert.rejects(openOrCopy(f), (error: Error) => {
    assert.match(error.message, /disk full/);
    assert.match((error.cause as Error).message, /schema version 0/);
    return true;
  });
  assert.equal(f.opened[0].isOpen, false);
});
