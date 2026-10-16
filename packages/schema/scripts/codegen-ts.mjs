// Generates TypeScript types from packages/schema/schemas into generated/ts.
// Each schema gets its own module; index.ts re-exports the types each schema owns.
import { readdir, readFile, rm, mkdir, writeFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const schemaDir = join(root, "schemas");
const outDir = join(root, "generated", "ts");

const banner = "// Generated from packages/schema/schemas by scripts/codegen-ts.mjs. Do not edit.";

await rm(outDir, { recursive: true, force: true });
await mkdir(outDir, { recursive: true });

const files = (await readdir(schemaDir)).filter((f) => f.endsWith(".schema.json")).sort();
const exports = [];

for (const file of files) {
  const schema = JSON.parse(await readFile(join(schemaDir, file), "utf8"));
  const moduleName = file.replace(".schema.json", "");
  const ts = await compile(schema, schema.title, {
    cwd: schemaDir,
    bannerComment: banner,
    additionalProperties: false,
    unreachableDefinitions: true,
    format: true,
    style: { printWidth: 100 },
  });
  await writeFile(join(outDir, `${moduleName}.ts`), ts);

  // Types this schema owns: its own title (unless it only holds $defs) and its $defs titles.
  const owned = Object.values(schema.$defs ?? {}).map((d) => d.title).filter(Boolean);
  if (schema.type) owned.unshift(schema.title);
  exports.push(`export type { ${owned.join(", ")} } from "./${moduleName}";`);
}

await writeFile(join(outDir, "index.ts"), `${banner}\n\n${exports.join("\n")}\n`);
console.log(`Generated ${files.length} TypeScript modules in generated/ts`);
