import os
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from typing import Dict, Optional, Annotated, List, Literal
from typing_extensions import TypedDict
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from pathlib import Path
from tempfile import TemporaryDirectory
from langchain_experimental.utilities import PythonREPL
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START
from config import MODEL_API_KEY, MODEL_BASE_URL, MODEL


DEBUG = False
SUBGRAPH = False

######################### 模型定义部分 ####################################
llm = ChatOpenAI(
    model=MODEL,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API_KEY
)


######################## 状态和主管节点定义 ##########################
class State(MessagesState):
    next: str


def make_supervisor_node(llm: BaseChatModel, members: list[str]):
    """
    各层级主控智能体创建，负责各子智能体之间的路由任务
    """
    system_prompt = (
        "你是一个主管，负责管理以下工作者之间的对话："
        f"{members}。根据以下用户请求，"
        "响应下一个要行动的工作者。每个工作者将执行一项任务并响应他们的结果和状态。"
        "完成后，回复FINISH。"
        "请使用json格式，格式为{'next': 'worker_name'}."
    )
    print (system_prompt)
    
    class Router(TypedDict):
        """
        路由到下一个工作者。如果不需要任何工作者，路由到FINISH
        """
        next: str

    def supervisor_node(state: State) -> Command[str]:
        """基于大模型的路由器"""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node


