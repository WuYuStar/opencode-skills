#!/usr/bin/env python3
"""
MinerU API 工具函数模块
提供通用的 API 调用、轮询、下载和解压功能
"""

import os
import sys
import time
import zipfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class MinerUError(Exception):
    """MinerU API 错误"""
    pass


def get_token() -> str:
    """从环境变量获取 Token"""
    token = os.environ.get('MINERU_TOKEN')
    if not token:
        raise MinerUError(
            "未找到 MINERU_TOKEN 环境变量。\n"
            "请在 .bashrc 或 .zshrc 中设置：\n"
            "export MINERU_TOKEN='your_api_token'\n"
            "Token 申请地址：https://mineru.net/apiManage"
        )
    return token


def create_headers(token: str) -> Dict[str, str]:
    """创建请求头"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }


def create_task(
    url: str,
    token: str,
    model_version: str = "vlm",
    enable_formula: bool = True,
    enable_table: bool = True,
    is_ocr: bool = False,
    language: str = "ch",
    page_ranges: Optional[str] = None,
    extra_formats: Optional[list] = None,
    data_id: Optional[str] = None,
    callback: Optional[str] = None,
    seed: Optional[str] = None,
    no_cache: bool = False
) -> str:
    """
    创建单个文件解析任务
    
    Args:
        url: 文件 URL
        token: API Token
        model_version: 模型版本
        enable_formula: 是否开启公式识别
        enable_table: 是否开启表格识别
        is_ocr: 是否启用 OCR
        language: 文档语言
        page_ranges: 页码范围
        extra_formats: 额外导出格式
        data_id: 数据 ID
        callback: 回调 URL
        seed: 随机种子
        no_cache: 是否绕过缓存
        
    Returns:
        task_id: 任务 ID
    """
    api_url = "https://mineru.net/api/v4/extract/task"
    headers = create_headers(token)
    
    data = {
        "url": url,
        "model_version": model_version,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "is_ocr": is_ocr,
        "language": language
    }
    
    if page_ranges:
        data["page_ranges"] = page_ranges
    if extra_formats:
        data["extra_formats"] = extra_formats
    if data_id:
        data["data_id"] = data_id
    if callback:
        data["callback"] = callback
    if seed:
        data["seed"] = seed
    if no_cache:
        data["no_cache"] = True
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"创建任务失败: {result.get('msg', '未知错误')} (code: {result.get('code')})")
        
        return result["data"]["task_id"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def query_task(task_id: str, token: str) -> Dict[str, Any]:
    """
    查询任务状态
    
    Args:
        task_id: 任务 ID
        token: API Token
        
    Returns:
        任务状态字典
    """
    api_url = f"https://mineru.net/api/v4/extract/task/{task_id}"
    headers = create_headers(token)
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"查询任务失败: {result.get('msg', '未知错误')}")
        
        return result["data"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def poll_task(
    task_id: str,
    token: str,
    timeout: int = 600,
    interval: int = 3,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    轮询任务直到完成或失败
    
    Args:
        task_id: 任务 ID
        token: API Token
        timeout: 超时时间（秒）
        interval: 轮询间隔（秒）
        verbose: 是否打印进度
        
    Returns:
        任务结果字典（包含 full_zip_url）
    """
    state_labels = {
        "pending": "排队中",
        "running": "正在解析",
        "converting": "格式转换中",
        "waiting-file": "等待文件上传"
    }
    
    start_time = time.time()
    
    if verbose:
        print(f"开始轮询任务 {task_id}...")
    
    while time.time() - start_time < timeout:
        try:
            data = query_task(task_id, token)
            state = data.get("state", "unknown")
            elapsed = int(time.time() - start_time)
            
            if state == "done":
                if verbose:
                    print(f"[{elapsed}s] 解析完成！")
                return data
            
            if state == "failed":
                err_msg = data.get("err_msg", "未知错误")
                raise MinerUError(f"解析失败: {err_msg}")
            
            if state == "running" and "extract_progress" in data:
                progress = data["extract_progress"]
                current = progress.get("extracted_pages", 0)
                total = progress.get("total_pages", 0)
                if verbose:
                    print(f"[{elapsed}s] 正在解析: {current}/{total} 页")
            else:
                if verbose:
                    print(f"[{elapsed}s] {state_labels.get(state, state)}...")
            
            time.sleep(interval)
            
        except MinerUError:
            raise
        except Exception as e:
            if verbose:
                print(f"[{int(time.time() - start_time)}s] 查询出错: {e}，稍后重试...")
            time.sleep(interval)
    
    raise MinerUError(f"轮询超时 ({timeout}秒)，任务可能仍在处理中。任务ID: {task_id}")


def download_file(url: str, output_path: str, verbose: bool = True) -> str:
    """
    下载文件
    
    Args:
        url: 文件 URL
        output_path: 保存路径
        verbose: 是否打印进度
        
    Returns:
        保存的文件路径
    """
    try:
        if verbose:
            print(f"正在下载: {url}")
        
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if verbose:
            print(f"下载完成: {output_path}")
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"下载失败: {e}")


def extract_zip(zip_path: str, extract_dir: str, verbose: bool = True) -> str:
    """
    解压 zip 文件
    
    Args:
        zip_path: zip 文件路径
        extract_dir: 解压目录
        verbose: 是否打印进度
        
    Returns:
        解压目录路径
    """
    try:
        if verbose:
            print(f"正在解压: {zip_path}")
        
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        if verbose:
            print(f"解压完成: {extract_dir}")
        
        return extract_dir
        
    except zipfile.BadZipFile:
        raise MinerUError(f"无效的 zip 文件: {zip_path}")
    except Exception as e:
        raise MinerUError(f"解压失败: {e}")


def find_markdown_file(extract_dir: str) -> Optional[str]:
    """
    在解压目录中查找 Markdown 文件
    
    Args:
        extract_dir: 解压目录
        
    Returns:
        Markdown 文件路径或 None
    """
    md_files = list(Path(extract_dir).rglob("*.md"))
    
    # 优先查找 full.md
    for md_file in md_files:
        if md_file.name == "full.md":
            return str(md_file)
    
    # 否则返回第一个找到的 md 文件
    return str(md_files[0]) if md_files else None


def process_result(
    task_data: Dict[str, Any],
    output_dir: str,
    base_filename: str,
    verbose: bool = True
) -> str:
    """
    处理解析结果：下载、解压、提取 Markdown
    
    Args:
        task_data: 任务结果数据
        output_dir: 输出目录
        base_filename: 基础文件名
        verbose: 是否打印进度
        
    Returns:
        Markdown 文件路径
    """
    full_zip_url = task_data.get("full_zip_url")
    if not full_zip_url:
        raise MinerUError("结果中没有 full_zip_url")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 下载 zip 文件
    zip_filename = f"{base_filename}_full.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    download_file(full_zip_url, zip_path, verbose)
    
    # 解压
    extract_dir = os.path.join(output_dir, f"{base_filename}_extracted")
    extract_zip(zip_path, extract_dir, verbose)
    
    # 查找 Markdown 文件
    md_file = find_markdown_file(extract_dir)
    if not md_file:
        raise MinerUError(f"在解压目录中未找到 Markdown 文件: {extract_dir}")
    
    # 复制到输出目录并重命名
    final_md_path = os.path.join(output_dir, f"{base_filename}.md")
    
    # 如果目标文件已存在，先删除
    if os.path.exists(final_md_path):
        os.remove(final_md_path)
    
    # 复制文件
    import shutil
    shutil.copy2(md_file, final_md_path)
    
    if verbose:
        print(f"\n解析完成！")
        print(f"  Markdown 文件: {final_md_path}")
        print(f"  完整结果目录: {extract_dir}")
        print(f"  压缩包: {zip_path}")
    
    return final_md_path


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不合法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除路径分隔符和其他不合法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def get_filename_from_url(url: str) -> str:
    """
    从 URL 中提取文件名
    
    Args:
        url: 文件 URL
        
    Returns:
        文件名（不含扩展名）
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    # 移除扩展名
    filename = os.path.splitext(filename)[0]
    # 如果文件名为空，使用时间戳
    if not filename:
        filename = f"document_{int(time.time())}"
    return sanitize_filename(filename)
