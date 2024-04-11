
import cv2
import torch
import openai
from djitellopy import Tello
import azure.cognitiveservices.speech as speechsdk
import threading
import time

#########################
# SETUP
#########################

# Constants
YOLO_MODEL = 'ultralytics/yolov5s'
AZURE_SUBSCRIPTION_KEY = '55f2007ae13640a59b52e03dad3361ea'
AZURE_SERVICE_REGION = 'https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken'  # e.g., 'westus'
OPENAI_API_KEY = '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'
TELLO_IP = '192.168.86.39'


# --- TELLO DRONE SETUP ---
tello = Tello(TELLO_IP)
tello.connect()
tello.streamoff()
tello.streamon()

# Assuming you initialize drone_state as 'landed' or 'flying' elsewhere in your script
in_flight = False

# Check CUDA availability
USE_CUDA = torch.cuda.is_available()
DEVICE = 'cuda:0' if USE_CUDA else 'cpu'

# Setup YOLOv5
print("Setting up YOLOv5...")
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(DEVICE)
if USE_CUDA:
    model = model.half()  # Half precision improves FPS
print("YOLOv5 setup complete.")

# Setup Azure Speech SDK
print("Setting up Azure Speech SDK...")
speech_config = speechsdk.SpeechConfig(subscription='55f2007ae13640a59b52e03dad3361ea', endpoint="https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken")
voice_config = speechsdk.SpeechConfig(subscription='55f2007ae13640a59b52e03dad3361ea', endpoint="https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken")
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
print("Azure Speech SDK setup complete.")

# Setup OpenAI API
print("Setting up OpenAI...")
openai.api_key = OPENAI_API_KEY
print("OpenAI setup complete.")

# ACTIONS TO COMMANDS MAPPING
ACTIONS_TO_COMMANDS = {
    ("start", "fly", "take off", "lift off", "launch", "begin flight", "skyward"): "takeoff",
    ("land", "settle", "touch down", "finish", "end flight", "ground"): "land",
    ("front flip", "forward flip"): "flip",
    ("forward", "move ahead", "go straight", "advance", "head forward", "proceed front", "go on", "move on"): "move_forward",
    ("backward", "move back", "retreat", "go backward", "back up", "reverse", "recede"): "move_back",
    ("left", "move left", "go leftward", "turn leftward", "shift left", "sidestep left"): "move_left",
    ("right", "move right", "go rightward", "turn rightward", "shift right", "sidestep right"): "move_right",
    ("move up", "up", "ascend", "rise", "climb", "skyrocket", "soar upwards", "elevate"): "move_up",
    ("move down", "down", "descend", "lower", "sink", "drop", "fall", "decline"): "move_down",
    ("spin right", "rotate clockwise", "turn right", "twirl right", "circle right", "whirl right", "swirl right"): "rotate_clockwise",
    ("spin left", "rotate counter-clockwise", "turn left", "twirl left", "circle left", "whirl left", "swirl left"): "rotate_counter_clockwise",
    ("back flip", "flip back"): "flip_backward",
    ("flip", "forward flip", "flip forward"): "flip_forward",
    ("right flip", "flip to the right", "sideways flip right"): "flip_right",
    ("video on", "start video", "begin stream", "camera on"): "streamon",
    ("video off", "stop video", "end stream", "camera off"): "streamoff",
    ("go xyz", "specific move", "exact move", "precise direction", "navigate xyz"): "go_xyz_speed"
}

#########################
# FUNCTIONS
#########################


def interpret_command_to_drone_action(command):
    for action_phrases, action in ACTIONS_TO_COMMANDS.items():
        if command in action_phrases:
            return action
    return None

def generate_drone_command(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=50
    )
    return response.choices[0].text.strip()

def execute_drone_commands(commands):
    global in_flight

    for command in commands:
        drone_command = interpret_command_to_drone_action(command)

        if drone_command:
            print(f"\nExecuting command: {drone_command}")
            try:
                execute_drone_command(drone_command)
                # Update the flight state based on executed commands
                if command == "takeoff":
                    if not in_flight:
                        tello.takeoff()
                        in_flight = True
                elif command == "land":
                    if in_flight:
                        tello.land()
                        in_flight = False
                elif in_flight:  # Only execute the following commands if the drone is in flight
                    if command == "move_forward":
                        tello.move_forward(20)
                elif command == "move_forward":
                    tello.move_forward(20)  # Default to 20 cm. Adjust as needed.
                elif command == "move_back":
                    tello.move_back(20)
                elif command == "move_left":
                    tello.move_left(20)
                elif command == "move_right":
                    tello.move_right(20)
                elif command == "move_up":
                    tello.move_up(20)
                elif command == "move_down":
                    tello.move_down(20)
                elif command == "rotate_clockwise":
                    tello.rotate_clockwise(90)
                elif command == "rotate_counter_clockwise":
                    tello.rotate_counter_clockwise(90)
                elif command == "flip":
                    tello.flip("f")  # Default to forward flip. Adjust as needed.
                elif command == "flip_backward":
                    tello.flip('b')
                elif command == "flip_right":
                    tello.flip('r')
                elif command == "streamon":
                    tello.streamon()
                elif command == "streamoff":
                    tello.streamoff()
                elif command == "go_xyz_speed":
                    x, y, z, speed = 20, 20, 20, 10
                    tello.go_xyz_speed(x, y, z, speed)
                else:
                    print(f"Unknown command: {command}")
            except Exception as e:
                print(f"Error executing the command: {e}")
        else:
            print(f"\nCould not interpret the command: {command}")

def command_listener():
    try:
        while True:
            command_heard = ""  # Initialize it at the start of the loop
            print("\nAwaiting command...")

            result = speech_recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                try:
                    command_heard = result.text.lower().strip('.')
                    print(f"\nHeard: {command_heard}")
                except Exception as e:  # Using a more generic exception to catch any unexpected errors
                    print(f"Error processing heard command: {e}")
                    command_heard = ""

                if "give me stats" in command_heard:
                    stats = get_drone_status()
                    print(stats)
                    continue

                execute_drone_commands([command_heard])

            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("\nNo speech could be recognized.")

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"\nSpeech Recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation.error_details}")

            # Check for a command to end the program gracefully
            if "terminate program" in command_heard:
                print("Terminating program...")
                break

    except Exception as e:
        print(f"Error in recognizing speech: {e}")

def get_drone_status():
    try:
        # Get various drone parameters using the Tello API
        battery_level = tello.get_battery()
        flight_time = tello.get_flight_time()
        pitch = tello.get_pitch()
        roll = tello.get_roll()
        barometer = tello.get_barometer()
        flight_distance = tello.get_distance_tof()

        # Format the status message
        status_message = (
            f"Drone Status:\n"
            f"Battery Level: {battery_level}%\n"
            f"Flight Time: {flight_time} seconds\n"
            f"Pitch: {pitch}°\n"
            f"Roll: {roll}°\n"
            f"Barometer: {barometer}cm\n"
            f"Flight Distance (ToF): {flight_distance}cm"
        )

        return status_message

    except Exception as e:
        print(f"Error getting drone status: {e}")
        return "Error getting drone status."

def main():
    try:
        # Start listening for voice commands
        listen_to_commands_thread = threading.Thread(target=command_listener)
        listen_to_commands_thread.start()
        time.sleep(5)  # Give a 5-second buffer before starting the video feed

        # Start the video feed sequentially to avoid overloading the system
        start_video_feed()
        time.sleep(5)  # Give a 5-second buffer before starting the video feed

        # Get the drone's status
        stats = get_drone_status()
        print(stats)

        # Start the video feed sequentially to avoid overloading the system
        listen_to_commands_thread.join()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()