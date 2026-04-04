#!/usr/bin/env python3
"""
Memos API 客户端
简化与 Memos v0.26.0 API 的交互
"""

import os
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin


class MemosClient:
    """Memos API 客户端"""
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            base_url: Memos 服务器地址，默认从环境变量 MEMOS_BASE_URL 读取
            token: 访问令牌，默认从环境变量 MEMOS_TOKEN 读取
        """
        self.base_url = (base_url or os.environ.get('MEMOS_BASE_URL', '')).rstrip('/')
        self.token = token or os.environ.get('MEMOS_TOKEN', '')
        
        if not self.base_url:
            raise ValueError("必须提供 base_url 或设置 MEMOS_BASE_URL 环境变量")
        if not self.token:
            raise ValueError("必须提供 token 或设置 MEMOS_TOKEN 环境变量")
        
        self.api_base = f"{self.base_url}/api/v1"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            raise MemosAPIError(
                f"API 错误 {response.status_code}: {error_data.get('message', response.text)}",
                status_code=response.status_code,
                error_code=error_data.get('code'),
                details=error_data.get('details', [])
            )
        
        return response.json() if response.content else {}
    
    # ==================== Memo 管理 ====================
    
    def create_memo(
        self,
        content: str,
        visibility: str = "PRIVATE",
        pinned: bool = False,
        state: str = "NORMAL",
        memo_id: Optional[str] = None,
        display_time: Optional[str] = None,
        location: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建备忘录
        
        Args:
            content: Markdown 格式的内容
            visibility: PRIVATE/PROTECTED/PUBLIC
            pinned: 是否置顶
            state: NORMAL/ARCHIVED
            memo_id: 自定义 ID（可选）
            display_time: 显示时间 ISO 8601 格式（可选）
            location: 地理位置（可选）
        """
        data = {
            "content": content,
            "visibility": visibility,
            "pinned": pinned,
            "state": state
        }
        
        if display_time:
            data["displayTime"] = display_time
        if location:
            data["location"] = location
        
        params = {}
        if memo_id:
            params["memoId"] = memo_id
        
        return self._request("POST", "/memos", params=params, json=data)
    
    def list_memos(
        self,
        page_size: int = 50,
        page_token: Optional[str] = None,
        state: Optional[str] = None,
        order_by: Optional[str] = None,
        filter_expr: Optional[str] = None,
        show_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        列出备忘录
        
        Args:
            page_size: 每页数量（最大 1000）
            page_token: 分页令牌
            state: NORMAL/ARCHIVED
            order_by: 排序方式，如 "pinned desc, display_time desc"
            filter_expr: CEL 过滤表达式
            show_deleted: 是否显示已删除
        """
        params = {"pageSize": page_size}
        
        if page_token:
            params["pageToken"] = page_token
        if state:
            params["state"] = state
        if order_by:
            params["orderBy"] = order_by
        if filter_expr:
            params["filter"] = filter_expr
        if show_deleted:
            params["showDeleted"] = "true"
        
        return self._request("GET", "/memos", params=params)
    
    def get_memo(self, memo_id: str) -> Dict[str, Any]:
        """获取单个备忘录"""
        return self._request("GET", f"/memos/{memo_id}")
    
    def update_memo(
        self,
        memo_id: str,
        update_mask: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        更新备忘录
        
        Args:
            memo_id: 备忘录 ID
            update_mask: 要更新的字段列表，如 ["content", "visibility"]
            **kwargs: 要更新的字段值
        """
        data = {"name": f"memos/{memo_id}"}
        data.update(kwargs)
        
        params = {"updateMask": ",".join(update_mask)}
        
        return self._request("PATCH", f"/memos/{memo_id}", params=params, json=data)
    
    def delete_memo(self, memo_id: str, force: bool = False) -> None:
        """删除备忘录"""
        params = {"force": "true"} if force else {}
        self._request("DELETE", f"/memos/{memo_id}", params=params)
    
    def archive_memo(self, memo_id: str) -> Dict[str, Any]:
        """归档备忘录"""
        return self.update_memo(memo_id, ["state"], state="ARCHIVED")
    
    def unarchive_memo(self, memo_id: str) -> Dict[str, Any]:
        """恢复归档的备忘录"""
        return self.update_memo(memo_id, ["state"], state="NORMAL")
    
    def pin_memo(self, memo_id: str) -> Dict[str, Any]:
        """置顶备忘录"""
        return self.update_memo(memo_id, ["pinned"], pinned=True)
    
    def unpin_memo(self, memo_id: str) -> Dict[str, Any]:
        """取消置顶"""
        return self.update_memo(memo_id, ["pinned"], pinned=False)
    
    # ==================== 搜索功能 ====================
    
    def search_by_tag(self, tag: str, **kwargs) -> List[Dict[str, Any]]:
        """按标签搜索
        
        注意：使用 content.contains("#标签") 方式，因为 v0.26.0 不支持 has() 函数
        """
        filter_expr = f'content.contains("#{tag}")'
        result = self.list_memos(filter_expr=filter_expr, **kwargs)
        return result.get("memos", [])
    
    def search_by_content(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """按内容搜索"""
        filter_expr = f'content.contains("{keyword}")'
        result = self.list_memos(filter_expr=filter_expr, **kwargs)
        return result.get("memos", [])
    
    def search_by_visibility(self, visibility: str, **kwargs) -> List[Dict[str, Any]]:
        """按可见性搜索"""
        filter_expr = f'visibility == "{visibility}"'
        result = self.list_memos(filter_expr=filter_expr, **kwargs)
        return result.get("memos", [])
    
    def get_pinned_memos(self, **kwargs) -> List[Dict[str, Any]]:
        """获取置顶的备忘录"""
        filter_expr = "pinned == true"
        result = self.list_memos(filter_expr=filter_expr, **kwargs)
        return result.get("memos", [])
    
    # ==================== 附件管理 ====================
    
    def upload_attachment(self, file_path: str) -> Dict[str, Any]:
        """
        上传附件
        
        Args:
            file_path: 本地文件路径
        """
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'Authorization': f'Bearer {self.token}'}
            
            url = f"{self.api_base}/attachments"
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise MemosAPIError(
                    f"上传失败 {response.status_code}: {error_data.get('message', response.text)}"
                )
            
            return response.json()
    
    def set_memo_attachments(
        self,
        memo_id: str,
        attachment_ids: List[str]
    ) -> None:
        """设置备忘录的附件"""
        attachments = [
            {"name": f"memos/{memo_id}/attachments/{aid}"}
            for aid in attachment_ids
        ]
        self._request(
            "PATCH",
            f"/memos/{memo_id}/attachments",
            json={"attachments": attachments}
        )
    
    def list_memo_attachments(self, memo_id: str) -> List[Dict[str, Any]]:
        """列出备忘录的附件"""
        result = self._request("GET", f"/memos/{memo_id}/attachments")
        return result.get("attachments", [])
    
    # ==================== 评论管理 ====================
    
    def create_comment(
        self,
        memo_id: str,
        content: str,
        visibility: str = "PRIVATE"
    ) -> Dict[str, Any]:
        """创建评论"""
        data = {
            "comment": {
                "content": content,
                "visibility": visibility,
                "state": "NORMAL"
            }
        }
        return self._request("POST", f"/memos/{memo_id}/comments", json=data)
    
    def list_comments(self, memo_id: str, **kwargs) -> Dict[str, Any]:
        """列出评论"""
        return self._request("GET", f"/memos/{memo_id}/comments", params=kwargs)
    
    # ==================== 表情反应 ====================
    
    def add_reaction(self, memo_id: str, reaction_type: str) -> Dict[str, Any]:
        """
        添加表情反应
        
        Args:
            reaction_type: emoji，如 👍, ❤️, 😄, 🎉
        """
        data = {
            "reaction": {
                "contentId": f"memos/{memo_id}",
                "reactionType": reaction_type
            }
        }
        return self._request("POST", f"/memos/{memo_id}/reactions", json=data)
    
    def list_reactions(self, memo_id: str) -> List[Dict[str, Any]]:
        """列出表情反应"""
        result = self._request("GET", f"/memos/{memo_id}/reactions")
        return result.get("reactions", [])
    
    def delete_reaction(self, memo_id: str, reaction_id: str) -> None:
        """删除表情反应"""
        self._request("DELETE", f"/memos/{memo_id}/reactions/{reaction_id}")
    
    # ==================== 关系管理 ====================
    
    def set_memo_relations(
        self,
        memo_id: str,
        relations: List[Dict[str, Any]]
    ) -> None:
        """
        设置备忘录关系
        
        Args:
            relations: 关系列表，每项包含 memo, relatedMemo, type
                type: REFERENCE 或 COMMENT
        """
        self._request(
            "PATCH",
            f"/memos/{memo_id}/relations",
            json={"relations": relations}
        )
    
    def list_memo_relations(self, memo_id: str) -> List[Dict[str, Any]]:
        """列出备忘录关系"""
        result = self._request("GET", f"/memos/{memo_id}/relations")
        return result.get("relations", [])
    
    def add_related_memo(
        self,
        memo_id: str,
        related_memo_id: str,
        relation_type: str = "REFERENCE"
    ) -> None:
        """添加关联备忘录"""
        relations = self.list_memo_relations(memo_id)
        relations.append({
            "memo": {"name": f"memos/{memo_id}"},
            "relatedMemo": {"name": f"memos/{related_memo_id}"},
            "type": relation_type
        })
        self.set_memo_relations(memo_id, relations)


class MemosAPIError(Exception):
    """Memos API 错误"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[int] = None,
        details: Optional[List] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []


# ==================== 命令行接口 ====================

def main():
    """命令行接口"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Memos CLI')
    parser.add_argument('--base-url', help='Memos base URL')
    parser.add_argument('--token', help='Access token')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 创建备忘录
    create_parser = subparsers.add_parser('create', help='Create a memo')
    create_parser.add_argument('content', help='Memo content')
    create_parser.add_argument('--visibility', default='PRIVATE', choices=['PRIVATE', 'PROTECTED', 'PUBLIC'])
    create_parser.add_argument('--pinned', action='store_true')
    
    # 列出备忘录
    list_parser = subparsers.add_parser('list', help='List memos')
    list_parser.add_argument('--page-size', type=int, default=50)
    list_parser.add_argument('--filter')
    list_parser.add_argument('--order-by')
    
    # 获取备忘录
    get_parser = subparsers.add_parser('get', help='Get a memo')
    get_parser.add_argument('memo_id', help='Memo ID')
    
    # 更新备忘录
    update_parser = subparsers.add_parser('update', help='Update a memo')
    update_parser.add_argument('memo_id', help='Memo ID')
    update_parser.add_argument('--content')
    update_parser.add_argument('--visibility', choices=['PRIVATE', 'PROTECTED', 'PUBLIC'])
    update_parser.add_argument('--pinned', type=bool)
    
    # 删除备忘录
    delete_parser = subparsers.add_parser('delete', help='Delete a memo')
    delete_parser.add_argument('memo_id', help='Memo ID')
    
    # 搜索
    search_parser = subparsers.add_parser('search', help='Search memos')
    search_parser.add_argument('--tag')
    search_parser.add_argument('--keyword')
    
    args = parser.parse_args()
    
    client = MemosClient(base_url=args.base_url, token=args.token)
    
    if args.command == 'create':
        result = client.create_memo(
            content=args.content,
            visibility=args.visibility,
            pinned=args.pinned
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'list':
        result = client.list_memos(
            page_size=args.page_size,
            filter_expr=args.filter,
            order_by=args.order_by
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'get':
        result = client.get_memo(args.memo_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'update':
        update_mask = []
        data = {'name': f"memos/{args.memo_id}"}
        
        if args.content:
            update_mask.append('content')
            data['content'] = args.content
        if args.visibility:
            update_mask.append('visibility')
            data['visibility'] = args.visibility
        if args.pinned is not None:
            update_mask.append('pinned')
            data['pinned'] = args.pinned
        
        result = client.update_memo(args.memo_id, update_mask, **data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'delete':
        client.delete_memo(args.memo_id)
        print(f"Memo {args.memo_id} deleted")
    
    elif args.command == 'search':
        if args.tag:
            result = client.search_by_tag(args.tag)
        elif args.keyword:
            result = client.search_by_content(args.keyword)
        else:
            print("Please specify --tag or --keyword")
            return
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
