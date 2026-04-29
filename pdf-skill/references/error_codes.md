# MinerU API 错误码参考

## 通用错误码

| 错误码 | 说明 | 解决建议 |
|--------|------|----------|
| `0` | 成功 | - |
| `A0202` | Token 错误 | 检查 Token 是否正确，确保有 `Bearer ` 前缀 |
| `A0211` | Token 过期 | 前往 https://mineru.net/apiManage 申请新 Token |
| `-500` | 传参错误 | 请确保参数类型及 Content-Type 正确 |
| `-10001` | 服务异常 | 请稍后再试 |
| `-10002` | 请求参数错误 | 检查请求参数格式 |

## 文件相关错误

| 错误码 | 说明 | 解决建议 |
|--------|------|----------|
| `-60001` | 生成上传 URL 失败 | 请稍后再试 |
| `-60002` | 获取匹配的文件格式失败 | 确保文件名及链接带有正确的后缀名，且文件为支持的格式 |
| `-60003` | 文件读取失败 | 请检查文件是否损坏并重新上传 |
| `-60004` | 空文件 | 请上传有效文件 |
| `-60005` | 文件大小超出限制 | 检查文件大小，精准 API 最大 200MB，轻量 API 最大 10MB |
| `-60006` | 文件页数超过限制 | 使用 `page_ranges` 参数指定页码范围，或拆分文件 |
| `-60007` | 模型服务暂时不可用 | 请稍后重试或联系技术支持 |
| `-60008` | 文件读取超时 | 检查 URL 是否可访问 |
| `-60009` | 任务提交队列已满 | 请稍后再试 |
| `-60010` | 解析失败 | 请稍后再试 |
| `-60011` | 获取有效文件失败 | 请确保文件已上传 |
| `-60012` | 找不到任务 | 请确保 task_id 有效且未删除 |
| `-60013` | 没有权限访问该任务 | 只能访问自己提交的任务 |
| `-60014` | 删除运行中的任务 | 运行中的任务暂不支持删除 |
| `-60015` | 文件转换失败 | 可以手动转为 PDF 再上传 |
| `-60016` | 文件转换失败 | 文件转换为指定格式失败，可以尝试其他格式导出或重试 |
| `-60017` | 重试次数达到上限 | 等后续模型升级后重试 |
| `-60018` | 每日解析任务数量已达上限 | 明日再来 |
| `-60019` | HTML 文件解析额度不足 | 明日再来 |
| `-60020` | 文件拆分失败 | 请稍后重试 |
| `-60021` | 读取文件页数失败 | 请稍后重试 |
| `-60022` | 网页读取失败 | 可能因网络问题或者限频导致读取失败，请稍后重试 |

## Agent 轻量 API 专属错误码

| 错误码 | 说明 | Agent 应对策略 |
|--------|------|----------------|
| `-30001` | 文件大小超出轻量接口限制（10MB） | 使用精准 API 或拆分文件 |
| `-30002` | 轻量接口不支持该文件类型 | 请上传 PDF/图片/Doc/PPT/Excel |
| `-30003` | 文件页数超出轻量接口限制 | 使用精准 API 或指定 page_range |
| `-30004` | 请求参数错误 | 检查必填参数是否缺失 |

## HTTP 状态码

| 状态码 | 说明 | 解决建议 |
|--------|------|----------|
| `200` | 请求成功 | - |
| `400` | 请求参数错误 | 检查请求体格式和参数 |
| `401` | 未授权 | 检查 Authorization 头是否正确 |
| `403` | 禁止访问 | Token 可能已过期或无效 |
| `404` | 资源不存在 | 检查 task_id 或 URL 是否正确 |
| `429` | 请求过于频繁 | 降低请求频率，或等待限频重置 |
| `500` | 服务器内部错误 | 请稍后再试 |
| `503` | 服务暂时不可用 | 服务维护中，请稍后再试 |

## 错误处理示例

### Python 错误处理

```python
import requests

def parse_document(url, token):
    api_url = "https://mineru.net/api/v4/extract/task"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"url": url, "model_version": "vlm"}
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        result = response.json()
        
        # 检查业务错误码
        if result.get("code") != 0:
            error_code = result.get("code")
            error_msg = result.get("msg", "未知错误")
            
            if error_code == "A0202":
                raise ValueError(f"Token 错误，请检查环境变量: {error_msg}")
            elif error_code == "A0211":
                raise ValueError(f"Token 已过期，请申请新 Token: {error_msg}")
            elif error_code == -60005:
                raise ValueError(f"文件过大: {error_msg}")
            elif error_code == -60006:
                raise ValueError(f"页数超限: {error_msg}")
            else:
                raise ValueError(f"API 错误 [{error_code}]: {error_msg}")
        
        return result["data"]
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            raise ValueError("请求过于频繁，请稍后再试")
        elif response.status_code == 401:
            raise ValueError("认证失败，请检查 Token")
        else:
            raise ValueError(f"HTTP 错误 {response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"网络请求失败: {e}")
```

### 重试机制

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """带指数退避的重试机制"""
    for attempt in range(max_retries):
        try:
            return func()
        except ValueError as e:
            error_msg = str(e)
            
            # 可重试的错误
            if any(code in error_msg for code in ["-10001", "-60007", "-60009", "-60010"]):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"请求失败，{delay:.1f}秒后重试... ({attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
            
            # 不可重试的错误直接抛出
            raise
    
    raise ValueError("达到最大重试次数")
```

### 文件大小检查

```python
import os

def check_file_size(file_path, api_mode="precise"):
    """
    检查文件大小是否符合 API 限制
    
    Args:
        file_path: 文件路径
        api_mode: "precise" (精准 API) 或 "agent" (轻量 API)
    """
    size = os.path.getsize(file_path)
    size_mb = size / (1024 * 1024)
    
    if api_mode == "precise":
        max_size = 200  # MB
        if size_mb > max_size:
            raise ValueError(f"文件过大 ({size_mb:.1f}MB)，精准 API 限制 {max_size}MB")
    elif api_mode == "agent":
        max_size = 10  # MB
        if size_mb > max_size:
            raise ValueError(f"文件过大 ({size_mb:.1f}MB)，轻量 API 限制 {max_size}MB")
    
    return True
```

## 常见问题排查

### 1. Token 相关

**问题**: `A0202 Token 错误`

**排查步骤**:
1. 检查环境变量是否正确设置：`echo $MINERU_TOKEN`
2. 确认 Token 格式：`Bearer` 前缀由代码自动添加，环境变量中不需要包含
3. 检查 Token 是否包含多余空格或换行
4. 重新申请 Token

### 2. 文件上传失败

**问题**: `-60003 文件读取失败` 或 `-60011 获取有效文件失败`

**排查步骤**:
1. 检查文件是否损坏：尝试用本地阅读器打开
2. 检查文件是否为空：`ls -lh file.pdf`
3. 检查文件扩展名是否正确
4. 尝试重新上传

### 3. URL 解析超时

**问题**: `-60008 文件读取超时` 或 `-60022 网页读取失败`

**排查步骤**:
1. 检查 URL 是否可直接访问：`curl -I <url>`
2. GitHub/AWS 等国外 URL 可能因网络限制超时
3. 建议先下载到国内服务器，再使用本地文件上传
4. 检查 URL 是否包含特殊字符，需要 URL 编码

### 4. 页数超限

**问题**: `-60006 文件页数超过限制`

**解决方案**:
```python
# 使用 page_ranges 参数分批解析
# 先解析前 100 页
data = {
    "url": url,
    "page_ranges": "1-100"
}

# 再解析 101-200 页
data = {
    "url": url,
    "page_ranges": "101-200"
}
```

### 5. 每日限额

**问题**: `-60018 每日解析任务数量已达上限`

**说明**: 
- 每个账号每天有 2000 页最高优先级解析额度
- 超过 2000 页后优先级降低（解析时间可能延长）
- 有硬性的每日任务数量上限

**建议**:
- 合理安排解析任务
- 对于大文件，使用 `page_ranges` 只解析需要的部分
- 考虑使用多个账号（需遵守服务条款）
