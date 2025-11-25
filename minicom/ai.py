import asyncio
from llama_cpp import Llama

print("Loading model...")
llm = Llama(model_path="./model_cache/gemma-3-270m-it-UD-Q2_K_XL.gguf", )


async def reply(message):
    response = await asyncio.to_thread(
        llm.create_chat_completion,
        messages=[{
            "role":
            "system",
            "content":
            "You are a customer service assistant and you have to help user with any query they have."
        }, {
            "role": "user",
            "content": message
        }])
    return response["choices"][0]["message"]["content"]
