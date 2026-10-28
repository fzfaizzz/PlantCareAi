import { access, readdir, stat } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
const source = readFileSync(new URL('../src/data/plantAssets.js', import.meta.url), 'utf8');
const names = [...source.matchAll(/'([a-z]+(?:-[a-z]+)+)'/g)].map(match => match[1]);
let bytes = 0;
for (const name of names) {
 const file = new URL(`../public/assets/plants/${name}.webp`, import.meta.url);
 await access(file); const info=await stat(file); if(!info.size) throw new Error(`Empty asset: ${name}`); bytes+=info.size;
}
console.log(`Verified ${names.length} real botanical assets (${(bytes/1024/1024).toFixed(2)} MB total).`);
