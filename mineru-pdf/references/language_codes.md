# MinerU 语言代码参考

MinerU 支持多种语言的 OCR 识别和文档解析。通过 `language` 参数指定文档的主要语言，以获得最佳识别效果。

## 独立语言包

| 代码 | 包含语言 | 说明 |
|------|----------|------|
| `ch` | 中文、英文、繁体中文 | **默认**，适合大多数中文文档 |
| `ch_server` | 中文、英文、繁体中文、日文 | 支持繁体、手写体 |
| `en` | 英文 | 纯英文文档 |
| `japan` | 日文、中文、英文、繁体中文 | 日文为主 |
| `korean` | 韩文、英文 | 韩文文档 |
| `chinese_cht` | 繁体中文、中文、英文、日文 | 繁体中文为主 |
| `ta` | 泰米尔文、英文 | 泰米尔文 |
| `te` | 泰卢固文、英文 | 泰卢固文 |
| `ka` | 卡纳达文 | 卡纳达文 |
| `el` | 希腊文、英文 | 希腊文 |
| `th` | 泰文、英文 | 泰文 |

## 语系包

以下代码支持整个语系的多语言识别：

### Latin（拉丁语系）
**代码**: `latin`

包含语言：
- 法语、德语、南非荷兰语、意大利语、西班牙语
- 波斯尼亚语、葡萄牙语、捷克语、威尔士语
- 丹麦语、爱沙尼亚语、爱尔兰语、克罗地亚语
- 乌兹别克语、匈牙利语、塞尔维亚语（拉丁）
- 印度尼西亚语、奥克语、冰岛语、立陶宛语
- 毛利语、马来语、荷兰语、挪威语
- 波兰语、斯洛伐克语、斯洛文尼亚语、阿尔巴尼亚语
- 瑞典语、斯瓦希里语、他加禄语、土耳其语
- 拉丁语、阿塞拜疆语、库尔德语、拉脱维亚语
- 马耳他语、巴利语、罗马尼亚语、越南语
- 芬兰语、巴斯克语、加利西亚语、卢森堡语
- 罗曼什语、加泰罗尼亚语、克丘亚语

### Arabic（阿拉伯语系）
**代码**: `arabic`

包含语言：
- 阿拉伯语、波斯语、维吾尔语、乌尔都语
- 普什图语、库尔德语、信德语、俾路支语
- 英文

### Cyrillic（西里尔语系）
**代码**: `cyrillic`

包含语言：
- 俄语、白俄罗斯语、乌克兰语、保加利亚语
- 塞尔维亚语（西里尔）、马其顿语、哈萨克语
- 吉尔吉斯语、塔吉克语、蒙古语（西里尔）
- 英文

### Devanagari（天城文语系）
**代码**: `devanagari`

包含语言：
- 印地语、马拉地语、尼泊尔语、梵语
- 孔卡尼语、信德语、克什米尔语、比哈里语
- 迈蒂利语、博杰普尔语、迈瓦尔语、尼泊尔班萨语

### 其他语系

| 代码 | 语系 | 包含语言 |
|------|------|----------|
| `hebrew` | 希伯来语系 | 希伯来语、意第绪语、阿拉姆语、英文 |
| `bengali` | 孟加拉语系 | 孟加拉语、阿萨姆语、曼尼普尔语、英文 |
| `kannada` | 卡纳达语系 | 卡纳达语、图卢语、英文 |
| `tamil` | 泰米尔语系 | 泰米尔语、英文 |
| `telugu` | 泰卢固语系 | 泰卢固语、贡迪语、英文 |
| `gujarati` | 古吉拉特语系 | 古吉拉特语、库奇语、英文 |
| `malayalam` | 马拉雅拉姆语系 | 马拉雅拉姆语、图卢语、英文 |
| `oriya` | 奥里亚语系 | 奥里亚语、科拉普里语、英文 |
| `punjabi` | 旁遮普语系 | 旁遮普语（古尔穆基）、英文 |
| `burmese` | 缅甸语系 | 缅甸语、掸语、孟语、克伦语、英文 |
| `khmer` | 高棉语系 | 高棉语、英文 |
| `thai` | 泰语系 | 泰语、老挝语、英文 |
| `lao` | 老挝语系 | 老挝语、英文 |
| `sinhala` | 僧伽罗语系 | 僧伽罗语、巴利语、英文 |
| `tibetan` | 藏语系 | 藏语、宗喀语、拉达克语、英文 |

## 使用建议

### 中文文档
```python
# 简体中文文档（默认）
language = "ch"

# 繁体中文文档
language = "chinese_cht"

# 混合繁体、手写体
language = "ch_server"
```

### 多语言文档
```python
# 中日韩混合
def detect_language(text_sample):
    """简单检测主要语言"""
    if any('\u4e00' <= c <= '\u9fff' for c in text_sample):
        return "ch"  # 中文
    elif any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text_sample):
        return "japan"  # 日文
    elif any('\uac00' <= c <= '\ud7af' for c in text_sample):
        return "korean"  # 韩文
    else:
        return "en"  # 默认英文
```

### 欧洲语言
```python
# 西欧语言混合
language = "latin"

# 东欧西里尔语
language = "cyrillic"

# 希腊文档
language = "el"
```

### 南亚语言
```python
# 印度次大陆语言
language = "devanagari"  # 印地语等

# 孟加拉语
language = "bengali"

# 泰米尔语
language = "ta"  # 或 "tamil"
```

## OCR 精度说明

### 高精度语言
- 中文（ch）
- 英文（en）
- 日文（japan）
- 韩文（korean）

### 良好支持
- 拉丁语系（latin）
- 阿拉伯语系（arabic）
- 西里尔语系（cyrillic）

### 基础支持
- 其他语系包

## 注意事项

1. **主要语言优先**：`language` 参数指定文档的主要语言，API 会以此为主进行识别
2. **多语言混合**：如果文档包含多种语言，建议选择占比最高的语言
3. **英文辅助**：大多数语言包都包含英文，无需担心英文内容的识别
4. **OCR 性能**：启用 OCR 时，语言选择会显著影响识别精度和速度

## 完整示例

```python
import requests

token = "your_api_token"
url = "https://mineru.net/api/v4/extract/task"

# 日文论文
data = {
    "url": "https://example.com/japanese_paper.pdf",
    "model_version": "vlm",
    "language": "japan",
    "is_ocr": True
}

# 阿拉伯语文档
data = {
    "url": "https://example.com/arabic_doc.pdf",
    "model_version": "vlm",
    "language": "arabic",
    "is_ocr": True
}

# 多语言欧洲文档
data = {
    "url": "https://example.com/european_doc.pdf",
    "model_version": "vlm",
    "language": "latin"
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```
