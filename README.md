# Amazon Listing Auditor

一个独立的 Amazon listing QA workflow，用 Google Sheet、人工输入和内部 ERP 资料交叉检查已完成的 MegaPC / JTD customized listings。这个仓库只负责审核，不属于 `create-custom-pc-listing`。

## v0.2 审核范围

- 输入方式：Google Sheet、CSV export，或人工提供内部编号（如 `VL-1249`）、产品名称与 Amazon URL。
- Amazon evidence：Title、bullets、Product Description，以及 Product information 中的 Additional details、Display、Connectivity、Ports & Slots、Processor、Item details、Memory、Battery、Input Devices、Customizations 等区域。
- ERP cross-check：通过内部编号查询 ERP GraphQL；本地也支持 ERP CSV / JSON export。
- 检查类型：品牌/型号上下文不对应、CPU/显示/内存/储存/OS/功能规格冲突、ERP 与输入冲突、证据不足，以及需要人工确认的 compliance claims。
- 抓取失败或资料不足时标记为 `REVIEW`，不会误报成 `PASS`。

## Excel output

每次运行最后生成 `reports/listing-audit-review.xlsx`。主表“问题清单”只包含有错误或有歧义的项目；已经确认无问题的 listing 不会进入主表。

主要字段包括：

- 严重程度与问题类型
- 产品名称、内部编号、Seller、ASIN
- 影响位置 / 字段
- 错误或歧义内容
- 已核实 / 预期内容
- 建议修改内容与问题说明
- Amazon、Input 与 ERP reference
- 证据摘录
- 人工审核状态、最终修改 / 备注、审核人与日期

第二个 tab `Source Evidence` 保存 Amazon 与 ERP 的字段级 evidence，便于后续人工复查。

## 已固化的回归案例

内部编号 `VL-1249` 的产品是 Dell 15 DC15250，但 ASIN `B0HBDTJNJV` 的描述写成 Lenovo ThinkPad X1 Carbon Gen 13，同时 CPU、屏幕尺寸、分辨率与刷新率均不一致。测试要求系统必须发现身份和具体规格 mismatch，并把 warranty validity claim 送入 compliance review。

## 本地运行

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
pytest

listing-auditor audit \
  --input examples/completed-listings.csv \
  --fixtures fixtures/listings \
  --erp-export fixtures/erp/products.json \
  --out reports
```

人工输入：

```bash
listing-auditor audit \
  --internal-id "VL-1249" \
  --product-name "Dell 15 DC15250 / Laptop / 15.6 inch / Intel Core i7-1355U" \
  --amazon-url "https://www.amazon.com/dp/B0HBDTJNJV" \
  --seller "MegaPC" \
  --erp-export fixtures/erp/products.json \
  --out reports
```

## GitHub Actions workflow

在 Actions 中运行 `Audit completed listings`：

1. 选择 `sheet` 或 `manual` input mode。
2. Sheet mode 可输入 URL，或设置 repository variable `AUDIT_SHEET_URL`。
3. Manual mode 填写内部编号、产品名称和 Amazon URL。
4. 如启用 ERP，设置 repository variable `ERP_GRAPHQL_URL`，并通过 GitHub Secrets 提供 `ERP_AUTH_TOKEN` 或 `ERP_ADMIN_SECRET`。不要把 ERP credential 写入公开仓库。
5. 运行结束后下载 artifact `amazon-listing-audit-output`；其中 `listing-audit-review.xlsx` 是最终人工复核 output。

Amazon 可能返回 bot challenge。此时 workflow 会记录 `REVIEW`；production 使用时可接 approved browser/provider 或上传已授权采集的 evidence fixture。

## Compliance 说明

当前规则只把需要 substantiation 的 warranty / absolute claims 标记为人工复核，不作法律判断。后续可以把正式 Amazon policy 与企业内部规则维护成 versioned rule pack。

详细设计见 [docs/architecture.md](docs/architecture.md)。
