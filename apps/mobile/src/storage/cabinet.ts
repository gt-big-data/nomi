import { File, Paths } from "expo-file-system";
import { useSyncExternalStore } from "react";

import type { ProductTier } from "@/theme";

/** One scanned barcode, as the cabinet shows it. Stays on the phone; nothing is sent anywhere. */
export type CabinetItem = {
  barcode: string;
  /** Brand name, or the NDC11 when there is none. */
  name: string;
  /** Generic name, when there is one. */
  generic?: string;
  /** The tier and score from the last time it was opened. */
  tier: ProductTier;
  score?: number;
  /** When it was last scanned or opened, in ms since 1970. */
  seenAt: number;
  /** Marked as a medicine this person takes. */
  taking: boolean;
};

/** Made on first use, not at import: the build also loads this module where there is no phone. */
let cached: File | undefined;
function file(): File {
  cached ??= new File(Paths.document, "cabinet.json");
  return cached;
}
/** The most scans kept, newest first. Medicines marked as taking are always kept. */
const MAX = 200;

/** The names earlier builds gave scans that found no product. */
const FAILED = new Set(["Not found", "Can't look up", "Couldn't read barcode"]);

let items: CabinetItem[] = [];
const listeners = new Set<() => void>();

function set(next: CabinetItem[]): void {
  items = next;
  for (const listener of listeners) listener();
  try {
    file().write(JSON.stringify(next));
  } catch {
    console.error("Couldn't save the cabinet.");
  }
}

/** Reads the cabinet once at launch. */
export async function loadCabinet(): Promise<void> {
  try {
    if (file().exists) {
      const saved = JSON.parse(await file().text()) as CabinetItem[];
      // Earlier builds also saved scans that found nothing; Home only shows products.
      items = saved.filter((item) => !FAILED.has(item.name));
      for (const listener of listeners) listener();
    }
  } catch {
    console.error("Couldn't read the cabinet.");
  }
}

/** Adds a scan, or moves it to the top with its latest score. Keeps whether it's marked as taking. */
export function recordScan(scan: Omit<CabinetItem, "seenAt" | "taking">): void {
  const old = items.find((item) => item.barcode === scan.barcode);
  const rest = items.filter((item) => item.barcode !== scan.barcode);
  const next = [{ ...scan, seenAt: Date.now(), taking: old?.taking ?? false }, ...rest];
  const kept = next.filter((item, index) => item.taking || index < MAX);
  set(kept);
}

/** Marks a scanned medicine as taken or not. */
export function setTaking(barcode: string, taking: boolean): void {
  set(items.map((item) => (item.barcode === barcode ? { ...item, taking } : item)));
}

/** Everything scanned, newest first, kept up to date. */
export function useCabinet(): CabinetItem[] {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => items,
    () => items,
  );
}
