# Amazon Listing Auditor

一个独立、可复查的 listing QA 工具：从 Google Sheet 读取已经完成的 MegaPC / JTD customized listings，提取预期产品身份，再与 Amazon 页面证据和官方资料进行比对，找出 product identity、型号和关键规格不一致的问题。

> 这个仓库只负责审核，和 listing generation 项目完全分离。

## 当前 MVP 能做什么

- 读取 `Listing Status Tracker` 导出的 CSV，自动挑选状态为 `Completed` 的 MegaPC 与 JTD 链接。
- 比较品牌、型号、屏幕尺寸、分辨率、CPU、触控与刷新率等字段。
- 把 `brand/model` 错配标为 `CRITICAL`，关键规格冲突标为 `HIGH`，证据不足标为 `REVIEW`。
- 输出 JSON、CSV 和便于人工 review 的 Markdown 报告。
- 支持本地 HTML/JSON evidence fixtures；Amazon 拦截自动抓取时不会误报为通过。
- GitHub Actions 可以手动运行审核，并把报告保存为 artifact。

## 已固化的首个回归案例

Sheet 中 `B0HBDTJNJV` 的预期产品是 **Dell 15 DC15250**，但采集到的 listing description 写的是 **Lenovo ThinkPad X1 Carbon Gen 13**。测试要求系统必须同时发现品牌和型号错配。

## 快速开始

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
pytest
listing-auditor audit \
  --input examples/completed-listings.csv \
  --fixtures fixtures/listings \
  --out reports
```

打开 `reports/report.md` 查看结果。示例数据只用于演示规则，不代表完整 production audit。

## 用 Google Sheet 运行

```bash
listing-auditor audit \
  --sheet-url "YOUR_GOOGLE_SHEET_URL" \
  --out reports
```

当前版本使用 Google Sheets CSV export endpoint。Sheet 必须允许运行者读取；私有 Sheet 后续可接 Google service account。GitHub Actions 的 `Audit completed listings` workflow 会优先使用手动输入的 `sheet_url`，否则读取 repository variable `AUDIT_SHEET_URL`。

## Evidence 优先级

1. Amazon 当前 listing 页面中的 title、bullets、product description、detail table
2. 制造商官方产品页或官方 specification / manual
3. 内部 catalog / source sheet
4. 搜索摘要仅用于发现线索，不可单独作为最终结论

每条 mismatch 都必须保留：字段、预期值、listing 值、severity、证据来源和简短原因。抓取失败或证据不足会输出 `REVIEW`，不会显示成 `PASS`。

## Production roadmap

- Google service-account / OAuth 读取私有 Sheet
- 可插拔的浏览器或 approved product-data provider，减少 Amazon bot challenge
- 官方厂商 source adapters 与 source citation cache
- 变体级比较、图片 OCR、容量组合检查
- 将审核结果写回单独 QA Sheet / 创建 GitHub Issue（需要显式开启）
- 人工确认队列和 false-positive suppression

详细设计见 [docs/architecture.md](docs/architecture.md)。

