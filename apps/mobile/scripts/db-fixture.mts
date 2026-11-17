// pnpm db:fixture: writes assets/nomi.sqlite from the reference products (NOMI-015).
import { rmSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";

import { buildDataset, referenceProducts } from "./fixture.mts";

const out = fileURLToPath(new URL("../assets/nomi.sqlite", import.meta.url));
rmSync(out, { force: true });
const db = new DatabaseSync(out);
buildDataset(db, referenceProducts(), "fixture");
db.close();
console.log(`Wrote ${out} from the reference products.`);
