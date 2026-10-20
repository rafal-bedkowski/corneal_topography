import { LABEL_TEXT } from "@/lib/format";
import type { Label } from "@/lib/types";

export function LabelBadge({ label, prefix = false }: { label: Label; prefix?: boolean }) {
  return (
    <span className={`badge badge--${label}`}>
      {prefix ? `Dataset label: ${LABEL_TEXT[label]}` : LABEL_TEXT[label]}
    </span>
  );
}
