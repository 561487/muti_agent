from utils import *
from research_team import *
from document_authoring import *


######################### 主控智能体定义(顶层架构) ####################################



def call_research_team(state: State) -> Command[Literal["supervisor"]]:
    """
    调用研究团队结果并返回给大boss
    """
    response = research_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="research_team"
                )
            ]
        },
        goto="supervisor",
    )


def call_paper_writing_team(state: State) -> Command[Literal["supervisor"]]:
    """
    调用写作团队结果并返回给大boss
    """
    response = paper_writing_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="writing_team"
                )
            ]
        },
        goto="supervisor",
    )


############################### 图模式构造 ###################################
super_builder = StateGraph(State)
# 团队大boss
schema={
    "research_team":{"prompt":"进行找寻资料的智能体，可以进行网上搜索和爬虫下载相关资料。不能做其他事情，不要进行联想","node":call_research_team},
    "writing_team":{"prompt":"将相关内容进行文档写作，写成报告并根据指定文件名保存在磁盘。不能做其他事情，不要进行联想","node":call_paper_writing_team},
}


teams_supervisor_node = make_supervisor_node(llm, [ s for s in schema.keys()])

super_builder.add_node("supervisor", teams_supervisor_node)
super_builder.add_node("research_team", schema["research_team"]["node"])
super_builder.add_node("writing_team", schema["writing_team"]["node"])

super_builder.add_edge(START, "supervisor")
super_graph = super_builder.compile()

# img = super_graph.get_graph().draw_mermaid_png()
# with open("super_graph.jpg", "wb") as f:
#     f.write(img)
# import io
# from PIL import Image
# img = super_graph.get_graph().draw_mermaid_png()
# image = Image.open(io.BytesIO(img))
# image.save("./hierarchy.png")



############################# 图运行示例 #####################################
def supervisor_example_write():
    for s in paper_writing_graph.stream(
        {
            "messages": [
                (
                    "user",
                    "写一个关于猫咪的诗歌大纲，然后将诗写入文件中。",
                )
            ]
        },
        {"recursion_limit": 100},
        subgraphs=SUBGRAPH
    ):
        print(s)
        print("---")


def supervisor_example_research():
    for s in research_graph.stream(
        {"messages": [("user", "从网上搜一些GPT5的新闻,抓取相关url并进行总结")]},
        {"recursion_limit": 100},
        subgraphs=SUBGRAPH
    ):
        print(s)
        print("---")


def supervisor_example_top():
    for s in super_graph.stream(
        {
            "messages": [
                # ("user", "从网上搜一些GPT5的新闻,抓取相关url并进行总结，并将爬取的内容写成总结报告。结果保存到gpt5_document.txt文件中。写完报告后，停止流程")
                ("user","写一个关于猫咪的诗歌大纲，然后将诗写入文件中。")
            ],
        },
        {"recursion_limit": 150},
        subgraphs=True
    ):
        print("主智能体",s)
        print("---")


#supervisor_example_write()
#supervisor_example_research()
supervisor_example_top()

