import threading
import queue
import time
import pyttsx3
import speech_recognition as sr
import wikipedia
from datetime import datetime
import webbrowser
from geopy.geocoders import Nominatim
import pyttsx3
import speech_recognition as sr
import wikipedia
import os
import time
import threading
import requests
import pyperclip
import numpy  
import random
from datetime import datetime
import shutil
import pyttsx3
from threading import Thread
import pyautogui 
import subprocess
import requests
import webbrowser


class SamAssistantBackend:
    def __init__(self, ui):
        self.ui = ui
        self.command_queue = queue.Queue()
        self.assistant_active = False
        self.is_typing_mode_active = False
        self.is_sleeping = False
        self.is_speaking = False
        self.is_listening = True
        self.last_command = None  # Initialize this variable in __init__()
        self.listening_thread = None
        self.speech_lock = threading.Lock()
        self.speech_event = threading.Event()  # Event to manage speech state
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)
        self.engine.setProperty("rate", 180)

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 3000
        self.recognizer.pause_threshold = 0.5

        # Start the command handler thread
        self.command_handler_thread = threading.Thread(target=self.handle_commands, daemon=True)
        self.command_handler_thread.start()

    pictures_folder = os.path.join(os.path.expanduser("~"), "Videos\\Captures")
    videos_folder = os.path.join(os.path.expanduser("~"), "Videos\\Captures")

    def wish_me(self):
        """Wish the user based on the time of day."""
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Good Morning, Sir"
        elif 12 <= current_hour < 18:
            greeting = "Good Afternoon, Sir"
        elif 18 <= current_hour < 22:
            greeting = "Good Evening, Sir"
        else:
            greeting = "Good Night, Sir"
        
        self.speak(f"{greeting}, My name is Sam, How may I assist you?")
        self.toggle_listening()
        self.ui.add_to_output(f"{greeting}, My name is Sam, How may I assist you?", "assistant")

    def toggle_listening(self):
        """Start or stop the listening mode."""
        if not self.assistant_active:
            self.assistant_active = True
            self.ui.mic_button.configure(bg="#2563eb")
            self.ui.listening_frame.grid()
            self.ui.add_to_output("SAM is listening... Speak your query.", "assistant")
            self.start_listening_thread()  # Start the listening thread
        else:
            self.assistant_active = False
            self.ui.mic_button.configure(bg="#1f2937")
            self.ui.listening_frame.grid_remove()
            self.ui.add_to_output("SAM is now inactive. Click the microphone to activate.", "assistant")

        # Ensure SAM starts listening immediately when activated
        if self.assistant_active and not self.listening_thread:
            self.start_listening_thread()

    def start_listening_thread(self):
        """Start a new thread for listening to commands."""
        if self.listening_thread and self.listening_thread.is_alive():
            return  # Avoid starting multiple threads
        self.listening_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        self.listening_thread.start()

    def toggle_input_bar(self):
        """Toggle visibility of the input bar."""
        self.is_typing_mode_active = not self.is_typing_mode_active
        if self.is_typing_mode_active:
            self.ui.input_frame.grid()  # Show the input frame
        else:
            self.ui.input_frame.grid_remove()  # Hide the input frame

    def process_input(self, event=None):
        """Process user input from the text entry."""
        user_input = self.ui.input_var.get()
        if user_input:
            self.ui.add_to_output(f"You: {user_input}", "user")
            self.ui.input_var.set("")  # Clear the input field
            self.command_queue.put(user_input)

    def speak(self, text):
        """Convert text to speech in a thread-safe manner."""
        with self.speech_lock:
            self.is_speaking = True
            self.is_listening = False
            self.speech_event.clear()
            try:
                self.engine.setProperty("rate", 150)
                self.engine.setProperty("volume", 1)
                
                # Split the text into sentences and speak each one with a pause
                sentences = text.split('. ')
                for sentence in sentences:
                    self.engine.say(sentence)
                    self.engine.runAndWait()
                    time.sleep(0.5)  # Pause for half a second between sentences
            except RuntimeError as e:
                print(f"Runtime error in speaking: {e}")
                self.engine = pyttsx3.init()
                self.engine.say(text)
                self.engine.runAndWait()
            finally:
                self.is_speaking = False
                self.speech_event.set()
                self.is_listening = True
        
    def listen_for_commands(self):
        """Listen for user commands through the microphone."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise
            while self.is_listening:  # Keep running indefinitely
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    command = self.recognizer.recognize_google(audio, language="en-in").lower()
                    self.ui.add_to_output(f": {command}", "assistant")  # Feedback for the user

                    if self.is_sleeping:
                        if "wake up" in command:
                            self.ui.add_to_output("SAM is waking up!", "assistant")
                            self.speak("I'm awake now! How can I assist you?")
                            self.assistant_active = True
                            self.start_listening_thread()  # Restart the listening thread
                    else:
                        self.command_queue.put(command)  # Process the command normally

                except sr.UnknownValueError:
                    continue  # Ignore timeout
                except sr.WaitTimeoutError:
                    continue  # Ignore timeout
                except Exception as e:
                    continue

    def open_folder(self, path):
        """Opens a folder using the file explorer."""
        if os.path.exists(path):
            try:
                subprocess.run(['explorer', path], shell=True)  # Open folder in file explorer
                print(f"Opened folder: {path}")
            except Exception as e:
                print(f"Error opening folder {path}: {e}")
        else:
            print(f"Folder not found: {path}")

    def process_command(self, command):
        """Parses the voice command to determine what to open (file or folder)."""
        if not command:
            return

        # Paths based on the custom locations you provided
        special_paths = {
            "desktop": r"C:\Users\mjayr\Desktop",
            "downloads": r"C:\Users\mjayr\Downloads",  # Custom path for Downloads
            "documents": r"C:\Users\mjayr\Documents",
            "pictures": r"C:\Users\mjayr\Pictures",
            "videos": r"C:\Users\mjayr\Videos",
            "music": r"C:\Users\mjayr\Music",
            "saved games": r"C:\Users\mjayr\Saved Games",
            "captured": r"C:",
            "captured": r"d:",
        }

        # Match special folders
        for key, path in special_paths.items():
            if key in command.lower():
                self.open_folder(path)
                return

        # If the command includes "open", search for files to open
        if "open" in command.lower():
            file_name = command.lower().replace("open", "").strip()
            self.search_and_open_file(file_name)

    def search_and_open_file(self, file_name):
        """Searches for a file in common directories and opens it."""
        base_dirs = [
            r"C:\Users\mjayr\Desktop",
            r"C:\Users\mjayr\Downloads",  # Custom path for Downloads
            r"C:\Users\mjayr\Documents",
            r"C:\Users\mjayr\Pictures",
            r"C:\Users\mjayr\Videos",
            r"C:\Users\mjayr\Music",
            r"C:\Users\mjayr\Saved Games",
            r"C:",
            r"d:",
            r"j:",
        ]

        # Define file extensions to search for
        file_extensions = [
            '.pdf', '.txt', '.docx', '.xlsx',  # Document files
            '.mp4', '.avi', '.mkv', '.mov',    # Video files
            '.mp3', '.wav', '.flac',           # Music files
            '.jpg', '.png', '.jpeg', '.gif',   # Image files
            '.zip', '.rar', '.7z'              # Compressed files
        ]

        # Search for files across the directories
        for base_dir in base_dirs:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file_name.lower() in file.lower():  # If the filename matches
                        file_path = os.path.join(root, file)
                        if any(file.lower().endswith(ext) for ext in file_extensions):  # Check for valid file types
                            self.speak(f"Opening")
                            self.ui.add_to_output("Opening", "assistant")
                            self.open_file(file_path)  # Open the file
                            return
                        
        self.ui.add_to_output(f"File not found: {file_name}")
        self.speak(f"File not found: {file_name}")

    def open_file(self, file_path):
        """Opens a file using the default application."""
        try:
            # Use subprocess to open the file with the default application
            subprocess.run(['start', '', file_path], shell=True)
        except Exception as e:
            print(f"Error opening file {file_path}: {e}")

    def takeScreenshot(self):
        try:
            # Ensure the folder exists before saving the screenshot
            if not os.path.exists(self.pictures_folder):
                os.makedirs(self.pictures_folder)

            screenshot_path = os.path.join(self.pictures_folder, f"Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            self.speak(f"Screenshot has been taken and saved.")
            self.ui.add_to_output(f"Screenshot has been taken and saved as {screenshot_path}.", "assistant")
        except Exception as e:
            print(f"Error: {e}", "assistant") # Log the actual error
            self.speak("An error occurred while taking the screenshot.")

    def startScreenRecording(self):
        try:
            pyautogui.hotkey('winleft', 'alt', 'r')
            pyautogui.hotkey('winleft', 'alt', 'r')  # Simulate Win + Alt + R to start screen recording
            time.sleep(2)  # Adding a small delay to ensure the hotkey is processed
            self.speak("Screen recording has started.")
        except Exception as e:
            self.speak("An error occurred while starting screen recording.")

    def stopScreenRecording(self):
            # Simulate pressing Windows Key + Alt + R to stop recording
            pyautogui.keyDown('winleft')  # Hold down Windows key (left)
            pyautogui.keyDown('alt')      # Hold down Alt key
            pyautogui.press('r')          # Press 'R' while holding down Windows + Alt
            pyautogui.keyUp('alt')        # Release Alt key
            pyautogui.keyUp('winleft')    # Release Windows key
            self.speak("Screen recording has been stopped and saved in captures folder.")
            self.ui.add_to_output(f"Recording saved in: {self.videos_folder}", "assistant")

    def listen(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration= 1)  # Adjust for ambient noise
            self.is_listen = True
            while self.is_listen: # Keep running indefinitely
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    query = self.recognizer.recognize_google(audio, language="en-in").lower()
                    self.ui.add_to_output(query, "assistant")
                    if "stop listening" in query :
                        self.start_listening_thread()
                        self.speak("Stopping listening.")
                        self.start_listening_thread()
                        break
                    return query
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError:
                    return ""
                except sr.WaitTimeoutError:
                    return "" 
                
    def start_typing(self):
        self.is_listening = False
        time.sleep(1)
        self.ui.add_to_output("Starting to write. Say 'stop typing' to stop.", "assistant")
        self.speak("Say 'stop writing' to stop.")
        
        while True:
            query = self.listen()
            if "stop writing" in query or "stop typing" in query:
                self.speak("Stopping writing.")
                self.start_listening_thread()
                break

            elif "next line" in query or "nextline" in query:
                pyautogui.press("enter")
            elif "back line" in query or "backline" in query or "delete line" in query:
                pyautogui.hotkey("shift", "home")
                pyautogui.press("backspace")
            elif "delete line" in query:
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")
            elif "select all" in query:
                pyautogui.hotkey("ctrl", "a")
            elif "copy" in query:
                pyautogui.hotkey("ctrl", "c")
            elif "paste" in query:
                pyautogui.hotkey("ctrl", "v")
            elif "cut" in query:
                pyautogui.hotkey("ctrl", "x")
            elif "undo" in query:
                pyautogui.hotkey("ctrl", "z")
            elif "space" in query:
                pyautogui.hotkey("space")
            elif "nextline" in query or "next line" in query:
                pyautogui.press("enter")
            elif "save" in query:
                self.save_notepad()
            elif query:
                pyautogui.write(query, interval=0.1)
                pyautogui.press("space")

    def choose_save_location(self):
        
        while True:
            self.ui.add_to_output("Where do you want to save the file? Say Desktop, Downloads, or Documents.", "assistant")
 # Normalize the input to lowercase and strip whitespace
            self.speak("Where?")
        
            location = self.listen()
            # Check for valid locations
            if "desktop" in location or "desktop" in location:
                return os.path.join(os.path.expanduser("~"), "Desktop")
            elif "downloads" in location or "download" in location:
                return os.path.join(os.path.expanduser("~"), "Downloads")
            elif "documents" in location or "documents" in location:
                return os.path.join(os.path.expanduser("~"), "Documents")
            else:
                continue

    def save_notepad(self):
        folder_path = self.choose_save_location()
        self.ui.add_to_output("Do you want to create a new folder?", "assistant")
        self.speak("Do you want to create a new folder?")
        response = self.listen()  # Listen for the response and strip whitespace
        
        # Check if the response is empty
        if not response:
            self.ui.add_to_output("No response detected. Skipping folder creation.", "assistant")
            self.speak("No response detected. Skipping folder creation.")
            folder_created = False  # No folder created
        else:
            # Check for folder creation commands
            if ("create new folder" in response or 
                "yes i want to" in response or 
                "create a new folder" in response or  
                "yes" in response or 
                "folder" in response): 
                self.ui.add_to_output("Please say the folder name", "assistant")
                self.speak("Please say the folder name.")
                
                folder_name = self.listen()  # Listen for the folder name and strip whitespace
                
                # Check if the folder name is empty
                if folder_name:
                    folder_path = os.path.join(folder_path, folder_name)
                    os.makedirs(folder_path, exist_ok=True)
                    self.ui.add_to_output(f"Folder created successfully at {folder_path}.", "assistant")
                    #self.speak(f"Folder created successfully.")
                    folder_created = True  # Folder was created
                else:
                    self.ui.add_to_output("No folder name provided. Skipping folder creation.", "assistant")
                    self.speak("No folder name provided. Skipping folder creation.")
                    folder_created = False  # No folder created
            else:
                self.ui.add_to_output("No new folder created. Proceeding to save the file.", "assistant")
                self.speak("No new folder created. Proceeding to save the file.")
                folder_created = False  # No folder created

        self.speak("Please say the file name.") # Listen for the file name and strip whitespace
        # Now that we have a valid folder path (or no folder), ask for the file name
        filename = self.listen()
        

        # Use default name if no filename is provided
        if not filename:
            filename = "abc demo"  # Default filename
            self.ui.add_to_output("No file name provided. Using default name 'abc demo'.", "assistant")
            self.speak("No file name provided. Using default name 'abc demo'.")

        # Determine the full file path based on whether a folder was created
        if folder_created:
            filepath = os.path.join(folder_path, filename + ".txt")  # Save in the created folder
        else:
            filepath = os.path.join(folder_path, filename + ".txt")  # Save in the chosen location

        self.ui.add_to_output(f"Saving file as {filepath}.", "assistant")
        self.speak(f"Saving file successfully!")
        
        # Simulate saving the file using pyautogui
        pyautogui.hotkey("ctrl","shift", "s")  # Trigger save dialog
        time.sleep(1)  # Wait for the save dialog to open
        pyautogui.write(filepath)  # Type the file path
        pyautogui.press("enter")  # Confirm save
        time.sleep(1)  # Wait for the save action to complete
        self.start_listening_thread()
        self.is_listen = False
        self.start_listening_thread()
            
    def handle_commands(self):
        debounce_time = 0.2  # Debounce time for processing commands
        max_silence_time = 5  # Maximum silence time (in seconds) before resetting

        last_command_time = time.time()  # Track the last time a command was received

        while True:
            try:
                # Check if the user has been silent for too long
                if time.time() - last_command_time > max_silence_time:
                    print("No commands received for a while. Resetting listener...")
                    self.reset_assistant()
                    last_command_time = time.time()  # Reset the timer

                # Try to get a command from the queue
                command = self.command_queue.get(timeout=debounce_time)
                command = command.strip().lower()  # Normalize the command

                # Update the last command time
                last_command_time = time.time()

                # Skip command if the assistant is already processing another command or sleeping
                if self.is_speaking or self.is_sleeping:
                    continue

                # Process the command in a separate thread to avoid blocking
                threading.Thread(target=self.process_command, args=(command,)).start()

                if "sleep" in command:
                    self.ui.add_to_output("SAM is going to sleep...Say 'wake up' to activate me again.", "assistant")
                    time.sleep(3)
                    self.speak("I'm going to sleep.")
                    time.sleep(2)
                    self.ui.hide_ui() 
                    self.assistant_active = True # Hide the UI
                    #self.assistant_active = False  # Set assistant to inactive
                    #self.is_listening = False  # Stop listening
                    #self.ui.mic_button.configure(bg="#1f2937")  # Reset microphone button to inactive
                    self.ui.listening_frame.grid_remove()  # Hide listening indicator
                        
                elif "wikipedia" in command:
                    try:
                        query = command.replace("wikipedia", "").strip()
                        result = wikipedia.summary(query, sentences=2)
                        self.ui.add_to_output(f"SAM: According to Wikipedia, {result}", "assistant")
                        self.speak(f"According to Wikipedia, {result}")
                    except Exception as e:
                        self.ui.add_to_output("SAM: Sorry, I couldn't find that information on Wikipedia.", "assistant")
                        self.speak("Sorry, I couldn't find that information on Wikipedia.")
                        self.reset_assistant()

                elif "search google" in command:
                    query = command.replace("search google", "").strip()
                    self.ui.add_to_output(f"SAM: Searching Google for {query}.", "assistant")
                    self.speak(f"Searching Google for {query}.")
                    webbrowser.open(f"https://www.google.com/search?q={query}")

                elif "search private" in command:
                    self.speak("Searching private.")
                    command = command.replace("search private google", "").strip()
                    command = command.replace("search private", "").strip()
                    command = command.replace("search", "").strip()
                    command = command.replace("private", "").strip()
                    command = command.replace("about", "").strip()
                    # Path to the Chrome executable (adjust if needed)
                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    # Open Chrome in Incognito mode and perform the search
                    subprocess.run([chrome_path, '-incognito', f'https://www.google.com/search?q={command}'])

                # Search on YouTube
                elif "search on youtube" in command:
                    self.speak("Searching YouTube.")
                    command = command.replace("search youtube", "").strip()
                    command = command.replace("about", "").strip()  # Removing "about" if present
                    webbrowser.open(f"https://www.youtube.com/results?search_query={command}")

                elif "search " in command or "search on chat GPT" in command:
                        self.is_listening = False
                        if self.last_command == "search on chat GPT":
                            return  # Prevent repeated execution
                        self.speak("What is your query?")
                    
                        query = self.listen()
                        self.is_listen = False
                        self.ui.add_to_output(f"SAM: Searching ChatGPT for {query}.", "assistant")
                        self.is_listen = False
                        
                        self.speak(f"Searching")

                        # Open ChatGPT in Chrome
                        search_url = "https://chat.openai.com/"
                        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Adjust the path if needed
                        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
                        webbrowser.get('chrome').open(search_url)
                        time.sleep(5)  # Allow the page to load

                        # Click on the text input box (change coordinates based on your screen resolution)
                        pyautogui.press("/")
                        #pyautogui.click(500, 900)  # Adjust this based on your screen resolution
                        time.sleep(1)
                        # Type the command and send it
                        pyautogui.write(query, interval=0.05)
                        time.sleep(1)
                        pyautogui.press("enter")
                        self.is_listening = True
                        self.start_listening_thread()
                        self.is_listen = False
                        #self.start_listening_thread()
                        

                elif "start typing" in command or "start Writing"in command or "start typ"in command or "on notepad"in command :
                    self.start_typing()
                elif "save file" in command:
                    self.save_notepad()

                elif "weather" in command:
                    # Check if the command is requesting weather info
                    if "in" in command:
                        location_name = command.split("in", 1)[1].strip()  # Extract location after "in"
                        
                        # Fallback locations to ensure some level of recognition
                        known_locations = {
                            'pune': 'Pune, Maharashtra',
                            'mumbai': 'Mumbai, Maharashtra',
                            'nagpur': 'Nagpur, Maharashtra',
                            'shirur': 'Pune, Maharashtra' ,
                            # Add more fallback locations as needed
                        }

                        # Match known locations if available
                        location_name = known_locations.get(location_name.lower(), location_name)

                        # Geolocator to convert location name to latitude and longitude
                        geolocator = Nominatim(user_agent="weather_bot")
                        location = geolocator.geocode(location_name)

                        if location:
                            coordinates = (location.latitude, location.longitude)
                            # Open-Meteo endpoint for current weather data
                            url = f"https://api.open-meteo.com/v1/forecast?latitude={coordinates[0]}&longitude={coordinates[1]}&current_weather=true"
                            
                            try:
                                # Make a GET request to the API
                                response = requests.get(url)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    
                                    temperature = data['current_weather']['temperature']
                                    weather_condition = data['current_weather']['weathercode']
                                    
                                    # Convert weather code to a more readable condition
                                    conditions = {
                                        0: 'Clear',
                                        1: 'Partly Cloudy',
                                        2: 'Cloudy',
                                        3: 'Rain',
                                        4: 'Thunderstorms',
                                        5: 'Snow',
                                    }
                                    
                                    weather = conditions.get(weather_condition, 'Unknown')
                                    
                                    # Output the results
                                    weather_info = f"The current temperature in {location_name} is {temperature}°C with {weather} conditions."
                                    self.ui.add_to_output(weather_info, "assistant")
                                    self.speak(weather_info)
                                else:
                                    self.ui.add_to_output("Failed to retrieve weather data.", "assistant")
                                    self.speak("Failed to retrieve weather data.", "assistant")
                            except Exception as e:
                                error_message = f"An error occurred: {str(e)}"
                                self.ui.add_to_output(error_message)
                                self.speak(error_message)
                        else:
                            self.ui.add_to_output(f"Sorry, I couldn't find the location '{location_name}.", "assistant")
                            self.speak(f"Sorry, I couldn't find the location '{location_name}.")
                    else:
                        # Handle case where "weather" is mentioned but no location is provided
                        self.ui.add_to_output("Please specify a location after 'weather in'.", "assistant")
                        self.speak("Please specify a location after 'weather in'.")

                elif "open google" in command or "open chrome" in command or "open browser" in command:
                    self.ui.add_to_output("Opening Google", "assistant")
                    self.speak("Opening Google.")
                    webbrowser.open("https://www.google.com")

                elif "play song" in command or "play music" in command:
                    self.speak("Playing a song for you.")
                    youtube_songs = [
                    "https://youtu.be/UBBHpoW3AKA?si=PBia51ViMQh1i8Jc",  
                    "https://youtu.be/lbCRtrrMvSw?si=PPgDFdK7pRWYw4oU",  
                    "https://youtu.be/psWV9GdEgzo?si=e4iBhysuEXYjHxJT", 
                    "https://youtu.be/FIaUYKLg5S4?si=_CV3nwKFbR_1Z-aq",  
                    "https://youtu.be/KhnVcAC5bIM?si=9MnDz9XbMzLZf0fH",  
                    "https://youtu.be/puKD3nkB1h4?si=sAAubx_lgVzEvvbE",  
                    "https://youtu.be/M7ub-Fg92Zk?si=akUYR-rzl3p9lihR", 
                    "https://youtu.be/Tb3x5I0ulCg?si=mjTAKJRLFOwjpMLP",  
                    "https://youtu.be/Ax0G_P2dSBw?si=fdLgqNJMBDHTDGfk",  
                    "https://youtu.be/kd-6aw99DpA?si=eIgTzasAIser4HtN",
                    "https://youtu.be/hc7IJO7fD78?si=t_o1vA3h37bMomeZ",
                    "https://youtu.be/abiL84EAWSY?si=igJiHLfFCb9sheLo",
                    "https://youtu.be/kd-6aw99DpA?si=AcWGRvvS_MD1TTRo",
                    "https://youtu.be/h6aGikIL-I4?si=_yl5vSMvYhbDDO4a",
                    "https://youtu.be/sRlA7JWTj04?si=Q0wcG1WEAkXUhpaD",
                    ]
                    random_song = random.choice(youtube_songs)
                    webbrowser.open(random_song)
                    self.speak("Hope you enjoy this song!")

                elif "click on enter" in command or "enter" in command:
                    time.sleep(1)
                    pyautogui.press("enter")
                    time.sleep(1)

                elif "open new tab" in command:
                    pyautogui.hotkey('ctrl', 't')
                    self.speak("Opened new tab.")
                    self.ui.add_to_output("Opened new tab.", "assistant")

                elif "reload" in command:
                    pyautogui.hotkey('ctrl', 'r')
                    self.speak("reloaded")
                    self.ui.add_to_output("reloaded.", "assistant")
                    
                elif "close tab" in command or "close current tab" in command:
                    pyautogui.hotkey('ctrl', 'w')
                    self.speak("Closed current tab.")
                    self.ui.add_to_output("Closed current tab.", "assistant")
                    
                elif "open downloads" in command:
                    pyautogui.hotkey('ctrl', 'j')
                    self.speak("Opened Downloads.")
                    self.ui.add_to_output("Opened Downloads.", "assistant")
                    
                elif "open bookmarks" in command:
                    pyautogui.hotkey('ctrl', 'shift', 'b')
                    self.speak("Opened bookmarks.")
                    self.ui.add_to_output("Opened bookmarks.", "assistant")
                    
                elif "open incognito" in command:
                    pyautogui.hotkey('ctrl', 'shift', 'n')
                    self.speak("Opened incognito window.")
                    self.ui.add_to_output("Opened incognito window.", "assistant")
                    
                elif "reopen closed tab" in command:
                    pyautogui.hotkey('ctrl', 'shift', 't')
                    self.speak("Reopened last closed tab.")
                    self.ui.add_to_output("Reopened last closed tab.", "assistant")
                    
                elif "zoom in" in command:
                    pyautogui.hotkey('ctrl', '+')
                    self.speak("Zoomed in.")
                    self.ui.add_to_output("Zoomed in.", "assistant")
                    
                elif "zoom out" in command:
                    pyautogui.hotkey('ctrl', '-')
                    self.speak("Zoomed out.")
                    self.ui.add_to_output("Zoomed out.", "assistant")
                    
                elif "reset zoom" in command:
                    pyautogui.hotkey('ctrl', '0')
                    self.speak("Reset zoom to default.")
                    self.ui.add_to_output("Reset zoom to default.", "assistant")
                # YouTube shortcuts
                elif "mute" in command or "unmute" in command:
                    pyautogui.hotkey('m')
                    self.speak("ok ")
                    
                elif "click" in command or "play" in command:
                    pyautogui.hotkey('space')
                    self.speak("played.")

                elif "pause" in command:
                    pyautogui.hotkey('space')
                    self.speak("paused.")

                # Open Google in Incognito (Private) mode
                elif "open private mode" in command:
                    self.speak("Opening Google in private mode.")
                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    subprocess.run([chrome_path, '-incognito', 'https://www.google.com'])

                elif "volume up" in command or "Increases volume" in command:
                    pyautogui.hotkey('up')
                    self.speak("Volume Increasesed")
                    self.ui.add_to_output("Volume Increasesed.", "assistant")
                    
                elif "volume down" in command or "Decreases volume" in command:
                    pyautogui.hotkey('down')
                    self.speak("Volume down.")
                    self.ui.add_to_output("Volume down.", "assistant")
                    
                elif "forward" in command:
                    pyautogui.hotkey('right')  # Skip forward 5 seconds
                    self.speak("Forwarded")
                    self.ui.add_to_output("Forwarded", "assistant")
                    
                elif "backward" in command or "rewind" in command:
                    pyautogui.hotkey('left')  # Rewind 5 seconds
                    self.speak("Rewinded")
                    self.ui.add_to_output("Rewinded.", "assistant")

                elif "next video" in command:
                    pyautogui.hotkey('shift', 'n')  # Rewind 5 seconds
                    self.speak("Playing Next Video")
                    self.ui.add_to_output("Playing Next Video", "assistant")
                    
                elif "full screen" in command:
                    pyautogui.hotkey('f')
                    self.speak("")
                    self.ui.add_to_output("full screen.", "assistant")
                    
                elif "exit full screen" in command:
                    pyautogui.hotkey('esc')
                    self.speak("")
                    self.ui.add_to_output("Exited full screen.", "assistant")

                elif "minimize" in command or "minimise" in command:
                    try:
                        pyautogui.hotkey('winleft', 'down')  
                        self.speak("Window minimized.")
                    except Exception as e:
                        self.speak("An error occurred while minimizing the window.")

                elif "maximize" in command:
                    try:
                        pyautogui.hotkey('winleft', 'up')  
                        self.speak("Window maximized.")
                    except Exception as e:
                        self.speak("An error occurred while maximizing the window.")
                
                elif "hide it" in command:
                    try:
                        pyautogui.hotkey('winleft', 'up', 'up')  
                        self.speak("Window maximized.")
                    except Exception as e:
                        self.speak("An error occurred while maximizing the window.")

                elif "turn on wi-fi" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('space')  # Toggle Wi-Fi
                        pyautogui.hotkey('win', 'a') 
                        self.speak("Wi-Fi is now turned on.")
                        self.ui.add_to_output("Wi-Fi turned on.", "assistant")  # Print Output

                elif "turn off wi-fi" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('space')  # Toggle Wi-Fi
                        pyautogui.hotkey('win', 'a') 
                        self.speak("Wi-Fi is now turned off.")
                        self.ui.add_to_output("Wi-Fi turned off.", "assistant")  # Print Output

                # 🔹 Turn On/Off Airplane Mode  
                elif "turn on airplane mode" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('right')
                        pyautogui.press('right') # Navigate to Airplane Mode
                        pyautogui.press('space')  # Toggle Airplane Mode OFF
                        pyautogui.hotkey('win', 'a')
                        self.speak("Airplane mode is now turned on.")
                        self.ui.add_to_output("Airplane mode turned on.", "assistant")  # Print Output

                elif "turn off airplane mode" in command.lower():
                        time.sleep(1)
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('right') 
                        pyautogui.press('right') # Navigate to Airplane Mode
                        pyautogui.press('space')  # Toggle Airplane Mode OFF
                        pyautogui.hotkey('win', 'a')
                        self.speak("Airplane mode is now turned off.")
                        self.ui.add_to_output("Airplane mode turned off.", "assistant")  # Print Output

                # 🔹 Turn On/Off Bluetooth  
                elif "turn on bluetooth" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('right')  # Navigate to Bluetooth
                        pyautogui.press('space')  # Toggle Bluetooth OFF
                        self.speak("Bluetooth is now turned on.")
                        pyautogui.hotkey('win', 'a')
                        self.ui.add_to_output("Bluetooth turned on.", "assistant")  # Print Output

                elif "turn off bluetooth" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'a')  # Open Action Center
                        time.sleep(1)
                        pyautogui.press('right')  # Navigate to Bluetooth
                        pyautogui.press('space')  # Toggle Bluetooth OFF
                        self.speak("Bluetooth is now turned off.")
                        pyautogui.hotkey('win', 'a')
                        self.ui.add_to_output("Bluetooth turned off.", "assistant")  # Print Output

                # 🔹 Open Settings  
                elif "open settings" in command.lower():
                        time.sleep(1)
                        pyautogui.hotkey('win', 'i')  # Open Windows Settings
                        self.speak("Opening settings.")
                        self.ui.add_to_output("Settings opened.", "assistant")  # Print Output
                        
                elif "open" in command and ("txt document" in command or "pdf" in command or "photo" in command or "movie" in command or "video" in command or "Document" in command or ".pdf" in command or "image" in command or "file" in command or "folder" in command):
                    file_path = command.replace("pdf", "").replace("photo", "").replace("movie", "").replace("Document", "").replace(".pdf", "").replace("image", "").replace("file", "").replace("song", "").strip()
                    command = command.replace("pdf", "").replace("photo", "").replace("movie", "").replace("Document", "").replace(".pdf", "").replace("image", "").replace("file", "").replace("song", "").strip()
                    self.process_command(command)
                    pyautogui.sleep(1)

                elif "open " in command and "application" in command or "app" in command or "software" in command.lower() :
                    command = command.replace("open", "").strip()
                    if "application" in command or "app" in command or "software" in command:
                    # Only extract the actual application name
                        command = command.replace("application", "").replace("app", "").replace("software", "").strip()
                    self.speak("opening")
                    pyautogui.press("super")
                    pyautogui.sleep(1)
                    pyautogui.typewrite(command)
                    pyautogui.sleep(2)
                    pyautogui.press("enter")
                    
                
                elif "close google" in command:
                    self.speak("Closing Google.")
                    os.system("taskkill /im chrome.exe /f > nul 2>&1")
                    
                elif "close youtube" in command:
                    self.speak("closing YouTube.")
                    os.system("taskkill /im chrome.exe /f > nul 2>&1")
                    
                elif "stop song" in command:
                    self.speak("Stopping song.", "assistant")
                    os.system("taskkill /im chrome.exe /f > nul 2>&1")
                    
                elif "close it" in command:
                    self.speak("Closing it.")
                    pyautogui.hotkey('alt', 'f4')
                    
                elif "close " in command.lower():
                    command = command.replace("close", "").strip()
                    
                    # Mapping common app names to process names
                    app_processes = {
                        "chrome": "chrome.exe",
                        "google chrome": "chrome.exe",
                        "notepad": "notepad.exe",
                        "word": "WINWORD.EXE",
                        "excel": "EXCEL.EXE",
                        "powerpoint": "POWERPOINT.EXE",
                        "vlc": "vlc.exe",
                        "spotify": "Spotify.exe",
                        "calculator": "Calculator.exe",
                        "file explorer": "explorer.exe",
                        "settings": "SystemSettings.exe",
                        "anydesk": "AnyDesk.exe",
                        "asus framework service": "ASUSFramework.exe",
                        "aura service": "AURACraterService.exe",
                        "cisco packet tracer": "PacketTracer.exe",
                        "epic games launcher": "EpicGamesLauncher.exe",
                        "google": "chrome.exe",
                        "microsoft edge": "msedge.exe",
                        "microsoft office": "WINWORD.EXE",  # Default to Word; add specific apps if needed
                        "microsoft onedrive": "OneDrive.exe",
                        "microsoft visual studio code": "Code.exe",
                        "nvidia app": "NVIDIASettings.exe",
                        "nvidia graphics driver": "NVDisplay.Container.exe",
                        "pycharm": "pycharm64.exe",
                        "python": "python.exe",
                        "remote desktop connection": "mstsc.exe",
                        "respondus lockdown browser": "LockDownBrowser.exe",
                        "riot client": "RiotClientServices.exe",
                        "steam": "steam.exe",
                        "valorant": "VALORANT.exe",
                        "vlc media player": "vlc.exe",
                        "winrar": "winrar.exe",
                        "youtube": "chrome.exe",  # Typically run via browser
                        "zoom": "Zoom.exe",
                    }

                    # Check if the app is in the list of known processes
                    if command in app_processes:
                        process_name = app_processes[command]
                        os.system(f"taskkill /im {process_name} /f > nul 2>&1")
                        self.speak(f"closed.")
                        continue
                    else:
                        continue
                        
                elif "stop all" in command.lower():
                    self.speak("Stopping all processes.")
                    os.system("taskkill /im chrome.exe /f")  # Closes browsers
                    os.system("taskkill /im AcroRd32.exe /f > nul 2>&1")  # Closes PDF reader
                    pyautogui.hotkey('alt', 'f4')  # Closes active windows
                    self.speak("All open applications have been closed.")
                    
                elif "the time" in command:
                    str_time = datetime.now().strftime("%H:%M:%S")
                    self.ui.add_to_output(f"The time is {str_time}.", "assistant")
                    self.speak(f"The time is {str_time}.")
                
                elif "the date" in command:
                    str_date = datetime.now().strftime("%Y-%m-%d")
                    self.ui.add_to_output(f"Today's date is {str_date}.", "assistant")
                    self.speak(f"Today's date is {str_date}.")

                elif "take a screenshot" in command:
                    self.takeScreenshot()

                elif "start screen recording" in command:
                    self.startScreenRecording()

                elif 'stop screen recording' in command.lower():
                    self.stopScreenRecording()

                elif "wake up" in command:
                        self.ui.add_to_output("SAM is waking up!", "assistant")
                        self.speak("I'm awake now! How can I assist you?")
                        self.ui.show_ui()  # Show the UI again
                        self.assistant_active = True
                        self.ui.mic_button.configure(bg="#2563eb")  # Mark mic button as active
                        self.ui.listening_frame.grid()  # Show listening indicator
                        self.start_listening_thread()  # Restart the listening thread

                elif "bye-bye" in command.lower():
                    self.ui.add_to_output("SAM: Goodbye! Have a great day!", "assistant")
                    self.speak("Goodbye! Have a great day!")
                    self.ui.quit()
                
                elif "shutdown system" in command:
                    self.speak("Shutting down the system.")
                    os.system("shutdown /s /t 1")

                elif "restart system" in command:
                    self.speak("Restarting the system.")
                    os.system("shutdown /r /t 1")

                elif "logout system" in command or "lock system" in command:
                    self.speak("Logging out the current user.")
                    os.system("shutdown /l")   
            except queue.Empty:
                continue   
            
            except Exception as e:
                # Log the error for debugging
                print(f"Error occurred: {e}")
                #self.ui.add_to_output("An error occurred. Resetting the assistant...", "assistant")
                #self.speak("An error occurred. Resetting the assistant...")

                # Reset the assistant state
                self.reset_assistant()

    def reset_assistant(self):
        """Reset the assistant to its initial state."""
        self.assistant_active = False
        self.is_listening = True
        self.is_speaking = False
        self.is_sleeping = False
        self.command_queue = queue.Queue()  # Clear the command queue

        # Restart the listening thread
        self.start_listening_thread()
        #self.ui.add_to_output("Assistant has been reset. Ready to assist you.", "assistant")
        #self.speak("Assistant has been reset. Ready to assist you.")