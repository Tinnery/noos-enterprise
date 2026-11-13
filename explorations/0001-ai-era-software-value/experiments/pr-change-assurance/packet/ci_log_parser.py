"""
CI 日志解析器

解析 pytest 输出日志，识别失败类型。
支持：
- AssertionError（行为回归的强证据）
- EOFError（测量工具问题，无效证据）
- Snapshot mismatch（行为变化的证据）
- Collection error（环境问题，无效证据）
- 提取失败数量和测试名称
"""

import re
from pathlib import Path
from typing import Optional

from .models import CIJobResult, ExecutionEvidence, FailureType, TestFailure


class CILogParser:
    """解析 pytest CI 日志"""
    
    # 失败类型模式
    FAILURE_PATTERNS = {
        FailureType.ASSERTION_ERROR: [
            re.compile(r'AssertionError', re.IGNORECASE),
            re.compile(r'assert\s+', re.IGNORECASE),
        ],
        FailureType.EOF_ERROR: [
            re.compile(r'EOFError', re.IGNORECASE),
            re.compile(r'EOF when reading', re.IGNORECASE),
        ],
        FailureType.SNAPSHOT_MISMATCH: [
            re.compile(r'snapshot.*mismatch', re.IGNORECASE),
            re.compile(r'inline_snapshot', re.IGNORECASE),
            re.compile(r'Do you want to fix these snapshots', re.IGNORECASE),
        ],
        FailureType.COLLECTION_ERROR: [
            re.compile(r'collection error', re.IGNORECASE),
            re.compile(r'ERROR collecting', re.IGNORECASE),
            re.compile(r'ImportError', re.IGNORECASE),
            re.compile(r'ModuleNotFoundError', re.IGNORECASE),
        ],
    }
    
    def __init__(self, log_text: str):
        """
        Args:
            log_text: pytest 输出日志文本
        """
        self.log_text = log_text
    
    def parse_job_result(
        self, 
        job_name: str, 
        job_url: Optional[str] = None,
        is_base_replay: bool = False
    ) -> CIJobResult:
        """解析单个 Job 的执行结果"""
        result = CIJobResult(
            job_name=job_name,
            job_url=job_url,
            is_base_replay=is_base_replay
        )
        
        # 提取摘要统计
        self._extract_summary(result)
        
        # 提取失败详情
        self._extract_failures(result)
        
        # 确定状态
        if result.failed > 0:
            result.status = "failure"
        elif result.passed > 0:
            result.status = "success"
        else:
            result.status = "unknown"
        
        return result
    
    def _extract_summary(self, result: CIJobResult):
        """提取摘要统计（passed/failed/skipped）"""
        # 匹配 pytest 摘要行
        # 例如："9 failed, 211 passed, 3 skipped, 3.04s"
        summary_pattern = re.compile(
            r'(\d+)\s+failed,?\s*(\d+)\s+passed(?:,\s*(\d+)\s+skipped)?(?:,\s*([\d.]+)s)?'
        )
        
        for line in self.log_text.split('\n'):
            match = summary_pattern.search(line)
            if match:
                result.failed = int(match.group(1))
                result.passed = int(match.group(2))
                result.skipped = int(match.group(3)) if match.group(3) else 0
                result.duration_seconds = float(match.group(4)) if match.group(4) else None
                break
        
        # 如果没有匹配到完整摘要，尝试匹配部分
        if result.failed == 0 and result.passed == 0:
            # 尝试匹配 "X passed"
            passed_match = re.search(r'(\d+)\s+passed', self.log_text)
            if passed_match:
                result.passed = int(passed_match.group(1))
            
            # 尝试匹配 "X failed"
            failed_match = re.search(r'(\d+)\s+failed', self.log_text)
            if failed_match:
                result.failed = int(failed_match.group(1))
    
    def _extract_failures(self, result: CIJobResult):
        """提取失败详情"""
        # 查找失败测试的块
        # pytest 输出格式：
        # _______________________________ test_name _______________________________
        # ...
        # E   AssertionError: ...
        
        # 分割成失败块
        failure_blocks = self._split_failure_blocks()
        
        for block in failure_blocks:
            failure = self._parse_failure_block(block)
            if failure:
                result.failures.append(failure)
    
    def _split_failure_blocks(self) -> list[str]:
        """将日志分割成失败块"""
        blocks = []
        current_block = []
        in_failure = False
        
        # pytest 失败块的分隔符
        separator_pattern = re.compile(r'^_{3,}\s+\S+.*\s+_{3,}$')
        
        for line in self.log_text.split('\n'):
            if separator_pattern.match(line):
                # 遇到新的失败块分隔符
                if current_block:
                    blocks.append('\n'.join(current_block))
                current_block = [line]
                in_failure = True
            elif in_failure:
                current_block.append(line)
                # 检测块结束（遇到新的分隔符或摘要行）
                if re.match(r'^=+\s+.*\s+=+$', line):
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    in_failure = False
        
        # 处理最后一个块
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def _parse_failure_block(self, block: str) -> Optional[TestFailure]:
        """解析单个失败块"""
        lines = block.split('\n')
        if not lines:
            return None
        
        # 提取测试名称
        test_name = None
        separator_pattern = re.compile(r'^_{3,}\s+(.+?)\s+_{3,}$')
        for line in lines[:5]:  # 只检查前几行
            match = separator_pattern.match(line)
            if match:
                test_name = match.group(1).strip()
                break
        
        if not test_name:
            return None
        
        # 检测失败类型
        failure_type = self._classify_failure(block)
        
        # 提取错误消息
        error_message = self._extract_error_message(block)
        
        return TestFailure(
            test_name=test_name,
            failure_type=failure_type,
            error_message=error_message
        )
    
    def _classify_failure(self, block: str) -> FailureType:
        """分类失败类型"""
        # 按优先级检查
        # 1. EOFError（最高优先级，因为是无效证据）
        for pattern in self.FAILURE_PATTERNS[FailureType.EOF_ERROR]:
            if pattern.search(block):
                return FailureType.EOF_ERROR
        
        # 2. Snapshot mismatch
        for pattern in self.FAILURE_PATTERNS[FailureType.SNAPSHOT_MISMATCH]:
            if pattern.search(block):
                return FailureType.SNAPSHOT_MISMATCH
        
        # 3. Collection error
        for pattern in self.FAILURE_PATTERNS[FailureType.COLLECTION_ERROR]:
            if pattern.search(block):
                return FailureType.COLLECTION_ERROR
        
        # 4. AssertionError（默认）
        for pattern in self.FAILURE_PATTERNS[FailureType.ASSERTION_ERROR]:
            if pattern.search(block):
                return FailureType.ASSERTION_ERROR
        
        # 5. 其他
        return FailureType.OTHER
    
    def _extract_error_message(self, block: str) -> Optional[str]:
        """提取错误消息"""
        # 查找以 "E   " 开头的行
        error_lines = []
        for line in block.split('\n'):
            if line.startswith('E   ') or line.startswith('E\t'):
                error_lines.append(line[4:])  # 去掉 "E   " 前缀
        
        if error_lines:
            return '\n'.join(error_lines)
        return None


def parse_ci_log(
    log_text: str, 
    job_name: str, 
    job_url: Optional[str] = None,
    is_base_replay: bool = False
) -> CIJobResult:
    """解析 CI 日志"""
    parser = CILogParser(log_text)
    return parser.parse_job_result(job_name, job_url, is_base_replay)


def parse_ci_log_file(
    log_file: Path, 
    job_name: str, 
    job_url: Optional[str] = None,
    is_base_replay: bool = False
) -> CIJobResult:
    """从文件解析 CI 日志"""
    with open(log_file, 'r', encoding='utf-8') as f:
        log_text = f.read()
    
    return parse_ci_log(log_text, job_name, job_url, is_base_replay)


def classify_failure_summary(log_text: str) -> dict[FailureType, int]:
    """快速分类失败类型统计（不提取详细信息）"""
    parser = CILogParser(log_text)
    counts = {ft: 0 for ft in FailureType}
    
    failure_blocks = parser._split_failure_blocks()
    for block in failure_blocks:
        failure_type = parser._classify_failure(block)
        counts[failure_type] += 1
    
    return counts
