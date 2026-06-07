PAGE_VISION_PROMPT = """你是一个学习课件页面解析助手。

请仔细阅读这张 PDF 页面图片，并输出该页的 Markdown 解释。

要求：
- 只根据图片内容回答，不要编造看不到的信息。
- 如果文字、公式、图表有看不清的地方，请明确写出来。
- 保留页码信息。
- 使用清晰的 Markdown 标题和列表。

请按以下结构输出：

## 第 {page} 页说明

### 这一页在讲什么

### 关键概念

### 图表/流程图/公式解释

### 例题说明

### 可能考点

### 易错点

### 不清楚或看不清的地方
"""


def build_page_vision_prompt(page: int) -> str:
    return PAGE_VISION_PROMPT.format(page=page)
