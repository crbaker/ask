"""
Ask conversation module
"""
# ask/conversation.py
# pylint: disable=line-too-long
import readline

import os
import atexit
import typer

from anthropic import Anthropic

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

app = typer.Typer(rich_markup_mode="rich")

_conversation: list[dict] = []

def ask_claude(conversation: list[dict]):
    """
    Ask the Claude API for a response
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    assert api_key, "Please set the CLAUDE_API_KEY environment variable"

    messages = [{"role": response["role"], "content": response["content"]}
                for response in conversation]
    
    client = Anthropic(api_key=api_key)
    response = client.messages.create(max_tokens=1024,
                           model="claude-3-haiku-20240307",
                           messages=messages)

    return response.content[0].text

@app.command()
def start_repl():
    """
    Sets up and start the Ask REPL
    """
    go_again = True
    console = Console()

    history_path = os.path.expanduser("~/.ask_history")

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
        else:
            current_query = f"{current_query} {input(': ')}".strip()

        if current_query == "exit":
            go_again = False
            rprint("Bye!:waving_hand:")
        elif current_query == "cls":
            typer.clear()
            current_query = None
            _conversation.clear()
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
