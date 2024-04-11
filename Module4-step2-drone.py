import cv2
import torch
import openai
import os
import re
import threading
import time
from djitellopy import Tello
import azure.cognitiveservices.speech as speechsdk

# Global definitions and initializations
YOLO_MODEL = 'ultralytics/yolov5s'
AZURE_SUBSCRIPTION_KEY = '55f2007ae13640a59b52e03dad3361ea'
AZURE_SERVICE_REGION = 'https://northcentralus.api.cognitive.microsoft.com/sts/v1.0/issuetoken'
OPENAI_API_KEY = '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'
TELLO_IP = '192.168.86.39'
openai.api_key = OPENAI_API_KEY

# Drone setup
tello = Tello(TELLO_IP)
tello.connect()
tello.streamoff()
tello.streamon()
in_flight = False

# YOLOv5 setup
USE_CUDA = torch.cuda.is_available()
DEVICE = 'cuda:0' if USE_CUDA else 'cpu'
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(DEVICE)
if USE_CUDA:
    model = model.half()

# Azure Speech SDK setup
speech_config = speechsdk.SpeechConfig(subscription=AZURE_SUBSCRIPTION_KEY, endpoint=AZURE_SERVICE_REGION)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

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

def translate_to_known_command(response):
    for key in ACTIONS_TO_COMMANDS.keys():
        for action in key:
            if action in response:
                return ACTIONS_TO_COMMANDS[key]
    return response  # Return original response if no known command found

def generate_drone_commands(pattern):
    messages = [
        {"role": "system", "content": "You are a drone flight assistant. Generate a sequence of actionable drone commands."},
        {"role": "user", "content": f"Provide specific drone commands to fly in a {pattern} pattern."}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    # Extract command sequence from the model's response
    raw_response_content = response.choices[0].message['content']

    # Split the commands by commas or periods (in case the model gives a sentence-like response)
    command_list = [cmd.strip() for cmd in re.split(',|\.|\n', raw_response_content) if cmd.strip()]

    # Translate the raw commands to known commands
    translated_commands = [translate_to_known_command(command) for command in command_list if translate_to_known_command(command) in ACTIONS_TO_COMMANDS.values()]

    # Remove consecutive takeoff or land commands to avoid unwanted drone behavior
    final_commands = []
    prev_command = None
    for command in translated_commands:
        if command == "takeoff" and prev_command != "land":
            final_commands.append(command)
        elif command == "land" and prev_command != "takeoff":
            final_commands.append(command)
        elif command not in ["takeoff", "land"]:
            final_commands.append(command)
        prev_command = command

    return final_commands

def execute_commands(commands):
    for command in commands:
        print(f"Executing command: {command}")
        if "takeoff" in command.lower():
            tello.takeoff()
            time.sleep(5)
        elif "land" in command.lower():
            tello.land()
            time.sleep(5)
        elif "move_forward" in command.lower():
            tello.move_forward(20)
            time.sleep(3)
        elif "move_right" in command.lower():
            tello.move_right(20)
            time.sleep(3)
        elif "move_left" in command.lower():
            tello.move_left(20)
            time.sleep(3)
        elif "move_back" in command.lower():
            tello.move_back(20)
            time.sleep(3)
        elif "move_up" in command.lower() or "ascend" in command.lower():
            tello.move_up(20)
            time.sleep(3)
        elif "move_down" in command.lower() or "descend" in command.lower():
            tello.move_down(20)
            time.sleep(3)
        else:
            print(f"Unrecognized command: {command}")



def translate_to_known_command(response):
    for key in ACTIONS_TO_COMMANDS.keys():
        for action in key:
            if action in response:
                return ACTIONS_TO_COMMANDS[key]
    return response  # Return original response if no known command found


def generate_drone_commands(pattern):
    messages = [
        {"role": "system", "content": "You are a drone flight assistant. Generate a sequence of actionable drone commands."},
        {"role": "user", "content": f"Provide specific drone commands to fly in a {pattern} pattern."}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Specifying the model
        messages=messages
    )

    # Extract command sequence from the model's response
    raw_response_content = response.choices[0].message['content']

    # Split the commands by commas or periods (in case the model gives a sentence-like response)
    command_list = [cmd.strip() for cmd in re.split(',|\.|\n', raw_response_content) if cmd.strip()]

    # Translate the raw commands to known commands
    translated_commands = [translate_to_known_command(command) for command in command_list if translate_to_known_command(command)]

    return translated_commands


def main():
    print("/Users/sbarr/Downloads/Summer-Drone-Capstone/Capstone-2023---Drones/Module4-Step3-OpenAI-Drone.py")
    
    mode = input("Enter 'voice' for voice commands or 'pattern' for pattern flight: ").lower()

    if mode == 'voice':
        # Start listening for voice commands
        listen_to_commands_thread = threading.Thread(target=listen_to_commands)

        listen_to_commands_thread.start()
        time.sleep(5)  # Give a 5-second buffer before starting the video feed
    
        # Start the video feed sequentially to avoid overloading the system
        start_video_feed()
        time.sleep(5)  # Give a 5-second buffer before starting the video feed
    
        # Get the drone's status
        stats = get_drone_status()
        print(stats)
    
        # Wait for the listen_to_commands thread to finish
        listen_to_commands_thread.join()

    elif mode == 'pattern':
        desired_pattern = input("Enter the desired pattern (e.g., 'box'): ")
        
        if not desired_pattern:
            print("No pattern provided!")
            return

        drone_commands = generate_drone_commands(desired_pattern)
        
        print("\nCommands for the drone to execute:")
        for command in drone_commands:
            print(command)
        
        input("Press Enter to start executing commands...")
        execute_commands(drone_commands)

    else:
        print("Invalid mode selected!")

if __name__ == "__main__":
    main()
