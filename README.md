# Amazon Listing Auditor

一个独立的 Amazon listing QA workflow，用 Google Sheet、人工输入和内部 ERP 资料交叉检查已完成的 MegaPC / JTD customized listings。这个仓库只负责审核，不属于 `create-custom-pc-listing`。

## v0.6 审核范围

- 输入方式：Google Sheet、CSV export、人工提供内部编号（如 `VL-1249`）与产品名称，或只提供一个 Amazon URL。
- Amazon evidence：Title、bullets、Product Description、Product information，以及 MAIN / PT01–PT08 图片 URL。
- ERP cross-check：通过内部编号查询 ERP GraphQL；本地也支持 ERP CSV / JSON export。
- 规格检查：品牌/型号上下文不对应、CPU/显示/内存/储存/OS/功能规格冲突，以及 ERP 与输入冲突。
- Compliance 检查：seller-brand-first、Customized / Created Using、RAM/储存、第一条 warranty、只允许 RAM/储存 customization、绝对化 claim 等规则。
- 图片检查：格式、尺寸、zoom、正方形、MAIN 白底与构图、重复图；再结合 OCR/视觉或人工 observation 检查错误 OEM/型号、图片 claims、价格/评价/Amazon 标识、联系方式、端口/配件、素材授权等。
- 文案修改建议：当 Title、Bullet Points 或 Product Description 存在问题时，按 generation 项目既有 style 输出三组可人工复核的建议文案。
- 抓取失败或资料不足时标记为 `REVIEW`，不会误报成 `PASS`。

## Excel output

Windows 本地运行默认保存到 `C:\Users\<当前用户>\OneDrive\Desktop\Listing Check\<内部编号>\`。例如 `VL-1249` 的文件会进入 `Listing Check\VL-1249\`。主表“问题清单”只包含有错误或有歧义的项目；已经确认无问题的 listing 不会进入主表。

每个产品文件夹包含：

- `listing-audit-review.xlsx`
- `report.json`
- `report.csv`
- `report.md`
- `source-evidence.json`

同一内部编号下的 MegaPC 和 JTD listing 会合并在同一个产品包中。URL-only 输入在尚未映射内部编号时保存到 `UNMAPPED-<ASIN>`；补充内部编号后会按 `VL-XXXX` 输出。使用 `--out` 或环境变量 `LISTING_CHECK_OUTPUT_ROOT` 可以覆盖根目录。

主要字段包括：

- 严重程度、问题类型、Rule ID / Reference
- 产品名称、内部编号、Seller、ASIN
- 影响位置 / 字段
- 错误或歧义内容
- 已核实 / 预期内容
- 建议修改内容与问题说明
- Amazon、Input 与 ERP reference
- 证据摘录
- 人工审核状态、最终修改 / 备注、审核人与日期

第二个 tab `Source Evidence` 保存 Amazon 与 ERP 的字段级 evidence，便于后续人工复查。

Title、Bullet Points、Product Description 的建议分别以 `STYLE-TITLE-001`、`STYLE-BULLET-001`、`STYLE-DESC-001` 写入问题清单。建议只使用已映射的 Input/ERP 事实；缺少的必要信息显示为 `[[VERIFY ...]]`，包含该标记的文案不能直接发布。

## 已固化的回归案例

内部编号 `VL-1249` 的产品是 Dell 15 DC15250，但 ASIN `B0HBDTJNJV` 的描述写成 Lenovo ThinkPad X1 Carbon Gen 13，同时 CPU、屏幕尺寸、分辨率与刷新率均不一致。测试要求系统必须发现身份和具体规格 mismatch，并把 warranty validity claim 送入 compliance review。

## 本地运行

本地可复现环境固定为 **Python 3.11**，使用独立 Conda environment；不要修改 Anaconda `base`。完整的环境检测、安装授权与 Jupyter kernel 流程见 [`docs/local-python-workflow.md`](docs/local-python-workflow.md)。

每次运行或调试前先执行只读预检：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight-local.ps1
```

如果 Conda 不在 `PATH` 或安装在非标准目录，再显式提供路径。例如当前这台电脑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight-local.ps1 `
  -CondaExe "E:\Coding\Scripts\conda.exe" `
  -EnvironmentPath "E:\Coding\envs\amazon-listing-auditor-py311"
```

如果 Python、Conda、environment 或依赖缺失，必须停止审核，说明缺失项并提供官方 Python/Anaconda 下载地址；在安装、创建或修复本地环境前，必须另行取得用户明确许可。

预检通过后：

```powershell
& "E:\Coding\envs\amazon-listing-auditor-py311\python.exe" -m pytest

& "E:\Coding\envs\amazon-listing-auditor-py311\Scripts\listing-auditor.exe" audit `
  --input examples/completed-listings.csv `
  --fixtures fixtures/listings `
  --erp-export fixtures/erp/products.json `
  --image-observations references/image-observations.example.json `
  --out reports
```

Jupyter Notebook/Lab 中选择 kernel **Python 3.11 (Amazon Listing Auditor)**；可运行 [`notebooks/environment-check.ipynb`](notebooks/environment-check.ipynb) 验证版本与依赖。

人工输入：

```powershell
& "E:\Coding\envs\amazon-listing-auditor-py311\Scripts\listing-auditor.exe" audit `
  --internal-id "VL-1249" `
  --product-name "Dell 15 DC15250 / Laptop / 15.6 inch / Intel Core i7-1355U" `
  --amazon-url "https://www.amazon.com/dp/B0HBDTJNJV" `
  --seller "MegaPC" `
  --erp-export fixtures/erp/products.json `
  --out reports
```

## URL-only 输入

只有 Amazon URL 时也可以运行完整的页面、Compliance 与图片审核：

```bash
listing-auditor audit \
  --amazon-url "https://www.amazon.com/dp/B0HBDTJNJV" \
  --seller "MegaPC" \
  --out reports
```

省略 `--out` 时，Windows 默认输出到 OneDrive Desktop 的 `Listing Check`；GitHub Actions 仍明确使用 `reports` 并上传所有内部编号子目录。

URL-only 模式会用抓取到的 Amazon Title 作为 Excel 中的产品名称，并加入 `INPUT-BASELINE-001 / REVIEW`。这表示页面本身已完成审核，但由于没有内部编号和标准产品资料，尚不能确认 Amazon 产品是否与 ERP 中的具体产品完全对应。之后补充内部编号与产品名称即可执行完整 mismatch 检查。

## GitHub Actions workflow

在 Actions 中运行 `Audit completed listings`：

1. Workflow 在临时 runner 中配置 Python 3.11，安装项目并执行两次版本/依赖检查；不会使用或修改用户电脑上的 Conda 环境。
2. 选择 `sheet`、`manual` 或 `url` input mode。
3. Sheet mode 可输入 URL，或设置 repository variable `AUDIT_SHEET_URL`。
4. Manual mode 填写内部编号、产品名称和 Amazon URL；URL mode 只需 Amazon URL，Seller 可选。
5. 如启用 ERP，设置 repository variable `ERP_GRAPHQL_URL`，并通过 GitHub Secrets 提供 `ERP_AUTH_TOKEN` 或 `ERP_ADMIN_SECRET`。不要把 ERP credential 写入公开仓库。
6. 默认开启图片审核；可在仓库中提供 `image-observations JSON` 路径完成 OCR/视觉或人工语义复核。
7. 运行结束后下载 artifact `amazon-listing-audit-output`；其中按内部编号分文件夹保存 Excel 与其他审核产出。

Amazon 可能返回 bot challenge。此时 workflow 会记录 `REVIEW`；production 使用时可接 approved browser/provider 或上传已授权采集的 evidence fixture。

## 图片语义复核输入

纯像素规则不能可靠判断图片是不是正确型号、端口是否对应、图片文字是否真实或素材是否获得授权。因此按 `listings.<ASIN>.images` 结构，在 `references/image-observations.example.json` 中为各图片提供 observation；一个文件可以安全覆盖 Sheet 中的多个 listing。未提供或找不到对应 ASIN 时会生成 `IMG-VISUAL-001 / REVIEW`，不会把技术检查通过误当作完整 PASS。

## Compliance 说明

本仓库保存了从 generation 项目中适配出的 versioned audit rule pack：`references/compliance-audit-rules.md` 与 `references/image-audit-rules.md`。它们用于内部 QA，不替代 Amazon 当前政策或法律判断。

文案建议遵循 `references/listing-copy-style.md`，该文件适配自 `create-custom-pc-listing/references/listing-style-guide.md` 与 `compliance-rules.md`。

详细设计见 [docs/architecture.md](docs/architecture.md)。
