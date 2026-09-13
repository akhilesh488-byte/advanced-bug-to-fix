from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    iterations: int

class Agent:
    def __init__(self, model, tools, system_message = "", max_iterations = 30):
        self.system_message = system_message
        graph = StateGraph(AgentState)
        self.model = model.bind_tools(list(tools.values()))
        self.max_iterations = max_iterations
        self.tools = tools
        graph.add_node("llm", self.call_llm)
        graph.add_node("report_write_node", self.report_write_node)
        graph.add_node("other_actions", self.call_tool)
        graph.add_conditional_edges(
            "llm",
            self.action_exists
        )
        graph.add_edge("other_actions", "llm")
        graph.add_edge("report_write_node", END)
        graph.set_entry_point("llm")
        self.graph = graph.compile()

    def call_llm(self, state: AgentState):
        messages = state["messages"]
        if self.system_message:
            messages = [SystemMessage(content=self.system_message)] + messages

        llm_response = self.model.invoke(messages)
        return {"messages": [llm_response], "iterations": state.get("iterations", 0) + 1}

    def call_tool(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []

        for t in tool_calls:
            print(f"calling: {t}")
            if not t["name"] in self.tools:
                print(f"tool named {t['name']} does not exist")
                tool_response = "wrong tool name, retry"
            else:
                tool_response = self.tools[t["name"]].invoke(t["args"])
            results.append(ToolMessage(content = str(tool_response), tool_call_id = t["id"]))

        print("back to the llm")
        return {"messages": results}

    def action_exists(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls

        if len(tool_calls) > 0: 
            if state.get("iterations", 0) >= self.max_iterations:
                return END

            elif tool_calls[0]["name"] == "report_write":
                return "report_write_node"
            
            else:
                return "other_actions"

        else:
            return END

    def report_write_node(self, state:AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        t = tool_calls[0]
        print(f"calling: {t['name']}")
        tool_response = self.tools[t["name"]].invoke(t["args"])
        results.append(ToolMessage(content = str(tool_response), tool_call_id = t["id"]))
        
        print("back to the llm")
        return {"messages": results}   
