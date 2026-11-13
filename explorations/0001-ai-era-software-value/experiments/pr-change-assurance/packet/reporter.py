"""
Evidence Packet 报告生成器

将 EvidencePacket 转换为可读的 Markdown 格式报告。
"""

from typing import TextIO
import sys

from .models import EvidencePacket, EvidenceGrade, FailureType


class EvidencePacketReporter:
    """生成 EvidencePacket 的可读报告"""
    
    def __init__(self, packet: EvidencePacket):
        self.packet = packet
    
    def generate_report(self, output: TextIO = None) -> str:
        """生成 Markdown 格式的报告"""
        if output is None:
            output = sys.stdout
        
        lines = []
        
        # 标题
        lines.append(f"# Evidence Packet: PR #{self.packet.metadata.pr_number}")
        lines.append("")
        lines.append(f"**仓库**: {self.packet.metadata.repo}")
        lines.append(f"**标题**: {self.packet.metadata.title}")
        lines.append(f"**作者**: {self.packet.metadata.author}")
        lines.append(f"**Base SHA**: `{self.packet.metadata.base_sha[:8]}`")
        lines.append(f"**Head SHA**: `{self.packet.metadata.head_sha[:8]}`")
        if self.packet.metadata.merge_sha:
            lines.append(f"**Merge SHA**: `{self.packet.metadata.merge_sha[:8]}`")
        lines.append("")
        
        # 需求来源
        lines.append("## 需求来源")
        lines.append("")
        if self.packet.metadata.has_independent_issue:
            lines.append(f"- ✅ 有独立 Issue: {', '.join(self.packet.metadata.linked_issues)}")
        else:
            lines.append("- ⚠️ 无独立 Issue，需求隐含在 PR 标题和测试中")
        
        if self.packet.metadata.ai_disclosure:
            lines.append(f"- AI 披露: {self.packet.metadata.ai_disclosure}")
        else:
            lines.append("- ⚠️ 无 AI 披露声明")
        lines.append("")
        
        # Claims
        lines.append("## Claims（主张）")
        lines.append("")
        for i, claim in enumerate(self.packet.claims, 1):
            lines.append(f"### Claim {i}: {claim.statement}")
            lines.append("")
            lines.append(f"- **来源**: {claim.source}")
            lines.append(f"- **证据等级**: {self._format_grade(claim.grade)}")
            if claim.has_independent_definition:
                lines.append("- ✅ 有独立的需求定义")
            else:
                lines.append("- ⚠️ 无独立的需求定义")
            lines.append("")
        
        # Evidence
        lines.append("## Evidence（证据）")
        lines.append("")
        for i, evidence in enumerate(self.packet.evidence, 1):
            lines.append(f"### Evidence {i}: {evidence.evidence_type}")
            lines.append("")
            lines.append(f"- **关联 Claim**: {evidence.claim_ref}")
            lines.append(f"- **描述**: {evidence.description}")
            lines.append(f"- **证据等级**: {self._format_grade(evidence.grade)}")
            
            if evidence.test_names:
                lines.append(f"- **测试函数**: {', '.join(evidence.test_names[:5])}")
                if len(evidence.test_names) > 5:
                    lines.append(f"  - ... 还有 {len(evidence.test_names) - 5} 个")
            
            if evidence.failure_type:
                lines.append(f"- **失败类型**: {self._format_failure_type(evidence.failure_type)}")
            
            if evidence.file_refs:
                lines.append(f"- **相关文件**: {', '.join(evidence.file_refs[:3])}")
                if len(evidence.file_refs) > 3:
                    lines.append(f"  - ... 还有 {len(evidence.file_refs) - 3} 个")
            lines.append("")
        
        # Unknowns
        lines.append("## Unknowns（未知）")
        lines.append("")
        for i, unknown in enumerate(self.packet.unknowns, 1):
            lines.append(f"### Unknown {i}: {unknown.question}")
            lines.append("")
            lines.append(f"- **关联 Claim**: {unknown.claim_ref}")
            lines.append(f"- **原因**: {unknown.reason}")
            lines.append("")
        
        # 自动化程度
        lines.append("## 自动化程度")
        lines.append("")
        lines.append("### 可自动提取的项目")
        lines.append("")
        for item in self.packet.automated_extractions:
            lines.append(f"- ✅ {item}")
        lines.append("")
        
        lines.append("### 需要人工判断的项目")
        lines.append("")
        for item in self.packet.manual_judgments_required:
            lines.append(f"- ⚠️ {item}")
        lines.append("")
        
        # 统计摘要
        lines.append("## 统计摘要")
        lines.append("")
        lines.append(f"- **生产代码文件**: {len(self.packet.code_change.production_files)}")
        lines.append(f"- **测试代码文件**: {len(self.packet.code_change.test_files)}")
        lines.append(f"- **函数变更**: {len(self.packet.code_change.function_changes)}")
        lines.append(f"- **代码行增加**: {self.packet.code_change.total_lines_added}")
        lines.append(f"- **代码行删除**: {self.packet.code_change.total_lines_removed}")
        lines.append("")
        
        if self.packet.execution.has_base_replay:
            lines.append("### Base 重放结果")
            lines.append("")
            for job in self.packet.execution.base_jobs:
                lines.append(f"- **{job.job_name}**: {job.passed} passed, {job.failed} failed")
                if job.failures:
                    failure_types = {}
                    for f in job.failures:
                        ft = f.failure_type
                        failure_types[ft] = failure_types.get(ft, 0) + 1
                    for ft, count in failure_types.items():
                        lines.append(f"  - {self._format_failure_type(ft)}: {count}")
            lines.append("")
        
        if self.packet.execution.head_jobs:
            lines.append("### Head 测试结果")
            lines.append("")
            for job in self.packet.execution.head_jobs:
                lines.append(f"- **{job.job_name}**: {job.passed} passed, {job.failed} failed")
            lines.append("")
        
        report = "\n".join(lines)
        output.write(report)
        return report
    
    def _format_grade(self, grade: EvidenceGrade) -> str:
        """格式化证据等级"""
        grade_map = {
            EvidenceGrade.FACT: "Fact（事实）",
            EvidenceGrade.EVIDENCE: "Evidence（证据）",
            EvidenceGrade.INFERENCE: "Inference（推论）",
            EvidenceGrade.JUDGMENT: "Judgment（判断）",
            EvidenceGrade.UNKNOWN: "Unknown（未知）",
        }
        return grade_map.get(grade, str(grade))
    
    def _format_failure_type(self, failure_type: FailureType) -> str:
        """格式化失败类型"""
        type_map = {
            FailureType.ASSERTION_ERROR: "AssertionError（行为回归的强证据）",
            FailureType.EOF_ERROR: "EOFError（测量工具问题，无效证据）",
            FailureType.SNAPSHOT_MISMATCH: "Snapshot mismatch（需审查差异内容）",
            FailureType.COLLECTION_ERROR: "Collection error（环境问题，无效证据）",
            FailureType.OTHER: "Other（原因不明）",
        }
        return type_map.get(failure_type, str(failure_type))
