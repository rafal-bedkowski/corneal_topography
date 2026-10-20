import { LABEL_TEXT } from "@/lib/format";
import type { ClassStats } from "@/lib/types";

export function ExtractionTable({ classes }: { classes: ClassStats[] }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <caption className="sr-only">Quality of the automatic text extraction per class</caption>
        <thead>
          <tr>
            <th scope="col">Class</th>
            <th scope="col">Accepted</th>
            <th scope="col">Low confidence</th>
            <th scope="col">Out of range</th>
            <th scope="col">Ignored labels</th>
          </tr>
        </thead>
        <tbody>
          {classes.map((item) => (
            <tr key={item.label}>
              <th scope="row">{LABEL_TEXT[item.label]}</th>
              <td>{item.extraction.accepted}</td>
              <td>{item.extraction.low_confidence}</td>
              <td>{item.extraction.out_of_range}</td>
              <td>{item.extraction.rejected}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
