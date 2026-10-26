> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 原始数据保留记录

日期：2026-10-22。

## 保留原则

完整研究资料与论文展示分开管理。主编要求压缩篇幅时，只精简论文选图或另存的
投稿子集，不删除完整原始资料、失败案例、原始预测、历史指标或来源记录。

这次在 `raw_archive_v1/` 新增原始资料的逐字节副本，而不只是登记外部路径。
原始文件、原 CSV、已有案例文件、渲染结果与封存清单均不修改。

## 范围

1. 已登记的 55 个完整来源文件，包括原始及各处理阶段的 plan/code JSONL、
   四模态 gate/geometry 明细与汇总、train/val/test JSONL、相关脚本和元数据。
2. 24 个案例、22 个独立目标对象的 8 类原始资产：STEP、点云 NPZ、输入 PNG、
   STEP descriptor、原始 IR、原始程序、feature tree、metadata。
3. 来源审计中已经登记的当前 checkpoint 观察文件也按原字节保存，但仍标记为
   current observation，不把它们改写成历史训练时使用权重的证明。
4. 原始路径与归档副本的映射、文件大小、SHA256 以及每个 case/role 的关联。

这不是全量 100K corpus 或全部实验权重的异地备份。完整数据集与各实验输出仍应
在原目录保留。JSONL 中未选样本引用的所有外部资产并未全量复制。

## 查询入口

从 [原始资料归档入口](__EVIDENCE_SOURCE_ROOT__/05_qualitative/raw_archive_v1/index.html)
查看。它链接到归档后的 reference/input 原始文件，并可打开同一 05 文件夹中的
案例文本和现有两视角图，不需要靠 WSL 原路径才能读取这批案例的原始资产。

- `raw_archive_v1/archive_plan.json`：原始路径、预期哈希与实际副本映射。
- `raw_archive_v1/archive_actuals.json`：最终文件数量、字节数和封存检查结果。
- `raw_archive_v1/archive_manifest.json`：新归档文件的 SHA256 清单。
- `raw_archive_v1/README.md`：保留政策、数据范围和限制。

归档采用按内容哈希去重的对象目录，文件不做清洗、截断、重编码、压缩重写或格式
转换。原始文本文件的空白和换行也按字节保留；原有提取版和原始版不混为一谈。

应保留整个 `05_qualitative` 文件夹，而不只保留 figure PNG。后期需要少量主文图时，
从这一完整资料库另行挑选、排版和导出，不覆盖完整资料库。
