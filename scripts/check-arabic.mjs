import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const atlas = JSON.parse(readFileSync("public/atlas/index.json", "utf8"));
const arabic = /[\u0600-\u06ff]/u;
const harakat = /[\u064b-\u065f\u0670\u06d6-\u06ed]/u;

assert.equal(atlas.words.length, atlas.count);
assert.deepEqual(atlas.fields, ["id", "word", "zh", "ipa", "cefr", "topic", "media", "ar"]);

for (const row of atlas.words) {
  const [id, word, , , , , , gloss] = row;
  assert.equal(typeof gloss, "string", `${word} (${id}) has no Arabic gloss`);
  assert.match(gloss, arabic, `${word} (${id}) has no Arabic letters`);
  assert.match(gloss, harakat, `${word} (${id}) has no Arabic reading marks`);
  assert.doesNotMatch(gloss, /[\\[\]<>{}]/u, `${word} (${id}) has unescaped dictionary markup`);
}

console.log(`Verified ${atlas.words.length.toLocaleString()} Arabic glosses with reading marks.`);
