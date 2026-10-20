import Image from "next/image";
import Link from "next/link";
import { assetUrl } from "@/lib/api";
import { LATERALITY_TEXT, examPath, formatNumber, shortExamId } from "@/lib/format";
import type { ExamSummary } from "@/lib/types";
import { LabelBadge } from "./LabelBadge";

export function ExamCard({ exam, backQuery }: { exam: ExamSummary; backQuery: string }) {
  const href = backQuery ? `${examPath(exam.exam_id)}?${backQuery}` : examPath(exam.exam_id);
  return (
    <li className="card">
      <Link href={href} className="card__link">
        {exam.thumbnail_url ? (
          <Image
            src={assetUrl(exam.thumbnail_url)}
            alt={`Anterior axial curvature map of ${shortExamId(exam.exam_id)}`}
            width={224}
            height={224}
            unoptimized
            className="card__image"
          />
        ) : (
          <div className="card__image card__image--missing">No image</div>
        )}
        <div className="card__body">
          <div className="card__row">
            <LabelBadge label={exam.label} />
            {exam.possible_duplicate_of.length > 0 && (
              <span className="badge badge--warning">Possible duplicate</span>
            )}
          </div>
          <p className="card__title">{shortExamId(exam.exam_id)}</p>
          <p className="muted">{LATERALITY_TEXT[exam.laterality]}</p>
          <dl className="card__facts">
            <div>
              <dt>Visible min thickness</dt>
              <dd>
                {exam.min_thickness_um === null
                  ? "—"
                  : `${formatNumber(exam.min_thickness_um, 0)} µm`}
              </dd>
            </div>
            <div>
              <dt>Visible max curvature</dt>
              <dd>
                {exam.max_curvature_a_d === null
                  ? "—"
                  : `${formatNumber(exam.max_curvature_a_d)} D`}
              </dd>
            </div>
          </dl>
        </div>
      </Link>
    </li>
  );
}
