# Ask App

## Build & Install
1. Create a new virtual environment so that you can have an isolated python environment
```sh
virtualenv venv
source venv/bin/activate
```
2. Install the required dependencies
```sh
pip install -r requirements.txt
```

3. Run lint
```sh
pylint ask
```
4. Use `pyinstaller` to create an executable. A `dist` directory will be created which will include the executable.
```sh
pyinstaller --clean -y -n ask ./ask/__main__.py
./dist/ask/ask
```

## Usage
when in the REPL, simply as a question and the AI will resond. Context is maintained between questions.

### Clear Conversation
To clear the current conversation type `cls`

### Save Conversation
To save the current conversation type `save {tag}` where {tag} is the name you would like to give to the conversation

### View saved conversations
To view a list of saved conversations type `replay`

### Replay a conversations
To view a list of saved conversations type `replay {tag}` where {tag} is the name of a previously saved conversation

### Delete a replay a conversations
To view a list of saved conversations type `replay {tag} del` where {tag} is the name of a previously saved conversation

### Open a file or URL
To read the contents or a file `open "{path_or_url}"` where {path_or_url} is the full path or URL (even a YouTube URL) of the content you want to read into the AI conversation
