/** Normalize Arabic for tolerant search input without requiring the learner to type vowels. */
export function normalizeArabic(value: string) {
  return value
    .toLowerCase()
    .replace(/[\u064b-\u065f\u0670\u06d6-\u06ed\u0640]/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه");
}
