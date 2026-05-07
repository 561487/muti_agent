import os
MODEL ="qwen2.5-72b-instruct"
MODEL_BASE_URL ='https://dashscope.aliyuncs.com/compatible-mode/v1'
MODEL_API_KEY=os.getenv("api_key")


os.environ["TAVILY_API_KEY"] = "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"
os.environ["MPLBACKEND"]="Agg"
