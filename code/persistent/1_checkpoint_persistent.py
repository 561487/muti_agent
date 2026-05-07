import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, START, END
import io
from PIL import Image


async def main():
    #########################图模式构建####################################
    builder = StateGraph(int)
    builder.add_node("add_one", lambda x: x + 1)
    builder.set_entry_point("add_one")
    builder.set_finish_point("add_one")

    #######################构建db并写入####################################
    # 定义checkpointer进行异步图信息存储
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:

        # 基于checkpointer定义图
        graph = builder.compile(checkpointer=memory)

        # # 画图
        # img = graph.get_graph().draw_mermaid_png()
        # image = Image.open(io.BytesIO(img))
        # image.save("./checkpoint_persistent.png")

        # 异步图调用
        coro = graph.ainvoke(1, {"configurable": {"thread_id": "thread-1"}})
        print(await asyncio.gather(coro))

asyncio.run(main())