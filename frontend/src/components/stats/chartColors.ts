import type { Label } from "@/lib/types";

/** Colour-blind-safe palette (ColorBrewer Dark2), one colour per dataset class. */
export const LABEL_COLORS: Record<Label, string> = {
  normal: "#1b9e77",
  keratoconus: "#d95f02",
  suspect: "#7570b3",
};
