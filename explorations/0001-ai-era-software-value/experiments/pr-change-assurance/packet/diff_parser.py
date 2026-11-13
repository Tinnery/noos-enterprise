"""
Diff 解析器

解析 unified diff 格式，提取函数级变更。
支持：
- 识别生产代码和测试代码的变更
- 提取变更的函数名
- 分类变更类型（新增、修改、删除函数）
"""

import re
from pathlib import Path
from typing import Optional

from .models import CodeChange, FunctionChange


class DiffParser:
    """解析 unified diff 格式"""
    
    def __init__(self, diff_text: str, test_patterns: Optional[list[str]] = None):
        """
        Args:
            diff_text: unified diff 格式的文本
            test_patterns: 测试文件路径匹配模式，默认 ["tests/", "testing/", "test_"]
        """
        self.diff_text = diff_text
        self.test_patterns = test_patterns or ["tests/", "testing/", "test_"]
        
    def is_test_file(self, file_path: str) -> bool:
        """判断是否为测试文件"""
        return any(pattern in file_path for pattern in self.test_patterns)
    
    def parse(self) -> CodeChange:
        """解析 diff，返回 CodeChange 对象"""
        change = CodeChange()
        
        # 按文件分割 diff
        file_diffs = self._split_by_file()
        
        for file_path, diff_content in file_diffs.items():
            is_test = self.is_test_file(file_path)
            
            if is_test:
                change.test_files.append(file_path)
            else:
                change.production_files.append(file_path)
            
            # 提取函数级变更
            function_changes = self._extract_function_changes(file_path, diff_content, is_test)
            change.function_changes.extend(function_changes)
            
            # 统计行数
            added, removed = self._count_lines(diff_content)
            change.total_lines_added += added
            change.total_lines_removed += removed
        
        return change
    
    def _split_by_file(self) -> dict[str, str]:
        """按文件分割 diff"""
        file_diffs = {}
        current_file = None
        current_diff = []
        
        for line in self.diff_text.split('\n'):
            # 检测新文件开始
            if line.startswith('diff --git'):
                if current_file:
                    file_diffs[current_file] = '\n'.join(current_diff)
                
                # 提取文件路径
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    current_diff = [line]
                else:
                    current_file = None
                    current_diff = []
            elif current_file:
                current_diff.append(line)
        
        # 处理最后一个文件
        if current_file:
            file_diffs[current_file] = '\n'.join(current_diff)
        
        return file_diffs
    
    def _extract_function_changes(
        self, 
        file_path: str, 
        diff_content: str, 
        is_test: bool
    ) -> list[FunctionChange]:
        """提取函数级变更"""
        changes = []
        
        # Python 函数定义模式
        func_pattern = re.compile(r'^[\+\-]\s*(?:async\s+)?def\s+(\w+)')
        # 类定义模式（用于上下文）
        class_pattern = re.compile(r'^[\+\-]?\s*class\s+(\w+)')
        
        current_function = None
        current_class = None
        added_lines = 0
        removed_lines = 0
        has_addition = False
        has_removal = False
        
        for line in diff_content.split('\n'):
            # 检测类定义
            class_match = class_pattern.match(line)
            if class_match and not line.startswith('+++') and not line.startswith('---'):
                current_class = class_match.group(1)
            
            # 检测函数定义
            func_match = func_pattern.match(line)
            if func_match:
                # 保存前一个函数的变更
                if current_function and (has_addition or has_removal):
                    change_type = self._determine_change_type(has_addition, has_removal)
                    changes.append(FunctionChange(
                        file_path=file_path,
                        function_name=current_function,
                        change_type=change_type,
                        is_test_code=is_test,
                        lines_added=added_lines,
                        lines_removed=removed_lines
                    ))
                
                # 开始新函数
                current_function = func_match.group(1)
                added_lines = 0
                removed_lines = 0
                has_addition = False
                has_removal = False
            
            # 统计变更
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
                has_addition = True
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines += 1
                has_removal = True
        
        # 处理最后一个函数
        if current_function and (has_addition or has_removal):
            change_type = self._determine_change_type(has_addition, has_removal)
            changes.append(FunctionChange(
                file_path=file_path,
                function_name=current_function,
                change_type=change_type,
                is_test_code=is_test,
                lines_added=added_lines,
                lines_removed=removed_lines
            ))
        
        # 如果没有检测到函数级变更，但有文件变更，记录文件级变更
        if not changes and (added_lines > 0 or removed_lines > 0):
            changes.append(FunctionChange(
                file_path=file_path,
                function_name="(module-level)",
                change_type="modified",
                is_test_code=is_test,
                lines_added=added_lines,
                lines_removed=removed_lines
            ))
        
        return changes
    
    def _determine_change_type(self, has_addition: bool, has_removal: bool) -> str:
        """确定变更类型"""
        if has_addition and has_removal:
            return "modified"
        elif has_addition:
            return "added"
        elif has_removal:
            return "deleted"
        return "modified"
    
    def _count_lines(self, diff_content: str) -> tuple[int, int]:
        """统计增加和删除的行数"""
        added = 0
        removed = 0
        
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed += 1
        
        return added, removed


def parse_diff_file(diff_file: Path, test_patterns: Optional[list[str]] = None) -> CodeChange:
    """从文件解析 diff"""
    with open(diff_file, 'r', encoding='utf-8') as f:
        diff_text = f.read()
    
    parser = DiffParser(diff_text, test_patterns)
    return parser.parse()


def parse_diff_text(diff_text: str, test_patterns: Optional[list[str]] = None) -> CodeChange:
    """从文本解析 diff"""
    parser = DiffParser(diff_text, test_patterns)
    return parser.parse()
