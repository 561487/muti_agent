from utils import *
from research_team import *
from document_authoring import *


######################### 主控智能体定义(顶层架构) ####################################

# 团队大boss
teams_supervisor_node = make_supervisor_node(llm, ["research_team", "writing_team"])


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
super_builder.add_node("supervisor", teams_supervisor_node)
super_builder.add_node("research_team", call_research_team)
super_builder.add_node("writing_team", call_paper_writing_team)

super_builder.add_edge(START, "supervisor")
super_graph = super_builder.compile()


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
        {"messages": [("user", "泰勒·斯威夫特的下一次巡演是什么时候？")]},
        {"recursion_limit": 100},
        subgraphs=SUBGRAPH
    ):
        print(s)
        print("---")


def supervisor_example_top():
    for s in super_graph.stream(
        {
            "messages": [
                ("user", "研究AI代理并写一份简短的报告，保存到research_document.txt文件中。")
            ],
        },
        {"recursion_limit": 150},
        subgraphs=True
    ):
        print(s)
        print("---")


# supervisor_example_write()
# supervisor_example_research()
supervisor_example_top()

