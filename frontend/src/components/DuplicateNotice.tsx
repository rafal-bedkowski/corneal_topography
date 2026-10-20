import Link from "next/link";
import { EXCLUSION_TEXT, examPath, shortExamId } from "@/lib/format";
import type { ExclusionReason } from "@/lib/types";

interface Props {
  duplicates: string[];
  excluded: boolean;
  reason: ExclusionReason | null;
}

export function DuplicateNotice({ duplicates, excluded, reason }: Props) {
  if (duplicates.length === 0) return null;
  return (
    <div className="notice notice--warning" role="note">
      <p>
        This exam looks like a duplicate of{" "}
        {duplicates.map((examId, index) => (
          <span key={examId}>
            {index > 0 && ", "}
            <Link href={examPath(examId)}>{shortExamId(examId)}</Link>
          </span>
        ))}
        .
      </p>
      <p>{excluded && reason ? EXCLUSION_TEXT[reason] : "It is included in the statistics."}</p>
    </div>
  );
}
