import os
from typing import TypedDict, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langgraph.graph import StateGraph, END
from graph.Agent import Agent
from tools.clone_repo import clone_repo
from tools.list_files import list_files
from tools.edit_file import edit_file
from tools.read_file import read_file
from tools.report_write import report_write
from tools.run_shell import run_shell
from tools.sandbox_manager import create_branch, discard_attempt, commit_changes
from tools.search_code import search_code
from tools.write_file import write_file
from tools.submit_context import submit_context

class PipelineState(TypedDict):
    job_id: int
    clone_success: bool
    target_repo_path: Optional[str] 
    target_files: Optional[list[str]]
    report_status: str
    report_files: list[str]
    user_prompt: str
    git_url: str
    baseline_output: Optional[str]
    solution_branch_path: Optional[str]
    llm_failure_message: Optional[str]
    api_status: bool
    agent1_status: bool
    agent2_status: bool
    agent3_status: bool


"""
initialize the llms and check for api key validity -> if invalid or failed to initialize then abort
get user prompt and git url
clone the repo -> if fails abort with message
list the files inside the repo -> if empty abort with message
llm1 node on file names -> it should at the end write the report and call submit tool to end the loop
llm2 node on llm1_report -> if no report then abort flag the problem which can be max tool calls or anyother reason which is handled inside the tool function -> at the end write the report and call the submit tool
llm3 node on llm2_report and llm1_report -> if no llm2_report then abort with message consisting of the problem which can again be a max tool call or anyother reason handled inside the tool function -> again at the end it will write the report and call the submit tool
"""

"""
the tools that are used by llms:
1. read_file
2. run_shell
3. search_code
4. edit_file
5. sandbox_manager
6. write_file
the tools handled manually:
1. clone_repo
2. list_files
3. report_write
"""
llm1_prompt = """"""
llm2_prompt = """"""
llm3_prompt = """"""


#-------------------------------------graph starts------------------------------------------
#node 1
def build_model(state: PipelineState) -> ChatOpenAI:
    global llm1_model, llm2_model, llm3_model

    try:

        llm1_model = ChatOpenAI(
            model = os.getenv("LLM1"),
            base_url = "https://openrouter.ai/api/v1",
            api_key = os.getenv("OPENROUTER_API_KEY")
        )

        llm2_model = ChatOpenAI(
                model = os.getenv("LLM2"),
                base_url = "https://openrouter.ai/api/v1",
                api_key = os.getenv("OPENROUTER_API_KEY")
            )

        llm3_model = ChatOpenAI(
                model = os.getenv("LLM3"),
                base_url = "https://openrouter.ai/api/v1",
                api_key = os.getenv("OPENROUTER_API_KEY")
            )

        return {"api_status": True}

    except Exception as e:
        return {"api_status": False}


#this is a node it will update the state, add the conditional edge to check if initialization was successful
def initialize_agents(state: PipelineState):

    print("initializing all three agents")
    try:
        global agent1, agent2, agent3

        llm1_tools = {
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "search_code": search_code,
            "submit_context": submit_context
        }

        agent1 = Agent(
            llm1_model,
            llm1_tools,
            llm1_prompt,
            max_iterations=10
        )

        llm2_tools = {
            "edit_file": edit_file,
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "create_branch": create_branch,
            "discard_attempt": discard_attempt,
            "commit_changes": commit_changes,
            "write_file": write_file,
            "submit_context": submit_context
        }

        agent2 = Agent(
            llm2_model,
            llm2_tools,
            llm2_prompt,
            max_iterations=25
        )

        llm3_tools = {
            "edit_file": edit_file,
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "create_branch": create_branch,
            "discard_attempt": discard_attempt,
            "commit_changes": commit_changes,
            "write_file": write_file,
            "submit_context": submit_context
        }

        agent3 = Agent(
            llm3_model,
            llm3_tools,
            llm3_prompt,
            max_iterations=10
        )

        print("agent initialization successful")
        return {}

    except Exception as e:
        print("agent couldn't be initialized")
        return {"llm_failure_message": str(e)}


def user_input(state: PipelineState):

    while True:
        user_prompt = input("enter the prompt for the agents")
        git_url = input("enter the git repository url")

        if user_prompt and git_url:
            return {"user_prompt": user_prompt, "git_url": git_url}

        else:
            print("both the fields are mandatory, try again...")


def clone_repository(state: PipelineState):

    print(f"clonning repository with url: {state['git_url']}...")
    response = clone_repo(state["git_url"], "/target_repo")

    return {"clone_success": response["success"], "target_repo_path": response["relative_path"]}

def repo_files(state: PipelineState):

    files_status = list_files(state["target_repo_path"])
    if not files_status["success"]:
        print(f"couldn't list the files in the target_repo reason: {files_status['error']}")
        return {"target_files": None}
    
    return {"target_files": files_status["files"]}
#i will add the print statement listing all the file names in the repository in the conditional edge function since it is going to check if the repo is empty or not

#one thing, report_write tools should be separate from other tool calls, make the llm return only content and you name the files and call the tool manually
def call_agent1(state:PipelineState):
    print("-----------------agent1 execution starts---------------------")
    try:

        prompt = f"""
            bug report: {state['user_prompt']}
            repo files: {state['target_files']}
        """
        response = agent1.graph.invoke({"messages": prompt})
        last_message = response["messages"][-1]

        if last_message.tool_calls[0]["name"] != "submit_context":
            return {"agent1_status": False, "report_status": False, "llm_failure_message": "agent did not submit"}

        args = last_message.tool_calls[0]["arguments"]
        report_status = report_write(args["data"], "llm1_report", args["format"])
        if report_status["success"]:
            return {"agent1_status": True, "report_status": True}
        else:
            return {"agent1_status": True, "report_status": False, "llm_failure_message": report_status["error"]}

    except Exception as e:
        return {"agent1_status": False, "llm_failure_message": str(e)}

#for the conditional edge, check if report_status is true check if llm1_report is in the report_dir if yes continue else abort
def call_agent2(state: PipelineState):
    print("-----------------agent2 execution starts---------------------")
    try:
        llm1_report = read_file("/report/llm1_report")
        prompt = f"""
            report: {llm1_report}
        """

        response = agent2.graph.invoke({"messages": prompt})
        last_message = response["messages"][-1]

        if last_message.tool_calls[0]["name"] != "submit_context":
            return {"agent2_status": False, "report_status": False, "llm_failure_message": "agent did not submit"}

        args = last_message.tool_calls[0]["arguments"]
        report_status = report_write(args["data"], "llm2_report", args["format"])
        if report_status["success"]:
            return {"agent2_status": True, "report_status": True}
        else:
            return {"agent2_status": True, "report_status": False, "llm_failure_message": report_status["error"]}

    except Exception as e:
        return {"agent2_status": False, "llm_failure_message": str(e)}

def call_agent3(state: PipelineState):
    print("-----------------agent3 execution starts---------------------")
    try:
        llm1_report = read_file("/report/llm1_report")
        llm2_report = read_file("/report/llm2_report")
        prompt = f"""
            llm1 report: {llm1_report}
            llm2 report: {llm2_report}
            baseline output: {state['baseline_output']}
            solved branch path: {state["solution_branch_path"]}
        """

        response = agent3.graph.invoke({"messages": prompt})
        last_message = response["messages"][-1]

        if last_message.tool_calls[0]["name"] != "submit_context":
            return {"agent3_status": False, "report_status": False, "llm_failure_message": "agent did not submit"}

        args = last_message.tool_calls[0]["arguments"]
        report_status = report_write(args["data"], "llm3_report", args["format"])
        if report_status["success"]:
            return {"agent3_status": True, "report_status": True}
        else:
            return {"agent3_status": True, "report_status": False, "llm_failure_message": report_status["error"]}

    except Exception as e:
        return {"agent3_status": False, "llm_failure_message": str(e)}
    
"""class PipelineState(TypedDict):
    job_id: int
    clone_success: bool
    target_repo_path: Optional[str] 
    target_files: list[str]
    report_status: str
    report_files: list[str]
    user_prompt: str
    git_url: str
    baseline_output: Optional[str]
    solution_branch_path: Optional[str]
    llm_failure_message: Optional[str]
    api_status: bool
    agent1_status: bool
    agent2_status: bool
    agent3_status: bool

initialize the llms and check for api key validity -> if invalid or failed to initialize then abort
get user prompt and git url
clone the repo -> if fails abort with message
list the files inside the repo -> if empty abort with message
llm1 node on file names -> it should at the end write the report and call submit tool to end the loop
llm2 node on llm1_report -> if no report then abort flag the problem which can be max tool calls or anyother reason which is handled inside the tool function -> at the end write the report and call the submit tool
llm3 node on llm2_report and llm1_report -> if no llm2_report then abort with message consisting of the problem which can again be a max tool call or anyother reason handled inside the tool function -> again at the end it will write the report and call the submit tool
"""

#conditional edge 1
#this is conditional edge function use this to verify
# def verify_api_connection(state: PipelineState):
#     print("verifying API keys...")
#     if state["api_status"] and llm1_model.models.list() and llm2_model.models.list() and llm3_model.models.list():
#         print("API keys verified")
#         return True

#     else:
#         print("API key failure")
#         return False

def check_agent_initialization(state: PipelineState):
    if state['llm_failure_message']:
        print(state['llm_failure_message'])
        return False
    return True

def clone_repo_check(state: PipelineState):
    if state["clone_success"]:
        print(f"successfully clonned the repository at {state['target_repo_path']}")
        return True
    
    return False

def repo_empty_check(state: PipelineState):
    if state["target_files"]:
        print(f"files in the target_repo are:{state['target_files']}")
        return True
    if state["target_files"] is None:
        return False
    if len(state["target_files"]):
        print(f"there are no files in {state['target_repo_path']}")
        return False

def check_agent1_work(state:PipelineState):
    llm1_report = list_files("report")["files"]
    if "llm1_report.json" not in llm1_report:
        print("agent1 couldn't write the report")
        return False
    
    if state["agent1_status"] and state["report_status"]:
        return True

    else:
        print(state['llm_failure_message'])
        return False

def check_agent2_work(state: PipelineState):
    llm2_report = list_files("report")["files"]
    if "llm2_report.json" not in llm2_report:
        print("agent2 couldn't write the report")
        return False
    
    if state["agent1_status"] and state["report_status"]:
        return True

    else:
        print(state['llm_failure_message'])
        return False

def check_agent3_work(state: PipelineState):
    llm3_report = list_files("report")["files"]
    if "llm3_report.md" not in llm3_report:
        print("agent3 couldn't write the report")
        return END
    
    if state["agent3_status"] and state["report_status"]:
        print("--------------------execution successful----------------------")
        return END

    else:
        print(state['llm_failure_message'])
        return END
#-------------------------------------------graph initialization-----------------------------------------------

graph = StateGraph(PipelineState)

graph.add_node("build_model", build_model)
graph.add_node("initialize_agents", initialize_agents)
graph.add_node("user_input", user_input)
graph.add_node("clone_repository", clone_repository)
graph.add_node("repo_files", repo_files)
graph.add_node("call_agent1", call_agent1)
graph.add_node("call_agent2", call_agent2)
graph.add_node("call_agent3", call_agent3)

graph.add_edge("build_model", "initialize_agents")
# graph.add_conditional_edges(
#     "build_model",
#     verify_api_connection,
#     {True: "initialize_agents", False: END}
# )

graph.add_conditional_edges(
    "initialize_agents",
    check_agent_initialization,
    {True: "user_input", False: END}
)

graph.add_edge(
    "user_input",
    "clone_repository"
)

graph.add_conditional_edges(
    "clone_repository",
    clone_repo_check,
    {True: "repo_files", False: END}
)

graph.add_conditional_edges(
    "repo_files",
    repo_empty_check,
    {True: "call_agent1", False: END}
)

graph.add_conditional_edges(
    "call_agent1",
    check_agent1_work,
    {True: "call_agent2", False: END}
)

graph.add_conditional_edges(
    "call_agent2",
    check_agent2_work,
    {True: "call_agent3", False: END}
)

graph.add_conditional_edges(
    "call_agent3",
    check_agent3_work
)

compiled_graph = graph.compile()