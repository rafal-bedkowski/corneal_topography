import { INDICATOR_KEYS, INDICATOR_TEXT, INDICATOR_TOOLTIP, formatIndicator } from "@/lib/format";
import type { Indicators } from "@/lib/types";

export function IndicatorsPanel({ indicators }: { indicators: Indicators }) {
  return (
    <section aria-labelledby="indicators-heading" className="panel">
      <h2 id="indicators-heading">Indicators from printed values</h2>
      <p className="muted">{INDICATOR_TOOLTIP}</p>
      <dl className="indicators">
        {INDICATOR_KEYS.map((key) => (
          <div key={key} title={INDICATOR_TOOLTIP}>
            <dt>{INDICATOR_TEXT[key].name}</dt>
            <dd>{formatIndicator(key, indicators[key])}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
