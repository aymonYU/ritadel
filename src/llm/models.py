import os
# from langchain_anthropic import ChatAnthropic # 不再需要 Anthropic (Anthropic is no longer needed)
# from langchain_groq import ChatGroq # 不再需要 Groq (Groq is no longer needed)
from langchain_openai import ChatOpenAI
# from enum import Enum # Enum 不再需要，因为 ModelProvider 被移除了 (Enum is no longer needed as ModelProvider is removed)
from pydantic import BaseModel
from typing import Tuple

# ModelProvider 枚举类已被移除，因为我们现在只支持 OpenAI 模型
# ModelProvider enum has been removed as we now only support OpenAI models
# class ModelProvider(str, Enum):
#     """Enum for supported LLM providers"""
#     OPENAI = "OpenAI"
#     GROQ = "Groq"
#     ANTHROPIC = "Anthropic"
#     GEMINI = "Gemini"  # Add Gemini provider


class LLMModel(BaseModel):
    """Represents an LLM model configuration"""
    display_name: str # 模型的显示名称 (Display name of the model)
    model_name: str # 模型的实际名称 (Actual name of the model)
    # provider: ModelProvider # provider 字段已被移除，因为我们现在只支持 OpenAI (provider field removed as we only support OpenAI)

    def to_choice_tuple(self) -> Tuple[str, str, str]:
        """Convert to format needed for questionary choices"""
        # 返回元组，其中第三个元素硬编码为 "OpenAI"
        # Return a tuple, where the third element is hardcoded to "OpenAI"
        return (self.display_name, self.model_name, "OpenAI")
    
    def is_deepseek(self) -> bool:
        """Check if the model is a DeepSeek model"""
        # DeepSeek 模型不再支持，此函数可以直接返回 False 或移除
        # DeepSeek models are no longer supported, this function can return False or be removed.
        return False


# 定义可用模型 - 现在只硬编码 OpenAI GPT-4o
# Define available models - now hardcoded to only OpenAI GPT-4o
AVAILABLE_MODELS = [
    LLMModel(
        display_name="[openai] gpt-4o",
        model_name="gpt-4o",
        # provider=ModelProvider.OPENAI # provider 字段已移除 (provider field removed)
    ),
]

# 以 UI 期望的格式创建 LLM_ORDER - 同样只包含 GPT-4o
# Create LLM_ORDER in the format expected by the UI - also only gpt-4o
LLM_ORDER = [("[openai] gpt-4o", "gpt-4o", "OpenAI")] # 直接硬编码 (Directly hardcoded)

# get_model_info 函数已移除，因为它不再被使用 (AVAILABLE_MODELS 只有一个模型)
# get_model_info function removed as it's no longer used (AVAILABLE_MODELS has only one model)
# def get_model_info(model_name: str) -> LLMModel | None:
#     """Get model information by model_name"""
#     return next((model for model in AVAILABLE_MODELS if model.model_name == model_name), None)

# 修改 get_model 函数，使其只支持 OpenAI GPT-4o
# Modify the get_model function to only support OpenAI GPT-4o
def get_model() -> ChatOpenAI | None: # model_provider 参数已移除，model_name 默认为 "gpt-4o" (model_provider parameter removed, model_name defaults to "gpt-4o")
    # 移除了 Groq, Anthropic, 和 Gemini 的逻辑，因为不再支持这些模型提供商
    # Removed logic for Groq, Anthropic, and Gemini as they are no longer supported

    model = ChatOpenAI(
        model=os.getenv("AI_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),               
        base_url=os.getenv("BASE_URL")
    )

    return model

# 确保文件末尾有一个换行符
# Ensure there is a newline at the end of the file