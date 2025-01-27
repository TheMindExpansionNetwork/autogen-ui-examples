import logging
from typing import Dict
from ..datamodel import GenerateWebRequest
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
import sys   

from ..manager import Manager
import traceback

logger = logging.getLogger("autogenui")


app = FastAPI()
# allow cross origin requests for testing on localhost: 800 * ports only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI(root_path="/api")
app.mount("/api", api)


root_file_path = os.path.dirname(os.path.abspath(__file__))
files_static_root = os.path.join(root_file_path, "files/")
static_folder_root = os.path.join(root_file_path, "ui")


os.makedirs(files_static_root, exist_ok=True)
api.mount("/files", StaticFiles(directory=files_static_root, html=True), name="files")


app.mount("/", StaticFiles(directory=static_folder_root, html=True), name="ui")



@api.post("/generate")
async def generate(req: Request) -> Dict:
    """Generate a response from the autogen flow"""
    req = await req.json()
    prompt = req.get("prompt")
    history = req.get("history", "")

    prompt_with_history = f"{history}\n\n{prompt}"
    print("******history******", history)

    try:

        manager = Manager()
        cases = {
            "/system_design": lambda: manager.run_system_design_flow(prompt=prompt),
            "/teachable": lambda: manager.run_teachable_agent_flow(prompt=prompt),
            "/local_llm": lambda: manager.run_local_llm_flow(prompt=prompt),
            # Add more cases here
        }

        for case, action in cases.items():
            if prompt.startswith(case):
                agent_response = action()
                return { "data" : agent_response, "status": True }

        # If no case matches, perform a default action
        agent_response = manager.run_flow(prompt=prompt_with_history)

        response = {
            "data": agent_response,
            "status": True
        }
    except Exception as e:
        traceback.print_exc()
        response = {
            "data": str(e),
            "status": False
        }

    return response


@api.post("/hello")
async def hello() -> None:
    return "hello world"
