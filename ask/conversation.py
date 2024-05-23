"""
Ask conversation module
"""
# ask/conversation.py
# pylint: disable=line-too-long
import readline
import pickle

import os
import atexit
import typer

from anthropic import Anthropic

from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

app = typer.Typer(rich_markup_mode="rich")

def ask_claude(conversation: list[dict]):
    """
    Ask the Claude API for a response
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    assert api_key, "Please set the CLAUDE_API_KEY environment variable"
    
    model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

    messages = [{"role": response["role"], "content": response["content"]}
                for response in conversation]

    client = Anthropic(api_key=api_key)
    response = client.messages.create(max_tokens=1024,
                           model=model,
                           messages=messages)

    return response.content[0].text

def replay_path():
    """
    Get the path to the conversation replay
    """
    return os.path.expanduser("~/.ask_replay")

def save_replay(replay: dict):
    """
    Save the conversation replay
    """
    path = replay_path()
    with open(path, "wb") as file:
        pickle.dump(replay, file)

def save_conversation(tag: str, conversation: list[dict]):
    """
    Save the conversation replay
    """
    replay = fetch_replay()
    replay[tag] = conversation

    save_replay(replay)

def fetch_replay():
    """
    Fetch the conversation replay
    """
    path = replay_path()
    if os.path.exists(path):
        with open(path, "rb") as file:
            return pickle.load(file)
    else:
        return {}

@app.command()
def start_repl():
    """
    Sets up and start the Ask REPL
    """
    go_again = True
    console = Console()

    history_path = os.path.expanduser("~/.ask_history")

    _conversation: list[dict] = []

    def save_history(history_path=history_path):
        readline.write_history_file(history_path)

    if os.path.exists(history_path):
        readline.set_history_length(100)
        readline.read_history_file(history_path)

    atexit.register(save_history)

    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode vi")

    rprint("[italic pink]Ask Repl[/italic pink] :brain:")
    rprint("[italic blue]type `exit` to quit[/italic blue]")

    current_query: str = None

    while go_again:

        if current_query is None or current_query.strip() == "":
            current_query = input('> ').strip()
        elif current_query == "exit":
            go_again = False
            rprint("Bye!:waving_hand:")
        elif current_query == "cls":
            typer.clear()
            current_query = None
            _conversation.clear()
        elif current_query.lower().startswith("replay"):
            replay = fetch_replay()
            components = current_query.split(" ")
            if len(components) == 2:
                tag = components[1]
                if tag in replay:
                    _conversation = replay[tag]
                    for message in _conversation:
                        if message["role"] == "user":
                            rprint(message["content"])
                        else:
                            console.print(Panel(Markdown(message["content"])))
            elif len(components) == 3 and components[2] == "del":
                replay = fetch_replay()
                del replay[components[1]]
                save_replay(replay)
            else:
                text = Text("The following can be replayed:", style="bold")
                console.print(text)

                for tag in replay:
                    rprint(tag)

            current_query = None

        elif current_query.lower().startswith("save"):
            components = current_query.split(" ")
            if len(components) < 2:
                rprint("Please provide a tag for the conversation to save")
            else:
                tag = components[1]
                save_conversation(tag, _conversation)
                rprint("Conversation saved")
            current_query = None
        else:
            try:
                _conversation.append({"role": "user", "content": current_query})
                answer = ask_claude(_conversation)
                _conversation.append({"role": "assistant", "content": answer})
                console.print(Panel(Markdown(answer)))
            except Exception as exception:
                rprint("[italic red]Query Error[/italic red] :exploding_head:")
                rprint(exception)
            finally:
                current_query = None
