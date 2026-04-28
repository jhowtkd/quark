"""
LLM客户端封装
统一使用OpenAI格式调用
支持 rate limit retry (429 errors)
"""

import json
import re
import time
import random
from typing import Optional, Dict, Any, List
from openai import OpenAI, RateLimitError

from ..config import Config


class LLMClient:
    """LLM客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 5,
        initial_retry_delay: float = 2.0
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY não configurada")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0  # 2 minute timeout for LLM calls
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        observation: Optional[Any] = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            observation: Langfuse span/observation to attach this generation to (optional).
            generation_name: Name for this generation in Langfuse (optional).
            generation_metadata: Extra metadata dict for this generation (optional).
            
        Returns:
            响应文本字符串
        """
        last_error = None
        start_time = time.perf_counter()
        span = None

        # If an observation is provided, open a generation span
        if observation is not None:
            name = generation_name or "llm_chat"
            span = observation.start_span(
                name=name,
                metadata={
                    "model": self.model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **(generation_metadata or {}),
                },
            )
            span.update(input={"messages": messages})
        delay = self.initial_retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = self.client.chat.completions.create(**kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # Extract output text
                output_text = response.choices[0].message.content
                
                # Extract usage if available
                usage_dict = {}
                if hasattr(response, "usage") and response.usage is not None:
                    usage_dict = {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                        "total_tokens": getattr(response.usage, "total_tokens", 0),
                    }
                
                # Record observation results
                if span is not None:
                    update_kwargs = {
                        "output": output_text,
                        "latency_ms": round(latency_ms, 2),
                    }
                    if usage_dict:
                        update_kwargs["usage"] = usage_dict
                    span.update(**update_kwargs)
                    span.end()
                
                return output_text
                
            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries:
                    # 计算延迟：指数退避 + 抖动
                    current_delay = min(delay * (2 ** attempt), 60.0)
                    jitter = current_delay * (0.5 + random.random() * 0.5)
                    wait_time = min(jitter, 60.0)
                    print(f"[LLMClient] Rate limit hit (attempt {attempt + 1}/{self.max_retries + 1}), waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                else:
                    if span is not None:
                        span.update(
                            status_message=f"rate_limit_exhausted: {str(e)}",
                            output="",
                        )
                        span.end()
                    raise
                    
            except Exception as e:
                last_error = e
                if span is not None:
                    span.update(
                        status_message=f"error: {str(e)}",
                        output="",
                    )
                    span.end()
                # 其他错误不重试
                raise
        
        raise last_error
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        observation: Optional[Any] = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            observation: Langfuse span/observation (optional).
            generation_name: Name for this generation in Langfuse (optional).
            generation_metadata: Extra metadata dict (optional).
            
        Returns:
            解析后的JSON对象
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            observation=observation,
            generation_name=generation_name,
            generation_metadata=generation_metadata,
        )
        cleaned_response = self._extract_json_payload(response)

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"JSON格式无效 / JSON retornado pelo LLM é inválido: {cleaned_response}")

    def _extract_json_payload(self, response: str) -> str:
        """Extract JSON payload from providers that prepend reasoning or fenced code blocks."""
        cleaned_response = response.strip()
        cleaned_response = re.sub(
            r'^\s*<think>.*?</think>\s*',
            '',
            cleaned_response,
            flags=re.IGNORECASE | re.DOTALL,
        )

        fenced_match = re.search(
            r'```(?:json)?\s*(\{.*\})\s*```',
            cleaned_response,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced_match:
            return fenced_match.group(1).strip()

        json_match = re.search(r'(\{.*\})', cleaned_response, flags=re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        return cleaned_response.strip()
