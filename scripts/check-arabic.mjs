import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";

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

let examples = 0;
let collocations = 0;
const entryDir = "public/atlas/entries";
for (const name of readdirSync(entryDir).filter((name) => name.endsWith(".json"))) {
  const entries = JSON.parse(readFileSync(`${entryDir}/${name}`, "utf8"));
  for (const entry of entries) {
    for (const example of entry.ex || []) {
      assert.equal(typeof example.ar, "string", `${entry.w}: example has no Arabic`);
      assert.match(example.ar, arabic, `${entry.w}: example has no Arabic letters`);
      assert.match(example.ar, harakat, `${entry.w}: example has no reading marks`);
      examples++;
    }
    for (const collocation of entry.col || []) {
      const parts = collocation.split("｜");
      assert.equal(parts.length, 3, `${entry.w}: malformed collocation`);
      const gloss = parts[2];
      assert.match(gloss, arabic, `${entry.w}: collocation has no Arabic letters`);
      assert.match(gloss, harakat, `${entry.w}: collocation has no reading marks`);
      collocations++;
    }
  }
}

assert.equal(examples, 14_596);
assert.equal(collocations, 24_722);
console.log(`Verified ${examples.toLocaleString()} Arabic examples and ${collocations.toLocaleString()} Arabic collocations.`);
