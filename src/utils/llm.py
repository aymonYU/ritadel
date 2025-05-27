"""Helper functions for LLM"""

import json
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel
from utils.progress import progress

T = TypeVar('T', bound=BaseModel)

# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def call_llm(
    prompt: Any,
    pydantic_model: Type[T],
    agent_name: Optional[str] = None,
    max_retries: int = 3,
    default_factory = None
) -> T:
    """
    Makes an LLM call with retry logic. Output is structured using the provided Pydantic model.
    模型调用函数，包含重试逻辑。输出将使用指定的 Pydantic 模型进行结构化。
    
    Args:
        prompt: The prompt to send to the LLM (要发送给 LLM 的提示)
        # model_name: Name of the model to use (不再需要)
        # model_provider: Provider of the model (不再需要)
        pydantic_model: The Pydantic model class to structure the output (用于结构化输出的 Pydantic 模型类)
        agent_name: Optional name of the agent for progress updates (用于进度更新的可选代理名称)
        max_retries: Maximum number of retries (default: 3) (最大重试次数，默认为 3)
        default_factory: Optional factory function to create default response on failure (可选的默认响应工厂函数，在失败时使用)
        
    Returns:
        An instance of the specified Pydantic model (指定 Pydantic 模型的实例)
    """
    # 移除了 get_model_info 的导入和使用，因为模型已固定
    # Removed import and usage of get_model_info as the model is fixed
    from llm.models import get_model
    
    # 调用 get_model 时不再需要参数，它将始终返回 GPT-4o 实例
    # No parameters needed when calling get_model, it will always return a GPT-4o instance
    llm = get_model() 
    
    # 由于模型固定为 GPT-4o (非 Deepseek)，我们总是使用结构化输出
    # As the model is fixed to GPT-4o (not Deepseek), we always use structured output
    llm = llm.with_structured_output(
        pydantic_model,
        method="json_mode",
    )
    
    # Call the LLM with retries (带重试逻辑调用 LLM)
    for attempt in range(max_retries):
        try:
            # Call the LLM (调用 LLM)
            result = llm.invoke(prompt)
            
            # 移除了 Deepseek 特定的 JSON 解析逻辑，因为不再支持 Deepseek 模型
            # Removed Deepseek-specific JSON parsing logic as Deepseek models are no longer supported
            # if model_info and model_info.is_deepseek():
            #     parsed_result = extract_json_from_deepseek_response(result.content)
            #     if parsed_result:
            #         return pydantic_model(**parsed_result)
            # else:
            return result # 直接返回结构化输出结果 (Directly return the structured output result)
                
        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Error - retry {attempt + 1}/{max_retries}")
            
            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts: {e}")
                # Use default_factory if provided, otherwise create a basic default
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    # This should never be reached due to the retry logic above
    return create_default_response(pydantic_model)

def create_default_response(model_class: Type[T]) -> T:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}
        else:
            # For other types (like Literal), try to use the first allowed value
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None
    
    return model_class(**default_values)

def extract_json_from_deepseek_response(content: str) -> Optional[dict]:
    """Extracts JSON from Deepseek's markdown-formatted response."""
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7:]  # Skip past ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from Deepseek response: {e}")
    return None
