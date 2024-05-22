"""ask entry point script."""
# ask/__main__.py

from ask import conversation, __app_name__

def main():
    """
    Main application function that starts the Ask CLI.
    """
    conversation.app(prog_name=__app_name__)

if __name__ == "__main__":
    main()
