"""
Evidence Packet 数据模型

定义 Evidence Packet 的核心数据结构：
- PR 元数据
- 代码变更（函数级）
- CI 执行结果
- 失败分类
- Claim / Evidence / Unknown 记录
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FailureType(Enum):
    """测试失败类型分类"""
    ASSERTION_ERROR = "assertion_error"  # 行为回归的强证据
    SNAPSHOT_MISMATCH = "snapshot_mismatch"  # 行为变化的证据，需审查差异内容
    EOF_ERROR = "eof_error"  # 测量工具问题，无效证据
    COLLECTION_ERROR = "collection_error"  # 环境问题，无效证据
    OTHER = "other"  # 原因不明


class EvidenceGrade(Enum):
    """证据分级"""
    FACT = "fact"  # 客观发生的事件、状态、数据
    EVIDENCE = "evidence"  # 用来确认事实的来源与材料
    INFERENCE = "inference"  # 通过逻辑推理得出的解释
    JUDGMENT = "judgment"  # 基于事实和证据的评价或立场
    UNKNOWN = "unknown"  # 无法从现有材料证明


@dataclass
class PRMetadata:
    """PR 元数据"""
    pr_number: int
    repo: str  # e.g., "fastapi/fastapi"
    title: str
    author: str
    base_sha: str
    head_sha: str
    merge_sha: Optional[str] = None
    merge_date: Optional[str] = None
    branch: Optional[str] = None
    linked_issues: list[str] = field(default_factory=list)
    ai_disclosure: Optional[str] = None  # AI 披露声明
    has_independent_issue: bool = False  # 是否有独立于测试的需求定义


@dataclass
class FunctionChange:
    """函数级代码变更"""
    file_path: str
    function_name: str
    change_type: str  # "added", "modified", "deleted"
    is_test_code: bool  # 是否为测试代码
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class CodeChange:
    """代码变更汇总"""
    production_files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    function_changes: list[FunctionChange] = field(default_factory=list)
    total_lines_added: int = 0
    total_lines_removed: int = 0


@dataclass
class TestFailure:
    """单个测试失败"""
    test_name: str
    failure_type: FailureType
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class CIJobResult:
    """CI Job 执行结果"""
    job_name: str
    job_url: Optional[str] = None
    status: str = "unknown"  # "success", "failure", "skipped"
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: Optional[float] = None
    failures: list[TestFailure] = field(default_factory=list)
    is_base_replay: bool = False  # 是否为 Base 重放 Job


@dataclass
class ExecutionEvidence:
    """执行证据"""
    base_jobs: list[CIJobResult] = field(default_factory=list)
    head_jobs: list[CIJobResult] = field(default_factory=list)
    has_base_replay: bool = False  # 是否有 Base 重放机制
    base_head_comparable: bool = False  # Base/Head 测试是否同条件


@dataclass
class Claim:
    """主张：本次变更声称修复了什么"""
    statement: str  # 主张内容
    source: str  # 来源（PR 标题、Issue、代码注释等）
    grade: EvidenceGrade = EvidenceGrade.JUDGMENT
    has_independent_definition: bool = False  # 是否有独立于测试的需求定义


@dataclass
class Evidence:
    """证据：哪些测试验证了这些主张"""
    claim_ref: str  # 关联的 Claim
    evidence_type: str  # "test_failure_on_base", "test_pass_on_head", "code_change", "structural_invariant"
    description: str
    grade: EvidenceGrade
    test_names: list[str] = field(default_factory=list)
    failure_type: Optional[FailureType] = None
    file_refs: list[str] = field(default_factory=list)


@dataclass
class Unknown:
    """未知：哪些主张没有证据支持"""
    claim_ref: str  # 关联的 Claim
    question: str  # 无法回答的问题
    reason: str  # 为什么无法回答


@dataclass
class EvidencePacket:
    """完整的 Evidence Packet"""
    metadata: PRMetadata
    code_change: CodeChange
    execution: ExecutionEvidence
    claims: list[Claim] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    unknowns: list[Unknown] = field(default_factory=list)
    
    # 元信息
    automated_extractions: list[str] = field(default_factory=list)  # 自动提取的项目
    manual_judgments_required: list[str] = field(default_factory=list)  # 需要人工判断的项目
