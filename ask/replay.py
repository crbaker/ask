"""
Manager for the conversation replay
"""
import os
import pickle

from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

def show_saved_conversations(console: Console):
    """
    Display the conversation replay
    """
    replay = fetch_replay()

    text = Text("The following can be replayed:", style="bold")
    console.print(text)

    for tag in replay:
        rprint(tag)

def fetch_conversation(tag: str):
    """
    Fetch a conversation from the replay
    """
    replay = fetch_replay()
    return replay.get(tag, None)

def show_conversation(conversation: list[dict], console: Console):
    """
    Display a conversation from the replay
    """
    for message in conversation:
        if message["role"] == "user":
            rprint(message["content"])
        else:
            console.print(Panel(Markdown(message["content"])))

def delete_conversation(tag: str):
    """
    Delete a conversation from the replay
    """
    replay = fetch_replay()
    if tag in replay:
        del replay[tag]
        _save_replay(replay)
        rprint(f"Conversation with tag '{tag}' deleted")
    else:
        rprint("No conversation found with that tag")

def _replay_path():
    """
    Get the path to the conversation replay
    """
    return os.path.expanduser("~/.ask_replay")

def _save_replay(replay: dict):
    """
    Save the conversation replay
    """
    path = _replay_path()
    with open(path, "wb") as file:
        pickle.dump(replay, file)

def save_conversation(tag: str, conversation: list[dict]):
    """
    Save the conversation replay
    """
    replay = fetch_replay()
    replay[tag] = conversation

    _save_replay(replay)

    rprint(f"Conversation saved as '{tag}'")

def fetch_replay():
    """
    Fetch the conversation replay
    """
    path = _replay_path()
    if os.path.exists(path):
        with open(path, "rb") as file:
            return pickle.load(file)
    else:
        return {}
