# pattern_templates = {
#     "box": "Please provide a sequence of drone commands to execute a box flight pattern.",
#     "circle": "Please provide a sequence of drone commands to execute a circular flight pattern."
# }
import openai
import os
import re

# Initialize the OpenAI API 
openai.api_key = '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'

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
def execute_commands(commands):
    for command in commands:
        print(f"Executing command: {command}")
        # Add logic to execute the drone command here
        input("Press Enter to continue...")  # Wait for user confirmation
        os.system('clear')  # Clear the console screen to keep it clean

def main():
    print("/Users/sbarr/Downloads/Summer-Drone-Capstone/Capstone-2023---Drones/Module4-Step3-OpenAI-Drone.py")
    desired_pattern = input("Enter the desired pattern (e.g., 'box'): ")
    
    if not desired_pattern:
        print("No pattern provided!")
        return

    drone_commands = generate_drone_commands(desired_pattern)
    
    print("\nCommands for the drone to execute:")
    for command in drone_commands:
        print(command)
    
    input("Press Enter to start executing commands...")
    #os.system('clear')  # Clear the console screen
    execute_commands(drone_commands)

if __name__ == "__main__":
    main()
