// Expo's default Metro config, plus the bundled dataset (NOMI-040).
const { execFileSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");
const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push("sqlite");

// assets/nomi.sqlite is generated, not committed, and the bundle fails without it. Expo's CLI sets
// NODE_ENV to production before loading this file for release bundles (expo export, and
// expo export:embed, which Xcode and Gradle release builds run), so those stop instead of
// building the five-product fixture. This only covers a missing file: a fixture left by an earlier
// development run still ships. In development, a fresh clone gets the fixture.
if (!existsSync(path.join(__dirname, "assets", "nomi.sqlite"))) {
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "assets/nomi.sqlite is missing. Run pnpm db:copy (or pnpm db:fixture) in apps/mobile first.",
    );
  }
  console.warn("assets/nomi.sqlite is missing; building the fixture (pnpm db:fixture).");
  execFileSync(
    process.execPath,
    ["--no-warnings=ExperimentalWarning", path.join(__dirname, "scripts", "db-fixture.mts")],
    { stdio: "inherit" },
  );
}

module.exports = config;
