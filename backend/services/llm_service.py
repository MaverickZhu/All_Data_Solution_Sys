"""
LLM 服务
负责与本地部署的大语言模型进行交互，例如通过Ollama。
"""
import logging
import re
import asyncio
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger("service")

class LLMService:
    """
    提供与大语言模型交互的服务。
    """
    
    DEFAULT_TIMEOUT = 30  # 默认30秒超时
    MAX_TIMEOUT = 120     # 最大120秒超时
    
    @staticmethod
    async def generate_summary(text_content: str) -> str:
        """
        使用本地Ollama中的qwen模型为给定文本生成摘要。

        Args:
            text_content: 需要生成摘要的原始文本。

        Returns:
            生成的摘要文本。如果生成失败，则返回空字符串。
        """
        if not text_content or not text_content.strip():
            return ""

        try:
            logger.info("Initializing LLM for summarization (model: deepseek-r1:8b, think=disabled)...")
            # 初始化Ollama LLM，明确指向在主机上运行的Ollama服务
            llm = ChatOllama(
                base_url="http://host.docker.internal:11435",
                model="deepseek-r1:8b", 
                temperature=0.6,
                timeout=30,
                # 关闭think模式，直接输出结果
                format="json",
                options={
                    "num_predict": 512,
                    "stop": ["<think>", "</think>"],
                    "temperature": 0.6
                }
            )

            # 创建一个更强大、更具指令性的专业摘要提示模板
            prompt_template = """
            <|system|>
            你是一个高度专业化的文本摘要引擎。你的唯一任务是将用户提供的文本压缩并提炼成一段精简、流畅且信息密度极高的摘要。
            你必须严格遵守以下规则：
            1.  摘要必须保留原文的核心观点和关键信息。
            2.  摘要必须是对原文的重新表述和浓缩，绝不能直接复制原文的句子。
            3.  最终输出的摘要长度必须严格控制在200字以内。
            4.  你的输出只能包含摘要文本本身，禁止添加任何前缀、标题或解释性文字（例如，不要说"这是摘要："）。

            <|user|>
            请为以下文本生成摘要：

            {input}
            """
            prompt = ChatPromptTemplate.from_template(prompt_template)
            
            # 创建一个解析器，用于获取模型的纯文本输出
            output_parser = StrOutputParser()

            # 构建处理链
            chain = prompt | llm | output_parser

            logger.info("Invoking LLM chain to generate summary...")
            # 异步调用链，添加超时保护
            summary = await asyncio.wait_for(
                chain.ainvoke({"input": text_content}), 
                timeout=60
            )
            logger.info("Successfully generated summary from LLM.")

            # 清理模型输出中可能包含的<think>标签和内容
            cleaned_summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL)

            return cleaned_summary.strip()

        except asyncio.TimeoutError:
            logger.error("LLM summarization timed out after 60 seconds")
            return ""
        except Exception as e:
            logger.error(f"Failed to generate summary with LLM (deepseek-r1:8b): {e}", exc_info=True)
            return "" # 在失败时返回空字符串，以便触发降级逻辑 

    @staticmethod
    async def generate_response(prompt: str, temperature: float = 0.7, timeout: int = None) -> str:
        """
        使用本地Ollama中的大模型为给定提示生成响应。
        这是一个通用的文本生成方法，被视频分析服务广泛使用。

        Args:
            prompt: 输入的提示文本
            temperature: 生成温度，控制输出的随机性
            timeout: 超时时间（秒），默认30秒

        Returns:
            生成的响应文本。如果生成失败，则返回空字符串。
        """
        if not prompt or not prompt.strip():
            return ""

        # 设置超时时间
        if timeout is None:
            timeout = LLMService.DEFAULT_TIMEOUT
        timeout = min(timeout, LLMService.MAX_TIMEOUT)  # 限制最大超时时间

        try:
            logger.info(f"Initializing LLM for response generation (model: deepseek-r1:8b, think=disabled, timeout: {timeout}s)...")
            # 初始化Ollama LLM，明确指向在主机上运行的Ollama服务
            llm = ChatOllama(
                base_url="http://host.docker.internal:11435",
                model="deepseek-r1:8b", 
                temperature=temperature,
                timeout=timeout,
                # 关闭think模式，直接输出结果
                options={
                    "num_predict": 1024,
                    "stop": ["<think>", "</think>"],
                    "temperature": temperature
                }
            )

            # 直接创建消息，不使用复杂的模板
            messages = [
                ("system", "你是一个专业的AI助手，能够理解和分析各种内容。请根据用户的要求提供准确、有用的回答。"),
                ("user", prompt)
            ]
            
            logger.info(f"Invoking LLM to generate response (timeout: {timeout}s)...")
            # 直接调用LLM，添加asyncio超时保护
            response = await asyncio.wait_for(
                llm.ainvoke(messages), 
                timeout=timeout
            )
            logger.info("Successfully generated response from LLM.")

            # 获取响应内容
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # 清理模型输出中可能包含的<think>标签和内容
            cleaned_response = re.sub(r"<think>.*?</think>", "", response_content, flags=re.DOTALL)

            return cleaned_response.strip()

        except asyncio.TimeoutError:
            logger.error(f"LLM response generation timed out after {timeout} seconds")
            return ""
        except Exception as e:
            logger.error(f"Failed to generate response with LLM (deepseek-r1:8b): {e}", exc_info=True)
            return "" # 在失败时返回空字符串 