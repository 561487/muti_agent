from utils import *


######################### 工具定义部分 ####################################

# 搜索工具 https://app.tavily.com/home
tavily_tool = TavilySearchResults(max_results=5)

# 网页抓取工具
@tool
def scrape_webpages(urls: List[str]) -> str:
    """
    使用requests和bs4去抓取提供的网页以获取更细节的信息
    """
    loader = WebBaseLoader(urls)
    docs = loader.load()
    return "\n\n".join(
        [
            f'<Document name="{doc.metadata.get("title", "")}">\n{doc.page_content}\n</Document>'
            for doc in docs
        ]
    )


################################# 智能体节点创建 #####################################

# 搜索智能体
search_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    debug=DEBUG
)


def search_node(state: State) -> Command[Literal["supervisor"]]:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="search")
            ]
        },
        # 所有工作者完成工作后都要返回supervisor节点
        goto="supervisor",
    )

# 网页抓取智能体
web_scraper_agent = create_react_agent(
    llm,
    tools=[scrape_webpages],
    debug=DEBUG
)


def web_scraper_node(state: State) -> Command[Literal["supervisor"]]:
    result = web_scraper_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="web_scraper")
            ]
        },
        # 所有工作者完成工作后都要返回supervisor节点
        goto="supervisor",
    )

############################### 图模式构造 ###################################
research_supervisor_node = make_supervisor_node(llm, ["search", "web_scraper"])
research_builder = StateGraph(State)
research_builder.add_node("supervisor", research_supervisor_node)
research_builder.add_node("search", search_node)
research_builder.add_node("web_scraper", web_scraper_node)

research_builder.add_edge(START, "supervisor")
research_graph = research_builder.compile()
