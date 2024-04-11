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
        messages=messages,
        max_tokens=100  # You can adjust this based on the desired response length
    )

    # Extract command sequence from the model's response
    raw_response_content = response['choices'][0]['message']['content']

    # Split the commands by commas or periods (in case the model gives a sentence-like response)
    command_list = [cmd.strip() for cmd in re.split(',|\.|\n', raw_response_content) if cmd.strip()]

    # Translate the raw commands to known commands
    translated_commands = [translate_to_known_command(command) for command in command_list if translate_to_known_command(command)]

    return translated_commands
def main():
    try:
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

        # Start the video feed sequentially to avoid overloading the system
        listen_to_commands_thread.join()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()