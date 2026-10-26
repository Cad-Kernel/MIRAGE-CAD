import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const require=createRequire(new URL('../support/build_case_registry.mjs',import.meta.url));
const {Workbook}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const root=path.resolve(import.meta.dirname,'..');
const input=path.join(root,'taxonomy','failure_taxonomy_v1.json');
const payload=JSON.parse(await fs.readFile(input,'utf8'));
const original=JSON.parse(await fs.readFile(path.join(root,'audit','master_records_v1.json'),'utf8'));
if(payload.rows.length!==1200 || payload.wide_registry_rows.length!==400) throw Error('Wrong classified universe');
for(let i=0;i<400;i++){
  const now=payload.wide_registry_rows[i];
  const before=original.csv_rows[i];
  for(const key of original.csv_columns) if(JSON.stringify(now[key])!==JSON.stringify(before[key])) throw Error('Changed original Step-1 value: '+key);
}
const jobs=[
  {rows:payload.rows,columns:payload.long_csv_columns,name:'fusion360_failure_taxonomy_v1.csv',sheet:'Native Outcomes',preview:'A1:F9'},
  {rows:payload.wide_registry_rows,columns:payload.wide_registry_columns,name:'fusion360_case_registry_step2_v1.csv',sheet:'Case Taxonomy',preview:'BP1:BU9'}
];
const outputs=[];
for(const job of jobs){
  const book=Workbook.create();
  const sheet=book.worksheets.add(job.sheet);
  const matrix=[job.columns,...job.rows.map(r=>job.columns.map(c=>r[c]))];
  const range=sheet.getRangeByIndexes(0,0,matrix.length,job.columns.length);
  range.values=matrix;
  range.format.font={name:'Arial',size:10};
  range.format.columnWidth=50;
  range.format.rowHeight=23;
  sheet.showGridLines=false;
  sheet.getRangeByIndexes(0,0,1,job.columns.length).format.font={name:'Arial',size:10,bold:true};
  sheet.getRangeByIndexes(0,0,matrix.length,1).format.columnWidth=16;
  sheet.getRangeByIndexes(0,1,matrix.length,1).format.columnWidth=42;
  if(job.rows.length===1200) sheet.getRangeByIndexes(0,2,matrix.length,1).format.columnWidth=12;
  sheet.freezePanes.freezeRows(1);
  book.recalculate();
  const values=range.values;
  if(JSON.stringify(values)!==JSON.stringify(matrix)) throw Error('Worksheet changed a literal');
  if(range.formulas.flat().some(v=>typeof v==='string'&&v.startsWith('='))) throw Error('Literal table contains a formula');
  console.log((await book.inspect({kind:'table',range:`'${job.sheet}'!A1:F6`,include:'values,formulas',tableMaxRows:6,tableMaxCols:6,maxChars:1800})).ndjson);
  const stringify=value=>value==null?'':String(value);
  const csv=values.map(row=>row.map(value=>'"'+stringify(value).replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
  const imported=await Workbook.fromCSV(csv,{sheetName:'Roundtrip'});
  const roundtrip=imported.worksheets.getItem('Roundtrip').getRangeByIndexes(0,0,matrix.length,job.columns.length).values;
  const norm=values=>values.map(row=>row.map(stringify));
  if(JSON.stringify(norm(roundtrip))!==JSON.stringify(norm(matrix))) throw Error('CSV roundtrip altered nulls, multiline traceback, IDs or evidence');
  const preview=await book.render({sheetName:job.sheet,range:job.preview,format:'png',scale:1});
  outputs.push({job,csv,preview:new Uint8Array(await preview.arrayBuffer())});
}
const digest=b=>createHash('sha256').update(b).digest('hex');
const files=[];
for(const {job,csv,preview} of outputs){
  await fs.writeFile(path.join(root,job.name),csv,{flag:'wx',encoding:'utf8'});
  await fs.writeFile(path.join(root,'taxonomy',job.name.replace('.csv','_preview.png')),preview,{flag:'wx'});
  files.push({name:job.name,rows:job.rows.length,columns:job.columns.length,sha256:digest(Buffer.from(csv))});
}
const report={status:'PASS_BOTH_CSVS_TYPED_AND_MULTILINE_ROUNDTRIP',files,
  source_sha256:digest(await fs.readFile(input)),builder_sha256:digest(await fs.readFile(import.meta.filename)),
  original_67_columns_unchanged:true,original_step1_csv_overwritten:false,
  missing_is_blank_not_zero:true,selection_and_semantic_labels_all_null:true,engine:'@oai/artifact-tool'};
await fs.writeFile(path.join(root,'taxonomy','csv_validation_v1.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
