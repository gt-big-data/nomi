/**
 * Barcodes you can open without a camera: the iOS Simulator has none, and a demo shouldn't depend
 * on aiming at a box. Each one goes through the same lookup as a real scan.
 */

/** The five reference products (NOMI-015), with the UPC printed on each box. */
export const REFERENCE_BARCODES = [
  { name: "Aleve Liquid Gels", barcode: "302806080201" },
  { name: "Tylenol Extra Strength", barcode: "350580449059" },
  { name: "Vicks NyQuil Cold and Flu", barcode: "369423995165" },
  { name: "Equate Allergy Relief", barcode: "379903297108" },
  { name: "ZzzQuil Nighttime Sleep-Aid", barcode: "384126316048" },
] as const;

/** One barcode per result state that the five products don't show. */
export const STATE_BARCODES = [
  // A valid drug barcode (labeler 99999 isn't assigned by the FDA) that isn't in the dataset.
  { name: "Medicine we don't have", barcode: "399999004015" },
  // A real EAN-13 that isn't a medicine.
  { name: "Not a medicine", barcode: "4006381333931" },
  // Tylenol's barcode with the last digit changed.
  { name: "Misread barcode", barcode: "350580449050" },
] as const;
