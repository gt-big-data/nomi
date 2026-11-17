// Runs openOrCopy on real files with node:sqlite, in place of expo-sqlite and the bundled asset.
import assert from "node:assert/strict";
import { copyFileSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { test, type TestContext } from "node:test";

import { buildDataset, referenceProducts } from "../../scripts/fixture.mts";
import { openOrCopy } from "./datasetFile.ts";

/** A bundled dataset, and a path for the app's copy of it, in a fresh folder. */
function files(t: TestContext) {
  const dir = mkdtempSync(join(tmpdir(), "nomi-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const bundled = join(dir, "bundled.sqlite");
  const db = new DatabaseSync(bundled);
  buildDataset(db, referenceProducts(), "test");
  db.close();
  return { bundled, copy: join(dir, "copy.sqlite") };
}

function edit(path: string, sql: string) {
  const db = new DatabaseSync(path);
  db.exec(sql);
  db.close();
}

/** openOrCopy's file, counting copies. copy() runs instead of the bundled copy when given. */
function file(path: string, bundled: string, copy = () => copyFileSync(bundled, path)) {
  const opened: DatabaseSync[] = [];
  const result = {
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
  };
  return result;
}

test("copies the bundled dataset when there is no copy yet", async (t) => {
  const { bundled, copy } = files(t);
  const f = file(copy, bundled);
  await openOrCopy(f);
  assert.equal(f.copies, 1);
  assert.ok(existsSync(copy));
});

test("opens an earlier copy without copying again", async (t) => {
  const { bundled, copy } = files(t);
  copyFileSync(bundled, copy);
  const f = file(copy, bundled);
  await openOrCopy(f);
  assert.equal(f.copies, 0);
});

test("copies again over a copy that fails the check, and closes it first", async (t) => {
  const { bundled, copy } = files(t);
  edit(copy, "PRAGMA user_version = 99");
  const f = file(copy, bundled);
  await openOrCopy(f);
  assert.equal(f.copies, 1);
  assert.equal(f.opened[0].isOpen, false);
});

test("fails when the bundled dataset fails the check too", async (t) => {
  const { bundled, copy } = files(t);
  edit(bundled, "DELETE FROM meta");
  const f = file(copy, bundled);
  await assert.rejects(openOrCopy(f), /meta rows/);
  assert.ok(f.opened.every((db) => !db.isOpen));
});

test("fails when the copy fails", async (t) => {
  const { bundled, copy } = files(t);
  const f = file(copy, bundled, () => {
    throw new Error("disk full");
  });
  await assert.rejects(openOrCopy(f), /disk full/);
});
