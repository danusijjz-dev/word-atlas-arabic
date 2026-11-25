import assert from "node:assert/strict";
import test from "node:test";
import { normalizeArabic } from "./arabic";

test("Arabic search ignores vowels and common letter variants", () => {
  assert.equal(normalizeArabic("مَكْتَبَة"), normalizeArabic("مكتبه"));
  assert.equal(normalizeArabic("إِجَازَة"), normalizeArabic("اجازه"));
  assert.equal(normalizeArabic("مُوسِيقَى"), normalizeArabic("موسيقي"));
});
