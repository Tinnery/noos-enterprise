"""
Evidence Packet 生成器

将解析后的数据组织为 Claim / Evidence / Unknown 记录。
这是原型的核心组件，负责：
1. 从 PR 标题和代码变更推断 Claim
2. 从 diff 和 CI 日志提取 Evidence
3. 识别无法从现有材料证明的 Unknown
4. 标注哪些是自动提取的，哪些需要人工判断
"""

from typing import Optional

from .models import (
    Claim, CodeChange, Evidence, EvidenceGrade, EvidencePacket,
    ExecutionEvidence, FailureType, PRMetadata, Unknown
)


class EvidencePacketGenerator:
    """生成 Evidence Packet"""
    
    def generate(
        self,
        metadata: PRMetadata,
        code_change: CodeChange,
        execution: ExecutionEvidence
    ) -> EvidencePacket:
        """生成完整的 Evidence Packet"""
        
        packet = EvidencePacket(
            metadata=metadata,
            code_change=code_change,
            execution=execution
        )
        
        # 1. 提取 Claims
        claims = self._extract_claims(metadata, code_change)
        packet.claims = claims
        
        # 2. 提取 Evidence
        evidence_list = self._extract_evidence(claims, code_change, execution)
        packet.evidence = evidence_list
        
        # 3. 提取 Unknowns
        unknowns = self._extract_unknowns(claims, metadata, execution)
        packet.unknowns = unknowns
        
        # 4. 标注自动化程度
        packet.automated_extractions = self._list_automated_extractions()
        packet.manual_judgments_required = self._list_manual_judgments(claims, execution)
        
        return packet
    
    def _extract_claims(self, metadata: PRMetadata, code_change: CodeChange) -> list[Claim]:
        """从 PR 标题和代码变更推断 Claim"""
        claims = []
        
        # Claim 1: 从 PR 标题提取主要主张
        title = metadata.title
        # 清理标题前缀（如 🐛、✨ 等 emoji）
        clean_title = title.lstrip('🐛✨🔧📝🎨⚡️🔥💄🚀✅❌⚠️🐞🎉📦🔒🔓')
        clean_title = clean_title.strip()
        
        # 判断是否有独立需求定义
        has_independent = metadata.has_independent_issue or len(metadata.linked_issues) > 0
        
        claims.append(Claim(
            statement=clean_title,
            source=f"PR #{metadata.pr_number} title",
            grade=EvidenceGrade.JUDGMENT,
            has_independent_definition=has_independent
        ))
        
        # Claim 2: 如果有 linked issues，提取 Issue 中的需求
        if metadata.linked_issues:
            for issue in metadata.linked_issues:
                claims.append(Claim(
                    statement=f"Issue {issue} 中定义的需求",
                    source=f"Linked issue: {issue}",
                    grade=EvidenceGrade.EVIDENCE,
                    has_independent_definition=True
                ))
        
        return claims
    
    def _extract_evidence(
        self,
        claims: list[Claim],
        code_change: CodeChange,
        execution: ExecutionEvidence
    ) -> list[Evidence]:
        """从代码变更和执行结果提取证据"""
        evidence_list = []
        
        if not claims:
            return evidence_list
        
        primary_claim = claims[0].statement
        
        # Evidence 1: 代码变更本身
        if code_change.production_files:
            evidence_list.append(Evidence(
                claim_ref=primary_claim,
                evidence_type="code_change",
                description=(
                    f"生产代码变更涉及 {len(code_change.production_files)} 个文件，"
                    f"共 {code_change.total_lines_added} 行增加，"
                    f"{code_change.total_lines_removed} 行删除"
                ),
                grade=EvidenceGrade.FACT,
                file_refs=code_change.production_files
            ))
        
        # Evidence 2: 测试变更
        if code_change.test_files:
            test_functions = [
                fc.function_name 
                for fc in code_change.function_changes 
                if fc.is_test_code and fc.change_type == "added"
            ]
            evidence_list.append(Evidence(
                claim_ref=primary_claim,
                evidence_type="test_change",
                description=(
                    f"测试代码变更涉及 {len(code_change.test_files)} 个文件"
                    + (f"，新增 {len(test_functions)} 个测试函数" if test_functions else "")
                ),
                grade=EvidenceGrade.FACT,
                test_names=test_functions,
                file_refs=code_change.test_files
            ))
        
        # Evidence 3: Base 重放失败（如果有）
        if execution.has_base_replay:
            for job in execution.base_jobs:
                if job.failed > 0:
                    # 按失败类型分组
                    assertion_failures = [
                        f for f in job.failures 
                        if f.failure_type == FailureType.ASSERTION_ERROR
                    ]
                    eof_failures = [
                        f for f in job.failures 
                        if f.failure_type == FailureType.EOF_ERROR
                    ]
                    snapshot_failures = [
                        f for f in job.failures 
                        if f.failure_type == FailureType.SNAPSHOT_MISMATCH
                    ]
                    
                    if assertion_failures:
                        evidence_list.append(Evidence(
                            claim_ref=primary_claim,
                            evidence_type="test_failure_on_base",
                            description=(
                                f"Base 重放中 {len(assertion_failures)} 个测试因 AssertionError 失败，"
                                f"这是行为回归的强证据"
                            ),
                            grade=EvidenceGrade.EVIDENCE,
                            test_names=[f.test_name for f in assertion_failures],
                            failure_type=FailureType.ASSERTION_ERROR
                        ))
                    
                    if eof_failures:
                        evidence_list.append(Evidence(
                            claim_ref=primary_claim,
                            evidence_type="invalid_evidence",
                            description=(
                                f"Base 重放中 {len(eof_failures)} 个测试因 EOFError 失败，"
                                f"这是测量工具问题，不是有效的行为回归证据"
                            ),
                            grade=EvidenceGrade.EVIDENCE,
                            test_names=[f.test_name for f in eof_failures],
                            failure_type=FailureType.EOF_ERROR
                        ))
                    
                    if snapshot_failures:
                        evidence_list.append(Evidence(
                            claim_ref=primary_claim,
                            evidence_type="snapshot_mismatch_on_base",
                            description=(
                                f"Base 重放中 {len(snapshot_failures)} 个测试出现 snapshot 差异，"
                                f"需要审查差异内容才能判断是否为行为回归"
                            ),
                            grade=EvidenceGrade.EVIDENCE,
                            test_names=[f.test_name for f in snapshot_failures],
                            failure_type=FailureType.SNAPSHOT_MISMATCH
                        ))
                    
                    # 如果没有解析到具体失败，但有失败计数
                    if not job.failures and job.failed > 0:
                        evidence_list.append(Evidence(
                            claim_ref=primary_claim,
                            evidence_type="test_failure_on_base",
                            description=(
                                f"Base 重放中 {job.failed} 个测试失败，"
                                f"但日志中未提取到具体失败类型，需要人工判断"
                            ),
                            grade=EvidenceGrade.INFERENCE
                        ))
        
        # Evidence 4: Head 测试通过
        for job in execution.head_jobs:
            if job.status == "success" and job.passed > 0:
                evidence_list.append(Evidence(
                    claim_ref=primary_claim,
                    evidence_type="test_pass_on_head",
                    description=(
                        f"Head 测试矩阵通过：{job.passed} 个测试通过，"
                        f"{job.failed} 个失败，{job.skipped} 个跳过"
                    ),
                    grade=EvidenceGrade.FACT,
                ))
        
        return evidence_list
    
    def _extract_unknowns(
        self,
        claims: list[Claim],
        metadata: PRMetadata,
        execution: ExecutionEvidence
    ) -> list[Unknown]:
        """识别无法从现有材料证明的问题"""
        unknowns = []
        
        if not claims:
            return unknowns
        
        primary_claim = claims[0].statement
        
        # Unknown 1: 需求独立性
        if not metadata.has_independent_issue:
            unknowns.append(Unknown(
                claim_ref=primary_claim,
                question="测试是否真的验证了需求？",
                reason=(
                    "没有独立的 Issue 定义预期行为，需求隐含在 PR 标题和测试断言中。"
                    "Test Oracle 与测试代码同源，无法独立验证。"
                )
            ))
        
        # Unknown 2: Base/Head 可比性
        if execution.has_base_replay and not execution.base_head_comparable:
            unknowns.append(Unknown(
                claim_ref=primary_claim,
                question="Base 失败和 Head 通过是否具有因果关系？",
                reason=(
                    "Base 重放和 Head 测试矩阵不是同条件对照："
                    "Base 只运行新增/修改的测试文件，Head 运行完整测试套件；"
                    "执行环境也不同。'Base 失败 + Head 通过'不能证明因果关系。"
                )
            ))
        
        # Unknown 3: AI 参与程度
        if not metadata.ai_disclosure:
            unknowns.append(Unknown(
                claim_ref=primary_claim,
                question="AI 参与程度如何？",
                reason="PR 中没有明确的 AI 披露声明。"
            ))
        
        # Unknown 4: 修复完整性
        unknowns.append(Unknown(
            claim_ref=primary_claim,
            question="修复是否覆盖了所有相关的边界情况？",
            reason="无法确认是否存在未被测试覆盖的边界情况。"
        ))
        
        return unknowns
    
    def _list_automated_extractions(self) -> list[str]:
        """列出可以自动提取的项目"""
        return [
            "PR 元数据（SHA、文件列表）",
            "代码 diff 中的函数级变更",
            "CI Job 摘要统计（passed/failed/skipped）",
            "AssertionError 识别",
            "EOFError 识别",
            "Snapshot mismatch 识别",
        ]
    
    def _list_manual_judgments(self, claims: list[Claim], execution: ExecutionEvidence) -> list[str]:
        """列出需要人工判断的项目"""
        judgments = [
            "需求-测试映射（测试是否真的验证了需求）",
            "失败性质的最终分类（需要理解上下文）",
            "Snapshot 差异是否为预期行为变化",
        ]
        
        if not execution.base_head_comparable:
            judgments.append("Base/Head 测试的可比性判断")
        
        return judgments
