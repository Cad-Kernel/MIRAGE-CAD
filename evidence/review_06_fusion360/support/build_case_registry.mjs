import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { Workbook } from '@oai/artifact-tool';

const root=path.resolve(import.meta.dirname,'..');
const input=path.join(root,'audit','master_records_v1.json');
const source=JSON.parse(await fs.readFile(input,'utf8'));
const rows=source.csv_rows;
const columns=source.csv_columns;
if(rows.length!==400 || new Set(rows.map(r=>r.sample_id)).size!==400) throw Error('Master is not 400 unique IDs');
if(rows.some((r,i)=>r.master_index!==i+1)) throw Error('Master order changed');
if(rows.some(r=>r.verified_failure_class!==null||r.failure_evidence!==null||r.selection_bucket!==null)) throw Error('Step 2/3 fields must remain null');
const matrix=[columns,...rows.map(r=>columns.map(c=>r[c]))];
const workbook=Workbook.create();
const sheet=workbook.worksheets.add('Fusion360 Cases');
const range=sheet.getRangeByIndexes(0,0,matrix.length,columns.length);
range.values=matrix;
range.format.font={name:'Arial',size:10};
range.format.columnWidth=32;
range.format.rowHeight=23;
sheet.getRange('A1:A401').format.columnWidth=16;
sheet.getRange('B1:B401').format.columnWidth=43;
sheet.getRange('C1:C401').format.columnWidth=40;
sheet.getRange('D1:D401').format.columnWidth=17;
sheet.getRangeByIndexes(0,0,1,columns.length).format.font={name:'Arial',size:10,bold:true};
sheet.showGridLines=false;
sheet.freezePanes.freezeRows(1);
workbook.recalculate();
const values=range.values;
if(JSON.stringify(values)!==JSON.stringify(matrix)) throw Error('Typed worksheet differs from source');
if(range.formulas.flat().some(x=>typeof x==='string'&&x.startsWith('='))) throw Error('Registry must be literal data');
console.log((await workbook.inspect({kind:'table',range:"'Fusion360 Cases'!A1:D9",include:'values,formulas',tableMaxRows:9,tableMaxCols:4,maxChars:1800})).ndjson);
const preview=await workbook.render({sheetName:'Fusion360 Cases',range:'A1:D9',format:'png',scale:1});
await fs.writeFile(path.join(root,'support','case_registry_preview.png'),new Uint8Array(await preview.arrayBuffer()),{flag:'wx'});
const string=value=>value==null?'':String(value);
const csv=values.map(row=>row.map(value=>'"'+string(value).replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
const roundtrip=await Workbook.fromCSV(csv,{sheetName:'Roundtrip'});
const restored=roundtrip.worksheets.getItem('Roundtrip').getRangeByIndexes(0,0,matrix.length,columns.length).values;
const norm=values=>values.map(row=>row.map(string));
if(JSON.stringify(norm(restored))!==JSON.stringify(norm(matrix))) throw Error('CSV changed ID/path/metric/missing-value semantics');
const target=path.join(root,'fusion360_case_registry.csv');
await fs.writeFile(target,csv,{encoding:'utf8',flag:'wx'});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const validation={status:'PASS_CSV_LITERAL_VALUES_AND_ROUNDTRIP',created_utc:new Date().toISOString(),
  rows:400,columns:columns.length,master_order_unchanged:true,taxonomy_and_selection_fields_all_blank:true,
  null_is_blank_not_zero:true,source_sha256:sha(await fs.readFile(input)),csv_sha256:sha(Buffer.from(csv)),
  builder_sha256:sha(await fs.readFile(import.meta.filename)),engine:'@oai/artifact-tool',
  preview:'Worksheet ID columns only; not a CAD rendering or case selection'};
await fs.writeFile(path.join(root,'audit','csv_validation_v1.json'),JSON.stringify(validation,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(validation));
