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
def get_model(model_name: str = "gpt-4o") -> ChatOpenAI | None: # model_provider 参数已移除，model_name 默认为 "gpt-4o" (model_provider parameter removed, model_name defaults to "gpt-4o")
    # 移除了 Groq, Anthropic, 和 Gemini 的逻辑，因为不再支持这些模型提供商
    # Removed logic for Groq, Anthropic, and Gemini as they are no longer supported

    # 只保留 OpenAI 的逻辑
    # Only keep OpenAI logic
    # 获取并验证 API 密钥
    # Get and validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # 打印错误到控制台
        # Print error to console
        print(f"API Key Error: Please make sure OPENAI_API_KEY is set in your .env file.") # API 密钥错误：请确保 OPENAI_API_KEY 已在您的 .env 文件中设置。 (API key error: Please ensure OPENAI_API_KEY is set in your .env file.)
        raise ValueError("OpenAI API key not found.  Please make sure OPENAI_API_KEY is set in your .env file.") # 未找到 OpenAI API 密钥。请确保 OPENAI_API_KEY 已在您的 .env 文件中设置。 (OpenAI API key not found. Please ensure OPENAI_API_KEY is set in your .env file.)
    # 确保我们总是使用 "gpt-4o" 模型，忽略传入的 model_name 参数，或者验证它是否为 "gpt-4o"
    # Ensure we always use the "gpt-4o" model, ignoring the passed model_name, or validate it is "gpt-4o"
    # 为了简单起见，我们这里直接使用 "gpt-4o"，并使函数签名中的 model_name 参数的意义更偏向于一个固定值。
    # For simplicity, we directly use "gpt-4o" here, and the model_name parameter in the function signature becomes more of a fixed value.
    return ChatOpenAI(model="gpt-4o", api_key=api_key)

# 确保文件末尾有一个换行符
# Ensure there is a newline at the end of the file