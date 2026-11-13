#!/usr/bin/env python3
"""
Evidence Packet 原型运行脚本

对六个案例运行原型，生成 Evidence Packet 报告。

用法:
    python run_packet.py [case_id]

参数:
    case_id: 可选，指定运行哪个案例（c1-c6）。不指定则运行全部。

示例:
    python run_packet.py          # 运行全部案例
    python run_packet.py c1       # 只运行 FastAPI #16557
"""

import sys
from pathlib import Path

# 添加 packet 模块到路径
sys.path.insert(0, str(Path(__file__).parent))

from packet import (
    PRMetadata, CodeChange, ExecutionEvidence, CIJobResult,
    FunctionChange, EvidencePacketGenerator, EvidencePacketReporter,
    FailureType, TestFailure
)


def create_case_c1() -> tuple:
    """FastAPI #16557: Form Model 的 AliasChoices 提取"""
    metadata = PRMetadata(
        pr_number=16557,
        repo="fastapi/fastapi",
        title="🐛 Fix `AliasChoices` extraction for form models",
        author="tiangolo",
        base_sha="e08d28df250b4e810862723166c83d2919944ed1",
        head_sha="5bcf22c97909f35bf0ee8dda0b655e7113501473",
        merge_sha="75f3a149359bfd39665aaf81dc223fb6fc28da23",
        has_independent_issue=False,
    )
    
    code_change = CodeChange(
        production_files=["fastapi/dependencies/utils.py"],
        test_files=[
            "tests/test_request_params/test_file/test_nullable_and_defaults.py",
            "tests/test_request_params/test_form/test_nullable_and_defaults.py",
            "tests/test_union_form_normalization.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="_extract_form_items",
                change_type="modified",
                is_test_code=False,
                lines_added=15,
                lines_removed=8,
            ),
        ],
        total_lines_added=111,
        total_lines_removed=12,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=True,
        base_head_comparable=False,
        base_jobs=[
            CIJobResult(
                job_name="regression-test",
                status="failure",
                passed=211,
                failed=9,
                skipped=3,
                is_base_replay=True,
                failures=[
                    TestFailure(
                        test_name="test_form_model_fields_can_share_an_unused_alias_choice",
                        failure_type=FailureType.ASSERTION_ERROR,
                    ),
                    TestFailure(
                        test_name="test_model_files_can_share_an_unused_alias_choice",
                        failure_type=FailureType.ASSERTION_ERROR,
                    ),
                ],
            ),
        ],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.13)",
                status="success",
                passed=4414,
                failed=0,
                skipped=20,
            ),
        ],
    )
    
    return metadata, code_change, execution


def create_case_c2() -> tuple:
    """FastAPI #16559: 命名 JSON Body 参数的 AliasChoices"""
    metadata = PRMetadata(
        pr_number=16559,
        repo="fastapi/fastapi",
        title="🐛 Fix `AliasChoices` for named JSON body parameters",
        author="tiangolo",
        base_sha="37f916101f36c4ed4faee1004d07a818c1330d63",
        head_sha="6b1599a09f3ecb1a7fb90a37ed5d8a0d2763c212",
        merge_sha="2d1851f35da7025273b51fc3aa3deb88839a6a33",
        has_independent_issue=False,
    )
    
    code_change = CodeChange(
        production_files=["fastapi/dependencies/utils.py"],
        test_files=[
            "tests/test_body_alias_choices.py",
            "tests/test_request_params/test_file/test_nullable_and_defaults.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="request_body_to_args",
                change_type="modified",
                is_test_code=False,
                lines_added=20,
                lines_removed=5,
            ),
        ],
        total_lines_added=431,
        total_lines_removed=9,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=True,
        base_head_comparable=False,
        base_jobs=[
            CIJobResult(
                job_name="regression-test",
                status="failure",
                passed=37,
                failed=26,
                skipped=3,
                is_base_replay=True,
                failures=[
                    TestFailure(
                        test_name="test_embedded_body_alias_choices",
                        failure_type=FailureType.ASSERTION_ERROR,
                    ),
                ],
            ),
        ],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.13)",
                status="success",
                passed=4414,
                failed=0,
                skipped=20,
            ),
        ],
    )
    
    return metadata, code_change, execution


def create_case_c3() -> tuple:
    """FastAPI #16564: Form 与 File 的验证错误位置"""
    metadata = PRMetadata(
        pr_number=16564,
        repo="fastapi/fastapi",
        title="🐛 Fix validation error locations for form and file `AliasChoices`",
        author="tiangolo",
        base_sha="3b39c91cd1f221042313634db901c64615bb4fb5",
        head_sha="3d92fbb407ca10c1e58f44ef13c53888a94aaaf8",
        merge_sha="1282e9a9f1ac0647cb2031c6dd9c1d5631ade4d4",
        has_independent_issue=False,
    )
    
    code_change = CodeChange(
        production_files=[
            "fastapi/dependencies/utils.py",
            "fastapi/_compat/v2.py",
            "fastapi/openapi/utils.py",
        ],
        test_files=[
            "tests/test_request_params/test_file/test_nullable_and_defaults.py",
            "tests/test_request_params/test_form/test_nullable_and_defaults.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="_extract_form_body",
                change_type="modified",
                is_test_code=False,
                lines_added=25,
                lines_removed=10,
            ),
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="request_body_to_args",
                change_type="modified",
                is_test_code=False,
                lines_added=15,
                lines_removed=8,
            ),
        ],
        total_lines_added=171,
        total_lines_removed=22,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=True,
        base_head_comparable=False,
        base_jobs=[
            CIJobResult(
                job_name="regression-test",
                status="failure",
                passed=179,
                failed=6,
                skipped=3,
                is_base_replay=True,
                failures=[
                    TestFailure(
                        test_name="test_file_alias_choices_errors_use_selected_aliases",
                        failure_type=FailureType.ASSERTION_ERROR,
                    ),
                ],
            ),
        ],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.13)",
                status="success",
                passed=4414,
                failed=0,
                skipped=20,
            ),
        ],
    )
    
    return metadata, code_change, execution


def create_case_c4() -> tuple:
    """FastAPI #16555: Query、Header、Cookie 的 AliasChoices"""
    metadata = PRMetadata(
        pr_number=16555,
        repo="fastapi/fastapi",
        title="🐛 Fix `AliasChoices` for query parameters, headers, and cookies",
        author="tiangolo",
        base_sha="44cc7420b798b70b406516f5f0abf039f99edbe3",
        head_sha="b6c0e4e43362a1e9b5a25d1b8ced3eb681d251e8",
        merge_sha="dfb3b91b7c6102cddde6e2cb1422d0faaa273be5",
        has_independent_issue=False,
    )
    
    code_change = CodeChange(
        production_files=[
            "fastapi/dependencies/utils.py",
            "fastapi/openapi/utils.py",
            "fastapi/_compat/v2.py",
        ],
        test_files=[
            "tests/test_query_alias_choices.py",
            "tests/test_header_cookie_alias_choices.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="_get_param_aliases",
                change_type="added",
                is_test_code=False,
                lines_added=30,
                lines_removed=0,
            ),
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="request_params_to_args",
                change_type="modified",
                is_test_code=False,
                lines_added=20,
                lines_removed=10,
            ),
        ],
        total_lines_added=1115,
        total_lines_removed=15,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=True,
        base_head_comparable=False,
        base_jobs=[
            CIJobResult(
                job_name="regression-test",
                status="success",  # 注意：Job 报告 success，但有 EOFError
                passed=0,
                failed=0,
                skipped=0,
                is_base_replay=True,
                failures=[
                    TestFailure(
                        test_name="test_query_alias_choices",
                        failure_type=FailureType.EOF_ERROR,
                    ),
                ],
            ),
        ],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.13)",
                status="success",
                passed=4414,
                failed=0,
                skipped=20,
            ),
        ],
    )
    
    return metadata, code_change, execution


def create_case_c5() -> tuple:
    """FastAPI #16560: Path 参数的 AliasChoices"""
    metadata = PRMetadata(
        pr_number=16560,
        repo="fastapi/fastapi",
        title="🐛 Fix `AliasChoices` for path parameters",
        author="tiangolo",
        base_sha="b2ce629ace6bdd152d577e5f5e256a079ac1e4fd",
        head_sha="3f9495882ebf29c25bb1c014d7e7cac4a9570669",
        merge_sha="89317c7003d0cca25e56b5acbfc11aa2c1810e08",
        has_independent_issue=False,
    )
    
    code_change = CodeChange(
        production_files=["fastapi/dependencies/utils.py"],
        test_files=[
            "tests/test_path_alias_choices.py",
            "tests/test_header_cookie_alias_choices.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="fastapi/dependencies/utils.py",
                function_name="analyze_param",
                change_type="modified",
                is_test_code=False,
                lines_added=15,
                lines_removed=5,
            ),
        ],
        total_lines_added=288,
        total_lines_removed=6,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=True,
        base_head_comparable=False,
        base_jobs=[
            CIJobResult(
                job_name="regression-test",
                status="success",  # 注意：Job 报告 success，但有 EOFError
                passed=0,
                failed=0,
                skipped=0,
                is_base_replay=True,
                failures=[
                    TestFailure(
                        test_name="test_path_alias_choices",
                        failure_type=FailureType.EOF_ERROR,
                    ),
                ],
            ),
        ],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.13)",
                status="success",
                passed=4414,
                failed=0,
                skipped=20,
            ),
        ],
    )
    
    return metadata, code_change, execution


def create_case_c6() -> tuple:
    """pytest #15255: tmp_path / mktemp 的 O(N²) 性能问题"""
    metadata = PRMetadata(
        pr_number=15255,
        repo="pytest-dev/pytest",
        title="tmpdir: hand out numbered dirs from a per-prefix counter",
        author="RonnyPfannschmidt",
        base_sha="ae37a013763e9c4a143245eda1acdc3c27961685",
        head_sha="22705a59e6b697edf6242ef96fb3abd933339259",
        merge_sha="082ed70e314ee8e1ab117763d17fe801648f7508",
        linked_issues=["#15254"],
        ai_disclosure="Written by Claude Opus 5.5 via Claude Code",
        has_independent_issue=True,
    )
    
    code_change = CodeChange(
        production_files=[
            "src/_pytest/tmpdir.py",
            "changelog/15254.improvement.rst",
        ],
        test_files=[
            "testing/test_tmpdir.py",
        ],
        function_changes=[
            FunctionChange(
                file_path="src/_pytest/tmpdir.py",
                function_name="_make_counted_dir",
                change_type="added",
                is_test_code=False,
                lines_added=25,
                lines_removed=0,
            ),
            FunctionChange(
                file_path="testing/test_tmpdir.py",
                function_name="test_mktemp_does_not_list_basetemp",
                change_type="added",
                is_test_code=True,
                lines_added=15,
                lines_removed=0,
            ),
            FunctionChange(
                file_path="testing/test_tmpdir.py",
                function_name="test_counted_dir_skips_unexpected_entries",
                change_type="added",
                is_test_code=True,
                lines_added=20,
                lines_removed=0,
            ),
        ],
        total_lines_added=105,
        total_lines_removed=0,
    )
    
    execution = ExecutionEvidence(
        has_base_replay=False,  # pytest 没有 Base 重放机制
        base_head_comparable=False,
        base_jobs=[],
        head_jobs=[
            CIJobResult(
                job_name="test (ubuntu-latest, 3.12)",
                status="success",
                passed=4705,
                failed=0,
                skipped=50,
            ),
        ],
    )
    
    return metadata, code_change, execution


def main():
    """主函数"""
    cases = {
        "c1": ("FastAPI #16557", create_case_c1),
        "c2": ("FastAPI #16559", create_case_c2),
        "c3": ("FastAPI #16564", create_case_c3),
        "c4": ("FastAPI #16555", create_case_c4),
        "c5": ("FastAPI #16560", create_case_c5),
        "c6": ("pytest #15255", create_case_c6),
    }
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        case_ids = [sys.argv[1].lower()]
    else:
        case_ids = list(cases.keys())
    
    # 验证 case_id
    for case_id in case_ids:
        if case_id not in cases:
            print(f"错误: 未知的案例 ID '{case_id}'")
            print(f"可用的案例: {', '.join(cases.keys())}")
            sys.exit(1)
    
    # 运行案例
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    for case_id in case_ids:
        case_name, case_factory = cases[case_id]
        print(f"\n{'='*60}")
        print(f"运行案例: {case_name} ({case_id})")
        print(f"{'='*60}\n")
        
        # 创建数据
        metadata, code_change, execution = case_factory()
        
        # 生成 Evidence Packet
        generator = EvidencePacketGenerator()
        packet = generator.generate(metadata, code_change, execution)
        
        # 生成报告
        reporter = EvidencePacketReporter(packet)
        output_file = output_dir / f"{case_id}-evidence-packet.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            reporter.generate_report(f)
        
        print(f"报告已生成: {output_file}")
        
        # 打印摘要
        print(f"\n摘要:")
        print(f"  Claims: {len(packet.claims)}")
        print(f"  Evidence: {len(packet.evidence)}")
        print(f"  Unknowns: {len(packet.unknowns)}")
        print(f"  自动提取: {len(packet.automated_extractions)} 项")
        print(f"  需人工判断: {len(packet.manual_judgments_required)} 项")
    
    print(f"\n{'='*60}")
    print(f"全部完成！报告保存在: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
