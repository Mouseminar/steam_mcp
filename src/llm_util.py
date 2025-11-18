import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY", default="sk-xxx"),
    base_url=os.getenv("DASHSCOPE_BASE_URL", default="https://dashscope.aliyuncs.com/compatible-mode/v1"),
    timeout=300.0,  # 设置5分钟超时，避免LLM调用超时
    max_retries=2,  # 失败时重试2次
)

def llm_gen(messages:list[dict], model:str):
    completion = client.chat.completions.create(
        model = model,
        messages = messages,
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        extra_body = {"enable_thinking": False},
    )
    result_json = completion.model_dump_json()
    # print(result_json)
    return result_json


if __name__ == "__main__":
   llm_gen()

