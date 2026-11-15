#!/usr/bin/env python3
"""
解决合并冲突 - 保留 main 分支的内容
"""
import re
import sys

def resolve_conflict(file_path):
    """解决单个文件的冲突，保留 main 的内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配冲突块
    # <<<<<<< HEAD
    # ... (PR branch content)
    # =======
    # ... (main branch content)
    # >>>>>>> main
    pattern = r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> main\n'
    
    def replace_conflict(match):
        # 保留 main 的内容（第二个捕获组）
        main_content = match.group(2)
        return main_content
    
    resolved = re.sub(pattern, replace_conflict, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(resolved)
    
    # 验证是否还有冲突标记
    remaining = resolved.count('<<<<<<<') + resolved.count('>>>>>>>')
    if remaining > 0:
        print(f"警告: {file_path} 仍有 {remaining} 个冲突标记")
        return False
    else:
        print(f"✓ 已解决: {file_path}")
        return True

if __name__ == '__main__':
    files = [
        'README.md',
        'explorations/0001-ai-era-software-value/README.md',
        'explorations/0001-ai-era-software-value/frameworks/software-landscape-taxonomy.md',
        'explorations/0001-ai-era-software-value/hypotheses/HYP-001-small-business-ai-workflow.md',
        'explorations/0001-ai-era-software-value/hypotheses/HYP-002-family-os.md',
        'explorations/0001-ai-era-software-value/hypotheses/HYP-003-agriculture-ai-assistant.md',
        'explorations/0001-ai-era-software-value/hypotheses/HYP-004-elderly-digital-assistant.md',
        'explorations/0001-ai-era-software-value/hypotheses/HYP-005-blue-collar-ai-assistant.md',
        'templates/hypothesis-template.md',
    ]
    
    all_ok = True
    for f in files:
        if not resolve_conflict(f):
            all_ok = False
    
    if all_ok:
        print("\n✓ 所有冲突已解决")
        sys.exit(0)
    else:
        print("\n✗ 部分文件仍有冲突")
        sys.exit(1)
