"""
Evidence Packet 原型

一个离线工具，用于从 PR 数据中提取和组织证据，生成 Claim / Evidence / Unknown 记录。

核心组件：
- models: 数据结构定义
- diff_parser: 解析 unified diff，提取函数级变更
- ci_log_parser: 解析 pytest CI 日志，识别失败类型
- generator: 生成 EvidencePacket
- reporter: 生成可读的报告输出
"""

from .models import (
    Claim,
    CIJobResult,
    CodeChange,
    Evidence,
    EvidenceGrade,
    EvidencePacket,
    ExecutionEvidence,
    FailureType,
    FunctionChange,
    PRMetadata,
    TestFailure,
    Unknown,
)
from .diff_parser import DiffParser, parse_diff_file, parse_diff_text
from .ci_log_parser import CILogParser, parse_ci_log, parse_ci_log_file, classify_failure_summary
from .generator import EvidencePacketGenerator
from .reporter import EvidencePacketReporter

__all__ = [
    # Models
    "Claim",
    "CIJobResult",
    "CodeChange",
    "Evidence",
    "EvidenceGrade",
    "EvidencePacket",
    "ExecutionEvidence",
    "FailureType",
    "FunctionChange",
    "PRMetadata",
    "TestFailure",
    "Unknown",
    # Parsers
    "DiffParser",
    "parse_diff_file",
    "parse_diff_text",
    "CILogParser",
    "parse_ci_log",
    "parse_ci_log_file",
    "classify_failure_summary",
    # Generator
    "EvidencePacketGenerator",
    # Reporter
    "EvidencePacketReporter",
]
