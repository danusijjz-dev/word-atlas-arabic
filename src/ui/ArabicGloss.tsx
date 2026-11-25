export function ArabicGloss({
  value,
  className = "",
}: {
  value?: string | null;
  className?: string;
}) {
  if (!value) return null;
  return (
    <span className={`arabic-gloss ${className}`.trim()}>
      <span className="sr-only">阿拉伯语：</span>
      <span aria-hidden="true">(</span>
      <bdi dir="rtl" lang="ar">
        {value}
      </bdi>
      <span aria-hidden="true">)</span>
    </span>
  );
}
