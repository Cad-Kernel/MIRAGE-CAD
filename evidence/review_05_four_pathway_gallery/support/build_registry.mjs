import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { Workbook } from '@oai/artifact-tool';

const root = path.resolve(import.meta.dirname, '..');
const schema = JSON.parse(await fs.readFile(path.join(root, 'qualitative_case_registry.schema.json'), 'utf8'));
const columns = Object.keys(schema.properties);
if (process.argv.includes('--populate-candidates')) {
  await populateCandidates();
  process.exit(0);
}
const workbook = Workbook.create();
if (process.argv.includes('--discover')) {
  console.log(workbook.help('*', {search: 'CSV|csv', include: 'index,examples,notes', maxChars: 4000 }).ndjson);
  process.exit(0);
}
const sheet = workbook.worksheets.add('Cases');
sheet.getRangeByIndexes(0, 0, 1, columns.length).values = [columns];
sheet.getRangeByIndexes(0, 0, 1, columns.length).format.columnWidth = 32;
sheet.getRangeByIndexes(0, 0, 1, columns.length).format.font = {name: 'Arial', size: 10};
sheet.showGridLines = false;
workbook.recalculate();
console.log((await workbook.inspect({kind: 'table', range: 'Cases!A1:H1', include: 'values,formulas', tableMaxRows: 1, tableMaxCols: 8})).ndjson);
const preview = await workbook.render({sheetName: 'Cases', range: 'A1:D1', scale: 1, format: 'png'});
await fs.writeFile(path.join(import.meta.dirname, 'registry_header_preview.png'), new Uint8Array(await preview.arrayBuffer()));
const header = sheet.getRangeByIndexes(0, 0, 1, columns.length).values[0];
if (JSON.stringify(header) !== JSON.stringify(columns)) throw new Error('Header/schema mismatch');
// CSV is a raw-data export. Serialize verified worksheet values using RFC4180 quoting.
const csv = header.map(value => '"' + String(value).replaceAll('"', '""') + '"').join(',') + '\r\n';
await fs.writeFile(path.join(root, 'qualitative_case_registry.csv'), csv, {encoding: 'utf8', flag: 'wx'});
console.log(JSON.stringify({columns: columns.length, rows: 0, schema: 'urn:mirage:qualitative-case:v1'}));

async function populateCandidates() {
  const inputPath = path.join(root, 'selection', 'candidate_rows_v1.json');
  const csvPath = path.join(root, 'qualitative_case_registry.csv');
  const payload = JSON.parse(await fs.readFile(inputPath, 'utf8'));
  const original = await fs.readFile(csvPath);
  const digest = bytes => createHash('sha256').update(bytes).digest('hex');
  if (digest(original) !== payload.registry_before.sha256) throw new Error('Registry changed since extraction; preserve manual edits');
  const workbook = await Workbook.fromCSV(original.toString('utf8'), { sheetName: 'Cases' });
  const sheet = workbook.worksheets.getItem('Cases');
  const header = sheet.getRangeByIndexes(0, 0, 1, columns.length).values[0];
  if (JSON.stringify(header) !== JSON.stringify(columns)) throw new Error('Existing header/schema mismatch');
  const encode = value => Array.isArray(value) ? JSON.stringify(value) : value;
  const matrix = payload.rows.map(row => columns.map(column => encode(row[column])));
  if (matrix.length < 8 || payload.main_candidates !== 8) throw new Error('Expected eight main candidates');
  if (new Set(payload.rows.map(row => row.case_id)).size !== matrix.length) throw new Error('Duplicate case ID');
  if (payload.rows.some(row => row.registry_status !== 'candidate')) throw new Error('Do not mark unrendered cases verified/selected');
  sheet.getRangeByIndexes(1, 0, matrix.length, columns.length).values = matrix;
  const range = sheet.getRangeByIndexes(0, 0, matrix.length + 1, columns.length);
  range.format.font = { name: 'Arial', size: 10 };
  range.format.columnWidth = 32;
  range.format.rowHeight = 24;
  for (const [column, width] of [['A', 64], ['B', 18], ['C', 14], ['D', 16], ['E', 14], ['F', 23]]) {
    sheet.getRange(`${column}1:${column}${matrix.length + 1}`).format.columnWidth = width;
  }
  sheet.showGridLines = false;
  workbook.recalculate();
  const values = range.values;
  if (JSON.stringify(values) !== JSON.stringify([columns, ...matrix])) throw new Error('Typed worksheet values differ from extracted records');
  if (range.formulas.flat().some(value => typeof value === 'string' && value.startsWith('='))) throw new Error('Registry must contain literal data, not formulas');
  console.log((await workbook.inspect({kind:'table', range:'Cases!A1:H9', include:'values,formulas', tableMaxRows:9, tableMaxCols:8, maxChars:3000})).ndjson);
  const preview = await workbook.render({sheetName:'Cases', range:'A1:F9', scale:1, format:'png'});
  await fs.writeFile(path.join(import.meta.dirname, 'registry_candidates_preview.png'), new Uint8Array(await preview.arrayBuffer()));
  // RFC4180 export of verified literal worksheet values; null remains blank, not zero.
  const stringify = value => value == null ? '' : String(value);
  const csv = values.map(row => row.map(value => '"' + stringify(value).replaceAll('"', '""') + '"').join(',')).join('\r\n') + '\r\n';
  const imported = await Workbook.fromCSV(csv, {sheetName:'Roundtrip'});
  const roundtrip = imported.worksheets.getItem('Roundtrip').getRangeByIndexes(0,0,values.length,columns.length).values;
  const expected = values.map(row => row.map(stringify));
  if (JSON.stringify(roundtrip.map(row => row.map(stringify))) !== JSON.stringify(expected)) throw new Error('CSV roundtrip changed a value/null/array/identifier');
  await fs.writeFile(path.join(root,'selection','registry_header_before_v1.csv'), original, {flag:'wx'});
  await fs.writeFile(csvPath, csv, 'utf8');
  const bytes = await fs.readFile(csvPath);
  const report = {created_utc:new Date().toISOString(), status:'PASS_CSV_POPULATED_AND_ROUNDTRIP_VERIFIED',
    rows:matrix.length, columns:columns.length, main_candidates:payload.main_candidates, appendix_candidates:payload.appendix_candidates,
    csv:{path:csvPath, bytes:bytes.length, sha256:digest(bytes)}, input_payload_sha256:digest(await fs.readFile(inputPath)),
    builder_sha256:digest(await fs.readFile(import.meta.filename)), engine:'@oai/artifact-tool',
    arrays:'JSON strings', booleans:'true/false', missing_values:'blank -> null, not zero',
    no_model_CAD_execution:true, no_case_marked_visually_selected:true};
  await fs.writeFile(path.join(import.meta.dirname,'registry_population_v1.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report));
}
