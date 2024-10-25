"""
Ask conversation module
"""
# ask/conversation.py
# pylint: disable=line-too-long,broad-exception-caught
import readline

import os
import shlex
import atexit
import typer
import requests

import pyperclip
import html2text

from anthropic import Anthropic

from pytubefix import YouTube
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

from pypdf import PdfReader

from ask.replay import delete_conversation, fetch_conversation, save_conversation, show_conversation, show_saved_conversations

app = typer.Typer(rich_markup_mode="rich")

def ask_claude(conversation: list[dict]):
    """
    Ask the Claude API for a response
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    assert api_key, "Please set the CLAUDE_API_KEY environment variable"

    # Models are shown at https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table
    model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

    messages = [{"role": response["role"], "content": response["content"]}
                for response in conversation]

    client = Anthropic(api_key=api_key)
    response = client.messages.create(max_tokens=1024,
                           model=model,
                           messages=messages)

    return response.content[0].text

def remove_html_tags(text: str):
    """Remove html tags from a string"""
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(text)

def is_youtube(url: str):
    """
    Check if the url is a youtube url
    """
    return url.startswith("https://youtu.be") or url.startswith("https://www.youtube.com")

def map_utf(utf):
    """
    Map the utf to a string
    """
    return utf["utf8"]

def ignore_new_line(word):
    """
    Ignore new line characters
    """
    return word != "\n"

def map_event(event):
    """
    Map the event to a string
    """
    if "segs" in event:
        return "".join(list(filter(ignore_new_line, map(map_utf, event["segs"]))))
    return ""

def extract_captions(yt: YouTube):
    """
    Extract the captions from a youtube video
    """
    captions = yt.captions

    if "en" in captions:
        return captions["en"]

    if "a.en" in captions:
        return captions["a.en"]

    return None

def read_youtube(url: str):
    """
    Read a youtube video and return the text
    """
    yt = YouTube(url)
    captions = extract_captions(yt)
    if captions is not None:
        dict_captions = captions.json_captions
        youtube_text = " ".join(list(map(map_event, dict_captions['events'])))
        return youtube_text

    return None

def read_txt_file(path: str):
    """
    Read a text file and return the text
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception:
        return None

def read_file(path: str):
    """
    Read a file and return the text
    """
    try:
        reader = PdfReader(path, strict=True)
        all_text = list(map(lambda page: page.extract_text(), reader.pages))
        return " ".join(all_text)
    except Exception as e:
        rprint(e)
        return None

def read_url(url: str):
    """
    Read a file and return the text
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        return remove_html_tags(response.text)
    except Exception:
        return None

def handle_open(current_query: str):
    """
    Handle the open command
    """
    components = shlex.split(current_query)
    if len(components) == 2:
        path = components[1]
        if path.startswith("http"):
            if is_youtube(path):
                return read_youtube(path)
            return read_url(path)

        if path.endswith("txt"):
            return read_txt_file(path)

        return read_file(path)

    rprint("Please provide a file path to read")
    return None

def handle_copy(current_query: str, conversation: list[dict]):
    """
    Handle the copy command
    """
    if len(conversation) > 0:
        if current_query.endswith("all"):
            all_content = list(map(lambda x: x["content"], conversation))
            pyperclip.copy("\n".join(all_content))
            rprint("[white on green]Copying all responses[/]")
        else:
            rprint("[white on green]Copying last response[/]")
            pyperclip.copy(conversation[-1]["content"])
    else:
        rprint("[black on red]Nothing to copy[/]")

def handle_delete(current_query: str):
    """
    Handle the delete command
    """
    components = current_query.split(" ")
    if len(components) == 2:
        delete_conversation(components[1])
    else:
        rprint("Please provide a tag to delete")

def handle_replay(current_query: str, conversation: list[dict], console: Console):
    """
    Handle the replay command
    """
    components = current_query.split(" ")
    if len(components) == 2:
        old_conversation = fetch_conversation(components[1])
        if old_conversation:
            conversation.clear()
            conversation.extend(old_conversation)

            show_conversation(conversation, console)
        else:
            rprint("[black on red]No conversation found with that tag[/]")
    else:
        show_saved_conversations(console)

def handle_help():
    rprint("[italic blue]type `exit` to quit[/]")
    rprint('[italic blue]type `open "path"` to open a file or url.[/]')
    rprint("[italic blue]type `replay` to view saved replays.[/]")
    rprint('[italic blue]type `replay "name"` to reload a previously saved conversation.[/]')
    rprint('[italic blue]type `save "name"` to save the current conversation.[/]')
    rprint('[italic blue]type `copy` to copy the last response to the clipboard.[/]')
    rprint('[italic blue]type `copy all` to copy the whole conversation to the clipboard.[/]')

def handle_save(current_query: str, conversation: list[dict]):
    """
    Handle the save command
    """
    components = current_query.split(" ")
    if len(components) < 2:
        rprint("[black on red]Please provide a tag for the conversation to save[/]")
    else:
        save_conversation(components[1], conversation)
    current_query = None

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

    model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

    rprint("[italic pink]Ask Repl[/italic pink] :brain:")
    rprint(f"[italic yellow]using model {model}[/]")
    rprint("[italic blue]type `help` to view available commands[/]")

    current_query: str = None

    while go_again:

        if current_query is None or current_query.strip() == "":
            current_query = input('> ').strip()

        if current_query == "":
            continue
        elif current_query == "exit":
            go_again = False
            rprint("Bye!:waving_hand:")
        elif current_query == "cls":
            console.clear()
            _conversation.clear()
        elif current_query.lower().startswith("copy"):
            handle_copy(current_query, _conversation)
        elif current_query.lower().startswith("help"):
            handle_help()
        elif current_query.lower().startswith("open"):
            file_text = handle_open(current_query)
            if file_text:
                query = f"Please read this text:\n\n{file_text}\n\n"
                _conversation.append({"role": "user", "content": query})
                answer = ask_claude(_conversation)

                _conversation.append({"role": "assistant", "content": answer})
                console.print(Panel(Markdown(answer)))
            else:
                rprint("[black on red]No text found in the file[/]")

        elif current_query.lower().startswith("del"):
            handle_delete(current_query)
        elif current_query.lower().startswith("replay"):
            handle_replay(current_query, _conversation, console)
        elif current_query.lower().startswith("save"):
            handle_save(current_query, _conversation)
        else:
            try:
                _conversation.append({"role": "user", "content": current_query})
                answer = ask_claude(_conversation)
                _conversation.append({"role": "assistant", "content": answer})
                console.print(Panel(Markdown(answer)))
            except Exception as exception:
                rprint("[italic red]Query Error[/italic red] :exploding_head:")
                rprint(exception)

        current_query = None
