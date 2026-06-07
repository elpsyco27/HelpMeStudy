# study-agent

本地运行的学习笔记整理 Agent，用于把 PDF 课件整理成 Markdown 笔记和复习卡片。

当前项目重点支持两条处理路线：

- 文本路线：读取 PDF 中可复制的文字，清洗、切块，然后调用 LLM 生成笔记和卡片。
- 视觉路线：将 PDF 每页渲染为图片，再调用多模态视觉模型逐页解释课件页面。

## 当前功能

### 已完成

- PDF 上传，并保存到本地 `app/storage/uploads/`
- PDF 文本解析，保留页码
- 文本清洗：去除多余空行、连续空格，尝试合并 PDF 异常断行
- 文本切块：默认约 3000 字符，保留 chunk 来源页码
- 调用 OpenAI-compatible 文本模型生成 Markdown 笔记
- 调用 OpenAI-compatible 文本模型生成复习卡片
- 复习卡片输出 Markdown 表格：

```markdown
| 问题 | 答案 | 易错点 | 来源 |
```

- PDF 页面渲染：使用 PyMuPDF 将每页保存为 PNG
- 逐页图片预览：Streamlit 中展示前 3 页渲染结果
- 多模态视觉模型客户端：支持本地图片转 base64 并调用 OpenAI-compatible 多模态接口
- 逐页视觉解释：每页图片单独调用视觉模型，结果保存为 Markdown
- 已有逐页解释会默认跳过，避免重复调用视觉模型
- 逐页视觉解释支持边处理边更新页面结果
- 将逐页视觉解释合并为完整的多模态 Markdown 笔记
- Streamlit 页面展示文本笔记、复习卡片、逐页视觉解释、多模态笔记，并提供下载按钮

### 进行中 / 下一阶段

- 将“仅文本解析 / 视觉逐页解析 / 文本 + 视觉融合”整理成明确的处理模式
- 优化课件中的公式、表格、流程图和复杂版式理解
- 增加更完整的自动化测试

## 技术栈

- Python
- Streamlit
- PyMuPDF
- OpenAI-compatible API
- Markdown 文件保存

## 环境变量

复制 `.env.example` 为 `.env`，然后填写模型配置。

文本模型配置：

```env
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
```

视觉模型配置：

```env
VISION_API_KEY=
VISION_BASE_URL=
VISION_MODEL=
VISION_API_STYLE=responses
```

说明：

- `LLM_*` 用于生成普通 Markdown 笔记和复习卡片。
- `VISION_*` 用于逐页图片理解。
- `.env` 包含密钥，已被 `.gitignore` 忽略，不要提交到 GitHub。

## 运行方式

安装依赖：

```bash
cd E:\HelpMeStudy\study-agent
python -m venv .venv
pip install -r requirements.txt
```

启动应用：

```bash
cd E:\HelpMeStudy\study-agent
streamlit run web/streamlit_app.py
```

浏览器打开：

```text
http://localhost:8501
```

## 使用流程

### 文本解析路线

1. 上传 PDF。
2. 点击 `解析 PDF`。
3. 点击 `生成 Markdown 笔记`。
4. 点击 `生成复习卡片`。
5. 在页面查看结果，或下载 `note.md` 和 `cards.md`。

### 视觉逐页解析路线

1. 上传 PDF。
2. 设置页面图片缩放倍数，默认 `2.0`。
3. 点击 `将 PDF 渲染为逐页图片`。
4. 页面会展示前 3 页图片预览。
5. 点击 `逐页解释课件图片`。
6. 页面会边处理边展示每页视觉解释，并可下载 `page_vision_notes.md`。
7. 点击 `合并多模态笔记`。
8. 页面会展示完整多模态笔记，并可下载 `multimodal_note.md`。

## Streamlit Cloud 部署

部署入口文件：

```text
web/streamlit_app.py
```

在 Streamlit Cloud 创建应用时：

1. 选择 GitHub 仓库。
2. Branch 选择 `main`。
3. Main file path 填写 `web/streamlit_app.py`。
4. 在应用的 `Settings -> Secrets` 中配置模型密钥。

Secrets 示例：

```toml
LLM_API_KEY = "your-text-model-api-key"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "your-text-model-name"

VISION_API_KEY = "your-vision-model-api-key"
VISION_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
VISION_MODEL = "doubao-seed-2-0-mini-260428"
VISION_API_STYLE = "responses"
```

云部署注意事项：

- 不要提交 `.env`，云端只使用 Streamlit Secrets。
- 当前文件保存目录在云端属于临时存储，应用重启后可能丢失。
- 大 PDF 逐页视觉分析会消耗较多时间和 API 费用，建议先用少页 PDF 测试。
- 如果视觉模型请求失败，优先检查模型是否开通、Secrets 是否填写正确、模型名是否完整。

## 项目结构

```text
app/
  prompts/
    card_prompt.py
    multimodal_note_prompt.py
    note_prompt.py
    page_vision_prompt.py
  services/
    card_generator.py
    chunker.py
    llm_client.py
    multimodal_note_merger.py
    note_generator.py
    page_vision_analyzer.py
    pdf_page_renderer.py
    pdf_parser.py
    text_cleaner.py
    vision_llm_client.py
  storage/
    uploads/
    notes/
    cards/
    page_images/
    page_vision_notes/
web/
  streamlit_app.py
.env.example
.gitignore
requirements.txt
README.md
```

## 本地输出目录

- `app/storage/uploads/`：上传的 PDF
- `app/storage/notes/`：生成的 Markdown 笔记
- `app/storage/cards/`：生成的复习卡片
- `app/storage/page_images/{pdf_stem}/`：PDF 每页渲染出的 PNG
- `app/storage/page_vision_notes/{pdf_stem}/`：每页视觉解释 Markdown

这些运行时文件默认不会提交到 GitHub。

## 当前限制

- PDF 文本解析依赖 PDF 本身是否包含可复制文字。
- 视觉逐页解析依赖所配置的多模态模型能力和上下文限制。
- 大型 PDF 逐页调用视觉模型会消耗较多时间和 API 费用。
- 复杂公式、密集表格、截图较糊的页面可能需要人工复核。
- 当前 Streamlit 页面仍偏原型阶段，处理模式还没有完全产品化。
