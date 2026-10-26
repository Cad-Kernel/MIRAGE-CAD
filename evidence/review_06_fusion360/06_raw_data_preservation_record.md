> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Fusion 360 Raw Data Preservation v1

Date: 2026-10-22. Status: COMPLETE_BYTE_EXACT_REGISTERED_SOURCE_ARCHIVE.

## Preserved Scope

`raw_archive_v1/archive_manifest_v1.json` 完整登记了 Step 1 审计的 **6,834 个原始路径**：

- **6,653 个确实存在的源文件**已逐字节复制，并逐份验证原始/归档 SHA256。
- 内容去重后 **5,039 个对象，170,729,801 bytes，约 162.82 MiB**。
- **181 个原本缺失的路径**继续登记为缺失，没有伪造 candidate STEP。
- 400 个原始 test IDs 全部保留，不仅是本轮 18 个选图 ID。

包括已登记的完整输入/预测/IR JSONL、reference STEP、point inputs、descriptor、
成功的 prediction STEP、CAD-Recode raw generation / extracted code、原生执行结果、
stdout/stderr、原 gate/export/geometry manifests 和相关复现来源。空日志也原样保留。
完整 JSONL 中非选中样本的记录没有裁掉。

manifest 每项保留 original path、roles、exists、bytes、SHA256、历史 hash 检查及
archive_path。对象采用 `objects/<sha256><extension>` 命名，不能仅靠文件名猜它的用途；
用 manifest 或逐例 `archived_asset_paths.json` 回溯。

## Explicit Limits

这不是全部 100K training corpus、全部训练权重/环境、或全部 1,725 个官方 Fusion 360
test objects 的完整备份。早期 manifest 中本来就不存在的临时/占位 mesh 路径没有被
当作已保存的原始 metric mesh。此次新建的 NPZ 是 display-only tessellation，
不是伪称找回了历史评分用 mesh。

原始源路径未改动。此前 Review/04、05、06 Step 1/2 的封存文件未覆盖。
本轮选择/相机/变换/PNG/CSV/观察记录另有 `gallery_v1/gallery_archive_seal_v1.json`。

## Later Paper Formatting

主编要求减少图或页数时，只减少论文引用的候选图，不删除完整 research archive。
改变字体、panel 布局、列序、图注或颜色时，另存如 `submission_layout_v2/`，
并链接本轮不带文字的独立视图与原始数据。原图、原数值、原错误、旧规则和旧版本保留。
新增作者审核也应另存记录，不覆盖封存的 provisional observations。

## Retrieval Order

1. `START_HERE.md` / `gallery_v1/index.html` 定位 case。
2. `fusion360_gallery_cases_v1.csv` 查 18 个候选和选择理由。
3. `fusion360_gallery_assets_v1.csv` 查 72 个 method/case 的 raw STEP、NPZ、PNG 和日志。
4. `gallery_v1/cases/<case_id>/archived_asset_paths.json` 查逐例原始路径及字节副本。
5. `raw_archive_v1/archive_manifest_v1.json` 查完整 400 例所登记源文件。
6. `audit/master_records_v1.json` / `taxonomy/evidence_v1/` 追溯物理 JSONL 行号和原生证据。
