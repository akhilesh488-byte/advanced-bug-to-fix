import os
from typing import TypedDict, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
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
#define the pipeline state
#define the graph
#define all the functions

#pipeline state design
"""
include all the info that needs to be conveyed to the llms
job_id -> to create the worktree
user_prompt -> to store the user prompt
git_url -> to store the github url
clone_success -> to check if clonning was successful
list_files -> this holds the list of names of the files in the folder
update_report -> if report was updated successfully by each llm, this needs to be updated after each llm call
baseline_output -> holds the output of the target_repo
"""
#the graph design
"""
check if everything is proper for llm to operate before calling it
abort if anything is missing without llm call
node 1 -> ask for user_prompt + git_url and update the state
conditional_edge 1 -> if any field is missing abort
node 2 -> clone the repo and list files, update clone_status + list_files
conditional_edge 2 -> if clonning unsuccessful or list_files state is empty then abort
node 3 -> call llm1 on user prompt + clonned repo file names -> this will execute the correct file based on the file then update the baseline_output in the state, generate a report consisting of solution to the bug then update the report_file as True
conditional_edge 3 -> if report is not present then abort, check if baseline state was updated else abort
node 4 -> call llm2 on the generated report -> creates sandbox and does all the experimentation at the end updates the report then update the report_status in the state if it was unsuccessful then update it as false else keep it true
conditional_edge 4 ->  if report_status = True then continue
node 5 -> call llm3 on the updated report -> merge the fixed branch to the main branch then rerun the file to check the output and compare it against the baseline_output then update the report, update the report_status variable as true or false
"""

class PipelineState(TypedDict):
    job_id: int
    user_prompt: str
    git_url: str
    clone_success: bool
    repo_files: list[str]
    baseline_output: Optional[str]
    vardict: Optional[str]
    report_path: str
    solution_branch_name: Optional[str]
    llm_status: bool
    llm_failure_message: Optional[str]

llm1_prompt = """"""
llm2_prompt = """"""
llm3_prompt = """"""

def build_model(env_key: str) -> ChatOpenAI:
    return ChatOpenAI(
        model = os.getenv(env_key),
        base_url = "https://openrouter.ai/api/v1",
        api_key = os.getenv("OPENROUTER_API_KEY")
    )

llm1_model = build_model("LLM1")
llm2_model = build_model("LLM2")
llm3_model = build_model("LLM3")

def get_prompt():

    while True:
        git_url = input("Enter the github repository url:").strip()
        user_prompt = input("Enter the prompt:").strip()

        if git_url and user_prompt:
            return {
                "git_url": git_url,
                "user_prompt": user_prompt
            }
        else:
            print("prompt and user prompt can't be empty, try again")


def clone_repository(state: PipelineState):
    print("trying to clone github repo ....")
    result = clone_repo(state["git_url"])
    file_names = list_files()

    return {
        "clone_success": result["success"],
        "repo_files": file_names
    }

def llm1_node(state: PipelineState):
    try:
        tools = {
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "search_code": search_code
        }
        response = llm1_agent = Agent(llm1_model, tools, llm1_prompt, max_iterations=10)
        report_file_name = response[0]["args"]["file_name"]
        file_format = response[0]["args"]["format"]
        report_path = f"report/{report_file_name}.{file_format}"
        prompt = (
            f"bug report: {state['user_prompt']}",
            f"baseline output: {state['baseline_output']}",
            f"repo files: {state['repo_files']}"
        )
        llm1_agent.graph.invoke({"messages": [HumanMessage(content = prompt)]})
        return {
            "llm_status": True,
            "llm_failure_message": None,
            "report_path": report_path
        }

    except Exception as e:
        return {
            "llm_status": False,
            "llm_failure_message": str(e),
            "report_path": None
        }

def llm2_node(state: PipelineState):
    try:
        tools = {
            "edit_file": edit_file,
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "create_branch": create_branch,
            "discard_attempt": discard_attempt,
            "commit_changes": commit_changes,
            "write_file": write_file
        }
        llm2_agent = Agent(llm2_model, tools, llm2_prompt, max_iterations=30)
        prompt = read_file(state["report_path"])
        response = llm2_agent.graph.invoke({"messages": [HumanMessage(content = prompt)]})
        report_file_name = response[0]["args"]["file_name"]
        file_format = response[0]["args"]["format"]
        report_path = f"report/{report_file_name}.{file_format}"
        return {
            "llm_status": True,
            "llm_failure_message": None,
            "report_path": report_path
        }
    
    except Exception as e:
        return {
            "llm_status": False,
            "llm_failure_message": str(e),
            "report_path": None
        }

def llm3_node(state: PipelineState):
    try:
        tools = {
            "edit_file": edit_file,
            "read_file": read_file,
            "report_write": report_write,
            "run_shell": run_shell,
            "create_branch": create_branch,
            "discard_attempt": discard_attempt,
            "commit_changes": commit_changes,
            "write_file": write_file
        }
        llm3_agent = Agent(llm3_model, tools, llm3_prompt, max_iterations=10)
        prompt = read_file(state["report_path"])
        response = llm3_agent.graph.invoke({"messages": [HumanMessage(content = prompt)]})
        report_file_name = response[0]["args"]["file_name"]
        file_format = response[0]["args"]["format"]
        report_path = f"report/{report_file_name}.{file_format}"
        return {
            "llm_status": True,
            "llm_failure_message": None,
            "report_path": report_path
        }
    
    except Exception as e:
        return {
            "llm_status": False,
            "llm_failure_message": str(e),
            "report_path": None
    }

def check_clone(state:PipelineState):
    if state["clone_success"] and state["repo_files"]:
        return True
    elif state["clone_success"] is True and state["repo_files"] is False:
        print("repository is empty")
        return False
    else:
        print("provide a proper github url")
        return False

def check_llm(state:PipelineState):
    if state["llm_status"] and state["report_path"]:
        return True
    elif state["llm_status"] is True and state["report_path"] is False:
        print("couldn't update the report")
        return False
    else:
        print(f"error: {state['llm_failure_message']}")
        return False

graph = StateGraph(PipelineState)
graph.add_node("user_prompt", get_prompt)
graph.add_node("clone_repo", clone_repository)
graph.add_node("llm1_node", llm1_node)
graph.add_node("llm2_node", llm2_node)
graph.add_node("llm3_node", llm3_node)

graph.add_edge(
    "user_prompt",
    "clone_repo"
)
graph.add_conditional_edges(
    "clone_repo",
    check_clone,
    {True: "llm1_node", False: END}
)
graph.add_conditional_edges(
    "llm1",
    check_llm,
    {True: "llm2_node", False: END}
)
graph.add_conditional_edges(
    "llm2",
    check_llm,
    {True: "llm3_node", False: END}
)

graph.set_entry_point("user_prompt")
compiled_graph = graph.compile()
