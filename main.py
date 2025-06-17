from ui import SamAssistantUI
from tasks import SamAssistantBackend

if __name__ == "__main__":
    backend = SamAssistantBackend(None)  # Create the backend first
    ui = SamAssistantUI(backend)  # Then create the UI with the backend
    backend.ui = ui  # Link the backend to the UI
    backend.wish_me()  # Call wish_me to greet the user
    ui.run()  # Start the UI
