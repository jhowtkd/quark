#!/usr/bin/env python3
"""
Automated color-to-token replacement for Vue SFC <style> blocks.
Only replaces inside <style>...</style> blocks.
Skips D3/SVG/JS color arrays and stop-color attributes.
"""

import re
import sys
from pathlib import Path

# Mapping: exact hex/RGB -> CSS custom property
# Ordered: most specific first
COLOR_MAP = {
    '#000000': 'var(--color-on-background)',
    '#000': 'var(--color-on-background)',
    '#FFFFFF': 'var(--color-surface)',
    '#ffffff': 'var(--color-surface)',
    '#FFF': 'var(--color-surface)',
    '#fff': 'var(--color-surface)',
    '#FAFAFA': 'var(--color-surface-container-low)',
    '#fafafa': 'var(--color-surface-container-low)',
    '#F5F5F5': 'var(--color-surface-container-low)',
    '#f5f5f5': 'var(--color-surface-container-low)',
    '#F9F9F9': 'var(--color-background)',
    '#f9f9f9': 'var(--color-background)',
    '#F3F4F6': 'var(--color-surface-container-low)',
    '#F3F3F3': 'var(--color-surface-container-low)',
    '#E5E5E5': 'var(--color-outline)',
    '#E5E7EB': 'var(--color-outline)',
    '#E2E2E2': 'var(--color-surface-container-highest)',
    '#e2e2e2': 'var(--color-surface-container-highest)',
    '#E0E0E0': 'var(--color-outline)',
    '#e0e0e0': 'var(--color-outline)',
    '#EEE': 'var(--color-outline)',
    '#eee': 'var(--color-outline)',
    '#EEEEEE': 'var(--color-surface-container-low)',
    '#eeeeee': 'var(--color-surface-container-low)',
    '#DDD': 'var(--color-outline)',
    '#ddd': 'var(--color-outline)',
    '#CCC': 'var(--color-outline)',
    '#ccc': 'var(--color-outline)',
    '#EAEAEA': 'var(--color-outline)',
    '#eaeaea': 'var(--color-outline)',
    '#E8E8E8': 'var(--color-surface-container-highest)',
    '#e8e8e8': 'var(--color-surface-container-highest)',
    '#DADADA': 'var(--color-outline)',
    '#dadada': 'var(--color-outline)',
    '#D0D0D0': 'var(--color-outline)',
    '#d0d0d0': 'var(--color-outline)',
    '#C0C0C0': 'var(--color-outline)',
    '#c0c0c0': 'var(--color-outline)',
    '#F0F0F0': 'var(--color-surface-container-low)',
    '#F1F5F9': 'var(--color-surface-container-low)',
    '#F8F9FA': 'var(--color-surface-container-low)',
    '#F8FAFC': 'var(--color-surface-container-low)',
    '#FEF3C7': 'var(--color-warning-bg)',
    '#FEE2E2': 'var(--color-error-bg)',
    '#E3F2FD': 'var(--color-info-bg)',
    '#E8F5E9': 'var(--color-success-bg)',
    '#FFEBEE': 'var(--color-error-bg)',
    '#FFF3F2': 'var(--color-error-bg)',
    '#FFF3E0': 'var(--color-warning-bg)',
    '#FFF7EF': 'var(--color-warning-bg)',
    '#FFF9E8': 'var(--color-warning-bg)',
    '#FDE2E0': 'var(--color-error-bg)',
    '#EEF2FF': 'var(--color-info-bg)',
    '#EEF2F6': 'var(--color-surface-container-low)',
    '#DCFCE7': 'var(--color-success-bg)',
    '#BBDEFB': 'var(--color-info-bg)',
    '#FFE0B2': 'var(--color-warning-bg)',
    '#E6E6E6': 'var(--color-outline)',
    '#EFEFEF': 'var(--color-surface-container-low)',
    '#1b1b1b': 'var(--color-on-background)',
    '#1B1B1B': 'var(--color-on-background)',
    '#333333': 'var(--color-on-surface)',
    '#333': 'var(--color-on-surface)',
    '#444444': 'var(--color-muted)',
    '#444': 'var(--color-muted)',
    '#555555': 'var(--color-muted)',
    '#555': 'var(--color-muted)',
    '#666666': 'var(--color-muted)',
    '#666': 'var(--color-muted)',
    '#777777': 'var(--color-muted)',
    '#777': 'var(--color-muted)',
    '#888888': 'var(--color-muted)',
    '#888': 'var(--color-muted)',
    '#999999': 'var(--color-disabled)',
    '#999': 'var(--color-disabled)',
    '#111111': 'var(--color-on-background)',
    '#111': 'var(--color-on-background)',
    '#111827': 'var(--color-on-background)',
    '#1A1A1A': 'var(--color-surface)',
    '#1a1a1a': 'var(--color-surface)',
    '#222222': 'var(--color-surface-elevated)',
    '#222': 'var(--color-surface-elevated)',
    '#374151': 'var(--color-on-surface)',
    '#4B5563': 'var(--color-muted)',
    '#6B7280': 'var(--color-muted)',
    '#757575': 'var(--color-muted)',
    '#9CA3AF': 'var(--color-disabled)',
    '#c6c6c6': 'var(--color-disabled)',
    '#D1D5DB': 'var(--color-outline)',
    '#CBD5E1': 'var(--color-outline)',
    '#94A3B8': 'var(--color-disabled)',
    '#64748B': 'var(--color-muted)',
    '#475569': 'var(--color-muted)',
    '#334155': 'var(--color-muted)',
    '#1E293B': 'var(--color-on-surface)',
    '#2563EB': 'var(--color-info)',
    '#1565C0': 'var(--color-info)',
    '#0D47A1': 'var(--color-info)',
    '#2E7D32': 'var(--color-success)',
    '#388E3C': 'var(--color-success)',
    '#1B5E20': 'var(--color-success)',
    '#16A34A': 'var(--color-success)',
    '#C62828': 'var(--color-error)',
    '#B3261E': 'var(--color-error)',
    '#A62B1F': 'var(--color-error)',
    '#A65A00': 'var(--color-warning)',
    '#DC2626': 'var(--color-error)',
    '#D97706': 'var(--color-warning)',
    '#C5283D': 'var(--color-error)',
    '#E91E63': 'var(--color-error)',
    '#E9724C': 'var(--color-warning)',
    '#FF6B35': 'var(--color-error)',
    '#FF5722': 'var(--color-error)',
    '#FF8A65': 'var(--color-error)',
    '#FF9800': 'var(--color-warning)',
    '#FFCCBC': 'var(--color-warning-bg)',
    '#f39c12': 'var(--color-warning)',
    '#f2e6e6': 'var(--color-error-bg)',
    '#e6eff5': 'var(--color-info-bg)',
    '#e6f2e8': 'var(--color-success-bg)',
    '#f5efe6': 'var(--color-warning-bg)',
    '#f2f0e6': 'var(--color-warning-bg)',
    '#e8eaed': 'var(--color-outline)',
    '#e6f2f2': 'var(--color-info-bg)',
    '#eae6f2': 'var(--color-info-bg)',
    '#a65a5a': 'var(--color-error)',
    '#5a7ea6': 'var(--color-info)',
    '#5aa668': 'var(--color-success)',
    '#a6815a': 'var(--color-warning)',
    '#6b7280': 'var(--color-muted)',
    '#815aa6': 'var(--color-info)',
    '#5aa6a6': 'var(--color-info)',
    '#a69b5a': 'var(--color-warning)',
    '#5e5e5e': 'var(--color-muted)',
    '#4a4a6a': 'var(--color-surface-elevated)',
    '#2a2a4e': 'var(--color-surface-elevated)',
    '#1a1a2e': 'var(--color-surface)',
    '#0a0a0a': 'var(--color-background)',
    '#0a1a3a': 'var(--color-surface)',
    '#0a2a0a': 'var(--color-surface)',
    '#2a0a0a': 'var(--color-surface)',
    '#2a1a0a': 'var(--color-surface)',
    '#4CAF50': 'var(--color-success)',
    '#A855F7': 'var(--color-info)',
    '#6366F1': 'var(--color-info)',
    '#818CF8': 'var(--color-info)',
}

# Line patterns that should NOT be modified
SKIP_PATTERNS = [
    r"stop-color",
    r"stopColor",
    r"\.attr\('stroke'",
    r"\.attr\('fill'",
    r"\.attr\('color'",
    r"const colors =",
    r"colorMap",
    r"getColor",
    r"background:\s*linear-gradient",
    r"background:\s*radial-gradient",
    r"filter:\s*drop-shadow",
    r"box-shadow:\s*0",
    r"border:\s*\d+px\s+solid\s+rgba",
    r"border-top:\s*\d+px\s+solid\s+rgba",
    r"border-bottom:\s*\d+px\s+solid\s+rgba",
    r"border-left:\s*.*\s+solid\s+rgba",
    r"border-right:\s*.*\s+solid\s+rgba",
    r"border-top-color:",
    r"border-color:",
    r"rgba\(",
]

def should_skip_line(line):
    stripped = line.strip()
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return True
    return False

def replace_line(line):
    if should_skip_line(line):
        return line
    
    def replacer(match):
        color = match.group(0)
        return COLOR_MAP.get(color, color)
    
    # Hex colors (3 or 6 digits)
    new_line = re.sub(r'#([0-9a-fA-F]{3})\b', replacer, line)
    new_line = re.sub(r'#([0-9a-fA-F]{6})\b', replacer, new_line)
    
    # Named colors
    for name, token in [('white', 'var(--color-surface)'), ('black', 'var(--color-on-background)')]:
        # Only replace standalone words, not inside selectors or other contexts
        new_line = re.sub(rf'\b{name}\b(?!-)', token, new_line, flags=re.IGNORECASE)
    
    return new_line

def replace_in_style_block(block):
    lines = block.split('\n')
    new_lines = [replace_line(line) for line in lines]
    return '\n'.join(new_lines)

def process_file(filepath):
    content = filepath.read_text(encoding='utf-8')
    
    def style_replacer(match):
        attrs = match.group(1) or ''
        block = match.group(2)
        new_block = replace_in_style_block(block)
        return f'<style{attrs}>{new_block}</style>'
    
    new_content = re.sub(r'<style([^>]*)>(.*?)</style>', style_replacer, content, flags=re.DOTALL)
    
    if new_content != content:
        filepath.write_text(new_content, encoding='utf-8')
        old_colors = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', content))
        new_colors = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', new_content))
        return old_colors - new_colors
    return 0

def main():
    src_dir = Path(__file__).parent.parent / 'src'
    vue_files = list(src_dir.rglob('*.vue'))
    
    total_replaced = 0
    for f in sorted(vue_files):
        if 'App.vue' in str(f):
            continue
        count = process_file(f)
        if count > 0:
            print(f"  {count} replacements in {f.relative_to(src_dir.parent)}")
            total_replaced += count
    
    print(f"\nTotal colors replaced: {total_replaced}")


# Third pass colors
COLOR_MAP.update({
    '#f3f3f3': 'var(--color-surface-container-low)',
    '#FFF5F5': 'var(--color-error-bg)',
    '#fff5f5': 'var(--color-error-bg)',
    '#FED7D7': 'var(--color-error-bg)',
    '#fed7d7': 'var(--color-error-bg)',
    '#DC3545': 'var(--color-error)',
    '#dc3545': 'var(--color-error)',
    '#F2FAF6': 'var(--color-success-bg)',
    '#f2faf6': 'var(--color-success-bg)',
    '#FFE0D6': 'var(--color-error-bg)',
    '#ffe0d6': 'var(--color-error-bg)',
    '#FFF5F2': 'var(--color-error-bg)',
    '#fff5f2': 'var(--color-error-bg)',
    '#FF6B35': 'var(--color-error)',
    '#ff6b35': 'var(--color-error)',
    '#C8E6C9': 'var(--color-success)',
    '#c8e6c9': 'var(--color-success)',
    '#F1F8E9': 'var(--color-success-bg)',
    '#f1f8e9': 'var(--color-success-bg)',
    '#F0B273': 'var(--color-warning)',
    '#f0b273': 'var(--color-warning)',
    '#FF8A65': 'var(--color-error)',
    '#ff8a65': 'var(--color-error)',
    '#F0D28A': 'var(--color-warning)',
    '#f0d28a': 'var(--color-warning)',
    '#F3C5BF': 'var(--color-error-bg)',
    '#f3c5bf': 'var(--color-error-bg)',
    '#A855F7': 'var(--color-info)',
    '#a855f7': 'var(--color-info)',
    '#6366F1': 'var(--color-info)',
    '#6366f1': 'var(--color-info)',
    '#818CF8': 'var(--color-info)',
    '#818cf8': 'var(--color-info)',
    '#F5F3FF': 'var(--color-info-bg)',
    '#f5f3ff': 'var(--color-info-bg)',
    '#6D28D9': 'var(--color-info)',
    '#6d28d9': 'var(--color-info)',
    '#EFF6FF': 'var(--color-info-bg)',
    '#eff6ff': 'var(--color-info-bg)',
    '#1D4ED8': 'var(--color-info)',
    '#1d4ed8': 'var(--color-info)',
    '#F5F5F3': 'var(--color-surface-container-low)',
    '#f5f5f3': 'var(--color-surface-container-low)',
    '#E8F0FE': 'var(--color-info-bg)',
    '#e8f0fe': 'var(--color-info-bg)',
    '#1A73E8': 'var(--color-info)',
    '#1a73e8': 'var(--color-info)',
    '#FFF4E5': 'var(--color-warning-bg)',
    '#fff4e5': 'var(--color-warning-bg)',
    '#B45309': 'var(--color-warning)',
    '#b45309': 'var(--color-warning)',
})

# Additional colors added in second pass
COLOR_MAP.update({
    '#F9FAFB': 'var(--color-surface-container-low)',
    '#f9fafb': 'var(--color-surface-container-low)',
    '#1F2937': 'var(--color-on-background)',
    '#1f2937': 'var(--color-on-background)',
    '#D1D5DB': 'var(--color-outline)',
    '#d1d5db': 'var(--color-outline)',
    '#ECFDF5': 'var(--color-success-bg)',
    '#ecfdf5': 'var(--color-success-bg)',
    '#7C3AED': 'var(--color-info)',
    '#7c3aed': 'var(--color-info)',
    '#A7F3D0': 'var(--color-success)',
    '#a7f3d0': 'var(--color-success)',
    '#E2E8F0': 'var(--color-outline)',
    '#e2e8f0': 'var(--color-outline)',
    '#1A936F': 'var(--color-success)',
    '#1a936f': 'var(--color-success)',
    '#10B981': 'var(--color-success)',
    '#10b981': 'var(--color-success)',
    '#065F46': 'var(--color-success)',
    '#065f46': 'var(--color-success)',
    '#BBB': 'var(--color-disabled)',
    '#bbb': 'var(--color-disabled)',
    '#EDE9FE': 'var(--color-info-bg)',
    '#ede9fe': 'var(--color-info-bg)',
    '#4F46E5': 'var(--color-info)',
    '#4f46e5': 'var(--color-info)',
    '#F44336': 'var(--color-error)',
    '#f44336': 'var(--color-error)',
    '#059669': 'var(--color-success)',
    '#C4B5FD': 'var(--color-info-bg)',
    '#c4b5fd': 'var(--color-info-bg)',
    '#DBEAFE': 'var(--color-info-bg)',
    '#dbeafe': 'var(--color-info-bg)',
    '#93C5FD': 'var(--color-info)',
    '#93c5fd': 'var(--color-info)',
    '#FFEDD5': 'var(--color-warning-bg)',
    '#ffedd5': 'var(--color-warning-bg)',
    '#FDBA74': 'var(--color-warning)',
    '#fdba74': 'var(--color-warning)',
    '#EA580C': 'var(--color-warning)',
    '#ea580c': 'var(--color-warning)',
    '#AAA': 'var(--color-disabled)',
    '#aaa': 'var(--color-disabled)',
    '#8B5CF6': 'var(--color-info)',
    '#8b5cf6': 'var(--color-info)',
    '#C2410C': 'var(--color-warning)',
    '#c2410c': 'var(--color-warning)',
    '#F8F8F8': 'var(--color-surface-container-low)',
    '#f8f8f8': 'var(--color-surface-container-low)',
    '#f8f9fa': 'var(--color-surface-container-low)',
    '#7B2D8E': 'var(--color-info)',
    '#7b2d8e': 'var(--color-info)',
    '#004E89': 'var(--color-info)',
    '#004e89': 'var(--color-info)',
    '#3498db': 'var(--color-info)',
    '#9b59b6': 'var(--color-info)',
    '#27ae60': 'var(--color-success)',
    '#9CA3AF': 'var(--color-disabled)',
    '#9ca3af': 'var(--color-disabled)',
    '#F0F0F0': 'var(--color-surface-container-low)',
    '#F44336': 'var(--color-error)',
    '#ba1a1a': 'var(--color-error)',
    '#FF5722': 'var(--color-error)',
    '#ff5722': 'var(--color-error)',
})
if __name__ == '__main__':
    main()

# Additional colors added in second pass
COLOR_MAP.update({
    '#F9FAFB': 'var(--color-surface-container-low)',
    '#f9fafb': 'var(--color-surface-container-low)',
    '#1F2937': 'var(--color-on-background)',
    '#1f2937': 'var(--color-on-background)',
    '#D1D5DB': 'var(--color-outline)',
    '#d1d5db': 'var(--color-outline)',
    '#ECFDF5': 'var(--color-success-bg)',
    '#ecfdf5': 'var(--color-success-bg)',
    '#7C3AED': 'var(--color-info)',
    '#7c3aed': 'var(--color-info)',
    '#A7F3D0': 'var(--color-success)',
    '#a7f3d0': 'var(--color-success)',
    '#E2E8F0': 'var(--color-outline)',
    '#e2e8f0': 'var(--color-outline)',
    '#1A936F': 'var(--color-success)',
    '#1a936f': 'var(--color-success)',
    '#10B981': 'var(--color-success)',
    '#10b981': 'var(--color-success)',
    '#065F46': 'var(--color-success)',
    '#065f46': 'var(--color-success)',
    '#BBB': 'var(--color-disabled)',
    '#bbb': 'var(--color-disabled)',
    '#EDE9FE': 'var(--color-info-bg)',
    '#ede9fe': 'var(--color-info-bg)',
    '#4F46E5': 'var(--color-info)',
    '#4f46e5': 'var(--color-info)',
    '#F44336': 'var(--color-error)',
    '#f44336': 'var(--color-error)',
    '#059669': 'var(--color-success)',
    '#C4B5FD': 'var(--color-info-bg)',
    '#c4b5fd': 'var(--color-info-bg)',
    '#DBEAFE': 'var(--color-info-bg)',
    '#dbeafe': 'var(--color-info-bg)',
    '#93C5FD': 'var(--color-info)',
    '#93c5fd': 'var(--color-info)',
    '#FFEDD5': 'var(--color-warning-bg)',
    '#ffedd5': 'var(--color-warning-bg)',
    '#FDBA74': 'var(--color-warning)',
    '#fdba74': 'var(--color-warning)',
    '#EA580C': 'var(--color-warning)',
    '#ea580c': 'var(--color-warning)',
    '#AAA': 'var(--color-disabled)',
    '#aaa': 'var(--color-disabled)',
    '#8B5CF6': 'var(--color-info)',
    '#8b5cf6': 'var(--color-info)',
    '#C2410C': 'var(--color-warning)',
    '#c2410c': 'var(--color-warning)',
    '#F8F8F8': 'var(--color-surface-container-low)',
    '#f8f8f8': 'var(--color-surface-container-low)',
    '#f8f9fa': 'var(--color-surface-container-low)',
    '#7B2D8E': 'var(--color-info)',
    '#7b2d8e': 'var(--color-info)',
    '#004E89': 'var(--color-info)',
    '#004e89': 'var(--color-info)',
    '#3498db': 'var(--color-info)',
    '#9b59b6': 'var(--color-info)',
    '#27ae60': 'var(--color-success)',
    '#9CA3AF': 'var(--color-disabled)',
    '#9ca3af': 'var(--color-disabled)',
    '#F0F0F0': 'var(--color-surface-container-low)',
    '#F44336': 'var(--color-error)',
    '#ba1a1a': 'var(--color-error)',
    '#FF5722': 'var(--color-error)',
    '#ff5722': 'var(--color-error)',
})

# Third pass colors
COLOR_MAP.update({
    '#f3f3f3': 'var(--color-surface-container-low)',
    '#FFF5F5': 'var(--color-error-bg)',
    '#fff5f5': 'var(--color-error-bg)',
    '#FED7D7': 'var(--color-error-bg)',
    '#fed7d7': 'var(--color-error-bg)',
    '#DC3545': 'var(--color-error)',
    '#dc3545': 'var(--color-error)',
    '#F2FAF6': 'var(--color-success-bg)',
    '#f2faf6': 'var(--color-success-bg)',
    '#FFE0D6': 'var(--color-error-bg)',
    '#ffe0d6': 'var(--color-error-bg)',
    '#FFF5F2': 'var(--color-error-bg)',
    '#fff5f2': 'var(--color-error-bg)',
    '#FF6B35': 'var(--color-error)',
    '#ff6b35': 'var(--color-error)',
    '#C8E6C9': 'var(--color-success)',
    '#c8e6c9': 'var(--color-success)',
    '#F1F8E9': 'var(--color-success-bg)',
    '#f1f8e9': 'var(--color-success-bg)',
    '#F0B273': 'var(--color-warning)',
    '#f0b273': 'var(--color-warning)',
    '#FF8A65': 'var(--color-error)',
    '#ff8a65': 'var(--color-error)',
    '#F0D28A': 'var(--color-warning)',
    '#f0d28a': 'var(--color-warning)',
    '#F3C5BF': 'var(--color-error-bg)',
    '#f3c5bf': 'var(--color-error-bg)',
    '#A855F7': 'var(--color-info)',
    '#a855f7': 'var(--color-info)',
    '#6366F1': 'var(--color-info)',
    '#6366f1': 'var(--color-info)',
    '#818CF8': 'var(--color-info)',
    '#818cf8': 'var(--color-info)',
    '#F5F3FF': 'var(--color-info-bg)',
    '#f5f3ff': 'var(--color-info-bg)',
    '#6D28D9': 'var(--color-info)',
    '#6d28d9': 'var(--color-info)',
    '#EFF6FF': 'var(--color-info-bg)',
    '#eff6ff': 'var(--color-info-bg)',
    '#1D4ED8': 'var(--color-info)',
    '#1d4ed8': 'var(--color-info)',
    '#F5F5F3': 'var(--color-surface-container-low)',
    '#f5f5f3': 'var(--color-surface-container-low)',
    '#E8F0FE': 'var(--color-info-bg)',
    '#e8f0fe': 'var(--color-info-bg)',
    '#1A73E8': 'var(--color-info)',
    '#1a73e8': 'var(--color-info)',
    '#FFF4E5': 'var(--color-warning-bg)',
    '#fff4e5': 'var(--color-warning-bg)',
    '#B45309': 'var(--color-warning)',
    '#b45309': 'var(--color-warning)',
})
