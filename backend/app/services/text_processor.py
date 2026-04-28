"""
文本处理服务
"""

import hashlib
import math
from typing import List, Optional
from ..config import Config
from ..utils.file_parser import FileParser, split_text_into_chunks


class TextProcessor:
    """文本处理器"""
    
    @staticmethod
    def extract_from_files(file_paths: List[str]) -> str:
        """从多个文件提取文本"""
        return FileParser.extract_from_multiple(file_paths)
    
    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = Config.DEFAULT_CHUNK_SIZE,
        overlap: int = Config.DEFAULT_CHUNK_OVERLAP,
    ) -> List[str]:
        """
        分割文本
        
        Args:
            text: 原始文本
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            文本块列表
        """
        return split_text_into_chunks(text, chunk_size, overlap)
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        预处理文本
        - 移除多余空白
        - 标准化换行
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        import re
        
        # 标准化换行
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除连续空行（保留最多两个换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    @staticmethod
    def deduplicate_chunks(chunks: List[str]) -> List[str]:
        """Remove exact duplicate chunks while preserving order of first occurrence."""
        seen = set()
        result = []
        for chunk in chunks:
            if chunk not in seen:
                seen.add(chunk)
                result.append(chunk)
        return result

    @staticmethod
    def compute_signature(data: str) -> str:
        """Return a SHA-256 hex digest of the input string."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def diff_chunks(current_chunks: List[str], stored_signatures: List[str]) -> tuple[List[str], List[str]]:
        """
        Compare current chunks against stored signatures.
        
        Returns:
            Tuple of (changed_chunks, new_signatures)
        """
        new_signatures = [TextProcessor.compute_signature(chunk) for chunk in current_chunks]
        stored_set = set(stored_signatures)
        changed = [
            chunk for chunk, sig in zip(current_chunks, new_signatures)
            if sig not in stored_set
        ]
        return changed, new_signatures

    @staticmethod
    def get_text_stats(text: str) -> dict:
        """获取文本统计信息"""
        return {
            "total_chars": len(text),
            "total_lines": text.count('\n') + 1,
            "total_words": len(text.split()),
        }

    @staticmethod
    def estimate_ingestion_cost(
        text: str,
        chunk_size: int,
        overlap: int,
        byte_step: int = 350,
        warning_credit_threshold: int = 25,
    ) -> dict:
        """Estimate chunk counts, UTF-8 bytes, and credits using production split logic."""
        chunks = TextProcessor.split_text(text, chunk_size, overlap)
        byte_sizes = [len(chunk.encode("utf-8")) for chunk in chunks]
        estimated_credits = sum(max(1, math.ceil(size / byte_step)) for size in byte_sizes)

        return {
            "chunk_count": len(chunks),
            "estimated_total_chars": len(text),
            "estimated_total_bytes": sum(byte_sizes),
            "estimated_credits": estimated_credits,
            "warning_level": "warning" if estimated_credits >= warning_credit_threshold else "none",
        }
