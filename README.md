# study-agent

本地运行的学习笔记整理 Agent。

第一版目标：

- 支持 PDF 课件上传
- 解析 PDF 文本
- 生成 Markdown 学习笔记
- 生成复习卡片
- 将 Markdown 文件保存到本地

## 技术栈

- Python
- Streamlit
- PyMuPDF
- OpenAI-compatible API
- Markdown 文件保存

## 项目结构

```text
app/
  services/
    pdf_parser.py
    text_cleaner.py
    chunker.py
    llm_client.py
    note_generator.py
    card_generator.py
  prompts/
    note_prompt.py
    card_prompt.py
  storage/
    uploads/
    notes/
    cards/
web/
  streamlit_app.py
.env.example
requirements.txt
README.md
```

## 本地开发

```bash
python -m venv .venv
pip install -r requirements.txt
```

后续可通过 `web/streamlit_app.py` 启动 Streamlit 应用。
