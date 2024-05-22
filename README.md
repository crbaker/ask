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

3. Run lint and tests
```sh
pylint ask
```
≈
4. Use `pyinstaller` to create an executable. A `dist` directory will be created which will include the executable.
```sh
pyinstaller --clean -y -n ask ./ask/__main__.py
./dist/ask/ask
```
