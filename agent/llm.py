import ollama

# Maximum generation tokens per call — prevents runaway thinking loops
MAX_PREDICT_TOKENS = 2048


class LLMClient:
    def __init__(self, model="qwen3"):
        self.model = model

    def call(self, messages: list, tools: list = None) -> dict:
        """
        messages: list of {"role": "user"/"assistant"/"tool", "content": "..."}
        tools: list of tool dicts in Ollama format
        returns the full response dict from Ollama
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "options": {"num_predict": MAX_PREDICT_TOKENS},
        }
        if tools:
            kwargs["tools"] = tools
        response = ollama.chat(**kwargs)
        return response
