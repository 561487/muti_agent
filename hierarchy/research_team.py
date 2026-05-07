from utils import *
import requests
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, AnyMessage
######################### 工具定义部分 ####################################
@tool
def my_search(query):
    """
        互联网搜索工具
       "A search engine optimized for comprehensive, accurate, and trusted results. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. "
        "This returns only the answer - not the original source data."
    """
    # 请求配置
    url = url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer sk-4565569ba65d42c28c0bd56f019b9706",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,  # 搜索关键词
        "summary": True,               # 显示摘要
        "count": 5,                    # 返回5条结果
        "page": 1                      # 第一页
    }

    # 发送请求
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    urls=[]
    contents=[]
    # 解析结果
    if response.status_code == 200:
        results = response.json()
        for item in results["data"]["webPages"]["value"]:
            # print(f"标题：{item['name']}")
            # print(f"链接：{item['url']}")
            # print(f"摘要：{item['snippet']}\n")
            #urls.append(item["url"])
            #contents.append({"title":item['name'],"url":item['url'],"content":item['snippet']})
            contents.append({"url":item['url']})
    else:
        print(f"请求失败！错误码：{response.status_code}, 详情：{response.text}")
    print ("搜索出如下网页")
    print (contents)
    return contents 
#search()
 


# 搜索工具 https://app.tavily.com/home
# tavily_tool = TavilySearchResults(max_results=5)
# r=tavily_tool.invoke({"args": {'query': 'who won the last french open'}, "type": "tool_call", "id": "foo", "name": "tavily"})
# print (r.content)
# print (type(r))
# r=my_search.invoke({"args": {'query': 'who won the last french open'}, "type": "tool_call", "id": "foo", "name": "tavily"})
# print (r.content)
# print (type(r))
# asd

# 网页抓取工具
@tool
def scrape_webpages(urls: List[str]) -> str:
    """
    使用requests和bs4去抓取提供的网页以获取更细节的信息
    """
    print ("爬虫抓取如下网页")
    print (urls)
 
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
    tools=[my_search],
    debug=DEBUG
)
# result=search_agent.invoke({"messages":"今天有什么新闻"})
# print (result)

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
