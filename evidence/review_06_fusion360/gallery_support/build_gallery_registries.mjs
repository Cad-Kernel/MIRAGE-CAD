import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const require = createRequire(new URL('../support/build_case_registry.mjs',import.meta.url));
const { Workbook } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const root=path.resolve(import.meta.dirname,'..');
const gallery=path.join(root,'gallery_v1');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const source=await read(path.join(gallery,'selection_v1.json'));
const archive=await read(path.join(root,'raw_archive_v1','archive_manifest_v1.json'));
const mapping=new Map(archive.sources.map(x=>[x.path,x]));
const cases=[];
const assets=[];
for(const c of source.cases){
  const base=path.join(gallery,'cases',c.case_id);
  const render=await read(path.join(base,'render_manifest.json'));
  cases.push({slot:c.slot,placement:c.placement,sample_id:c.sample_id,selection_bucket:c.selection_bucket,
    cohort_size:c.cohort_size,selected_priority_rank:c.selected_priority.priority_rank,selection_rule:c.selection_rule,
    mirage_CD_x1000:c.master.view.mirage_CD,mirage_IoU:c.master.view.mirage_IoU,
    cadr_CD_x1000:c.master.view.cadr_CD,cadr_IoU:c.master.view.cadr_IoU,
    nn_CD_x1000:c.master.view.nn_CD,nn_IoU:c.master.view.nn_IoU,
    case_record_path:path.join(base,'case_record.json'),archived_asset_paths:path.join(base,'archived_asset_paths.json'),
    shape_normalized_panel:render.panels.metric_space.path,reference_world_panel:render.panels.reference_world.path,
    camera_and_transform_record:path.join(base,'render_manifest.json'),
    visual_review_record:path.join(gallery,'visual_review_v1.json'),author_confirmation:'PENDING'});
  for(const method of ['reference','cadr','mirage','nn']){
    const mesh=await read(path.join(base,`${method}_mesh.json`));
    const native=c.taxonomy[method];
    const sourcePath=c.master.assets[method==='reference'?'reference':`${method}_step`];
    const original=mapping.get(sourcePath);
    const find=(series,view)=>render.renders.find(r=>r.series===series&&r.view===view&&r.method===method).path;
    assets.push({slot:c.slot,sample_id:c.sample_id,method,selection_bucket:c.selection_bucket,
      historical_outcome:native?.primary_outcome??'REFERENCE',native_reason_subtype:native?.reason_subtype??null,
      CD_scoreable:native?.cd_scoreable??null,IoU_scoreable:native?.iou_scoreable??null,
      CD_x1000:native?.CD??null,IoU:native?.IoU??null,
      original_step_path:sourcePath,archived_step_path:original.exists?path.join(root,'raw_archive_v1',original.archive_path):null,
      original_step_sha256:original.sha256,render_status:mesh.status,mesh_npz_path:mesh.mesh_path??null,
      native_mesh_record:path.join(base,`${method}_mesh.json`),
      normalized_isometric:find('metric_space','isometric'),normalized_front:find('metric_space','front'),
      world_isometric:find('reference_world','isometric'),world_front:find('reference_world','front'),
      camera_and_transform_record:path.join(base,'render_manifest.json'),
      native_failure_evidence:native?.failure_evidence??null,
      original_prediction_path:method==='reference'?null:method==='cadr'?c.master.view.cadr_prediction_path:c.master.view[`${method}_prediction_path`],
      original_log_path:method==='reference'?null:c.master.view[`${method}_log_path`],
      archived_asset_paths:path.join(base,'archived_asset_paths.json'),
      visual_review_record:path.join(gallery,'visual_review_v1.json'),author_confirmation:'PENDING'});
  }
}
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const validation=[];
for(const [name,rows,sheetName] of [
  ['fusion360_gallery_cases_v1.csv',cases,'Selected Cases'],
  ['fusion360_gallery_assets_v1.csv',assets,'Render Assets']]){
  const columns=Object.keys(rows[0]);
  const matrix=[columns,...rows.map(r=>columns.map(c=>r[c]))];
  const book=Workbook.create();
  const sheet=book.worksheets.add(sheetName);
  const range=sheet.getRangeByIndexes(0,0,matrix.length,columns.length);
  range.values=matrix;
  range.format.font={name:'Arial',size:10};
  range.format.columnWidth=35;
  range.format.rowHeight=24;
  sheet.getRangeByIndexes(0,0,matrix.length,1).format.columnWidth=12;
  sheet.getRangeByIndexes(0,1,matrix.length,1).format.columnWidth=name.includes('cases')?17:41;
  sheet.getRangeByIndexes(0,2,matrix.length,1).format.columnWidth=name.includes('cases')?41:20;
  sheet.getRangeByIndexes(0,3,matrix.length,1).format.columnWidth=38;
  sheet.getRangeByIndexes(0,0,1,columns.length).format.font={name:'Arial',size:10,bold:true};
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines=false;
  book.recalculate();
  if(JSON.stringify(range.values)!==JSON.stringify(matrix))throw Error('Typed worksheet changed literal values');
  if(range.formulas.flat().some(x=>typeof x==='string'&&x.startsWith('=')))throw Error('Literal registry contains formulas');
  console.log((await book.inspect({kind:'table',range:`'${sheetName}'!A1:D7`,include:'values,formulas',tableMaxRows:7,tableMaxCols:4,maxChars:1600})).ndjson);
  const preview=await book.render({sheetName,range:'A1:D7',format:'png',scale:1});
  await fs.writeFile(path.join(gallery,name.replace('.csv','_preview.png')),new Uint8Array(await preview.arrayBuffer()),{flag:'wx'});
  const str=v=>v==null?'':String(v);
  const csv=range.values.map(row=>row.map(v=>'"'+str(v).replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
  const roundtrip=await Workbook.fromCSV(csv,{sheetName:'Roundtrip'});
  const restored=roundtrip.worksheets.getItem('Roundtrip').getRangeByIndexes(0,0,matrix.length,columns.length).values;
  const normalize=m=>m.map(r=>r.map(str));
  if(JSON.stringify(normalize(restored))!==JSON.stringify(normalize(matrix)))throw Error('CSV roundtrip changed source');
  await fs.writeFile(path.join(root,name),csv,{flag:'wx'});
  validation.push({file:name,rows:rows.length,columns:columns.length,sha256:sha(Buffer.from(csv)),literal_roundtrip:'PASS',nulls_are_blank:true});
}
await fs.writeFile(path.join(gallery,'csv_validation_v1.json'),JSON.stringify({status:'PASS',engine:'@oai/artifact-tool',files:validation,builder_sha256:sha(await fs.readFile(import.meta.filename))},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(validation));
