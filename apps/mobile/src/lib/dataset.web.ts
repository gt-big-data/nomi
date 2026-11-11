// Web build of dataset.ts. The app is for phones; expo-sqlite would pull in its WebAssembly build,
// so on web the lookup reports that there is no product database.
import type { Dataset } from "./db.ts";

export function openDataset(): Promise<Dataset> {
  return Promise.reject(new Error("The product database isn't available on web."));
}
