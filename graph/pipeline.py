from typing import TypedDict



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

