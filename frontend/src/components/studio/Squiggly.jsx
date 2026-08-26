// Shared helpers for the AI Writing Coach red-squiggly underlines.

const isWordChar = (ch) => /[A-Za-z0-9]/.test(ch || "");

// Find the first index of `needle` in `text` (at/after `start`) that respects
// word boundaries, so a short token like "i" never matches inside "First".
export function findBoundaryIndex(text, needle, start = 0) {
  if (!needle) return -1;
  const needStartWord = isWordChar(needle[0]);
  const needEndWord = isWordChar(needle[needle.length - 1]);
  let from = start;
  let idx;
  while ((idx = text.indexOf(needle, from)) !== -1) {
    const before = idx > 0 ? text[idx - 1] : "";
    const after = idx + needle.length < text.length ? text[idx + needle.length] : "";
    const okStart = !needStartWord || !isWordChar(before);
    const okEnd = !needEndWord || !isWordChar(after);
    if (okStart && okEnd) return idx;
    from = idx + 1;
  }
  return -1;
}

// Split `value` into segments, marking the first non-overlapping, word-boundary
// occurrence of each issue's flagged substring so it can be underlined.
export function computeSegments(value, issues) {
  const text = value || "";
  if (!issues || !issues.length) return [{ t: text }];
  const ranges = [];
  const used = [];
  const overlaps = (s, e) => used.some(([us, ue]) => s < ue && e > us);
  issues.forEach((iss) => {
    const needle = iss && iss.text ? iss.text : "";
    if (!needle) return;
    let from = 0;
    let idx;
    while ((idx = findBoundaryIndex(text, needle, from)) !== -1) {
      const end = idx + needle.length;
      if (!overlaps(idx, end)) {
        ranges.push({ start: idx, end, iss });
        used.push([idx, end]);
        break;
      }
      from = idx + 1;
    }
  });
  if (!ranges.length) return [{ t: text }];
  ranges.sort((a, b) => a.start - b.start);
  const segs = [];
  let cur = 0;
  ranges.forEach((r) => {
    if (r.start < cur) return;
    if (r.start > cur) segs.push({ t: text.slice(cur, r.start) });
    segs.push({ t: text.slice(r.start, r.end), bad: true, iss: r.iss });
    cur = r.end;
  });
  if (cur < text.length) segs.push({ t: text.slice(cur) });
  return segs;
}

// Transparent-text mirror layer placed BEHIND a textarea. Its wavy underlines
// line up under the words the (visible, transparent-background) textarea draws.
export function SquigglyBackdrop({ value, issues, style, className }) {
  const segs = computeSegments(value || "", issues || []);
  return (
    <div
      aria-hidden
      className={`absolute inset-0 pointer-events-none whitespace-pre-wrap break-words overflow-hidden ${className || ""}`}
      style={{ ...(style || {}), color: "transparent" }}
    >
      {segs.map((s, i) =>
        s.bad ? (
          <span key={i} className="hq-squiggly">{s.t}</span>
        ) : (
          <span key={i}>{s.t}</span>
        )
      )}
    </div>
  );
}

// Read-only display of text with visible words + red squigglies (e.g. a sent email).
export function SquigglyText({ value, issues, className }) {
  const segs = computeSegments(value || "", issues || []);
  return (
    <span className={className}>
      {segs.map((s, i) =>
        s.bad ? (
          <mark key={i} className="hq-squiggly" style={{ background: "transparent", color: "inherit" }} title={s.iss ? `${s.iss.message}${s.iss.suggestion ? " → " + s.iss.suggestion : ""}` : ""}>{s.t}</mark>
        ) : (
          <span key={i}>{s.t}</span>
        )
      )}
    </span>
  );
}
