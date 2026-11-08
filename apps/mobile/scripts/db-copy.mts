// pnpm db:copy: copies the pipeline's build (NOMI-038) into the app as assets/nomi.sqlite.
import { copyFileSync, existsSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";

import { checkDataset } from "../src/lib/db.ts";

const build = fileURLToPath(new URL("../../../data/build/nomi.sqlite", import.meta.url));
const out = fileURLToPath(new URL("../assets/nomi.sqlite", import.meta.url));
if (!existsSync(build)) {
  console.error(`${build} not found. Build it with the pipeline, or run pnpm db:fixture instead.`);
  process.exit(1);
}

// Run the app's own open check here, so a build the app would refuse never reaches a bundle.
let db: DatabaseSync | undefined;
try {
  db = new DatabaseSync(build, { readOnly: true });
  const open = db;
  await checkDataset({
    async getAllAsync<T>(sql: string, params: (string | number)[]) {
      return open.prepare(sql).all(...params) as unknown as T[];
    },
  });
} catch (error) {
  console.error(`${build} isn't a dataset the app can open: ${(error as Error).message}`);
  process.exitCode = 1;
} finally {
  db?.close();
}

if (process.exitCode !== 1) {
  copyFileSync(build, out);
  console.log(`Copied ${build} to ${out}.`);
}
