import openai

# Initialize OpenAI API (Ensure you set up your API key)
openai.api_key = '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'

# Define the patterns dictionary to store patterns
patterns = {
    "box": [],
    "circle": []
}

def get_pattern_commands(pattern_name):
    """
    Function to get drone commands for a specific pattern using OpenAI.
    """
    
    # Define structured prompts for known patterns
    prompts = {
        "box": """
        Generate a sequence of commands to make a drone fly in a box pattern. The drone should:
        1. Take off
        2. Move forward
        3. Move right
        4. Move forward
        5. Move right
        6. Move forward
        7. Move right
        8. Move forward
        9. Land
        """,
        
        "circle": """
        Generate a sequence of commands to make a drone fly in a circular pattern. The drone should:
        1. Take off
        2. Gradually move forward while slowly turning right continuously until a circle is completed
        3. Land
        """
    }
    
    # If the pattern is a known one
    if pattern_name in prompts:
        prompt = prompts[pattern_name]
    else:
        # If the pattern is unknown, ask OpenAI to come up with the pattern
        prompt = f"Generate a sequence of commands to make a drone fly in a {pattern_name} pattern."
    
    # Query OpenAI to get the pattern commands
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=150)
    commands = response.choices[0].text.strip().split("\n")
    
    return commands

def execute_pattern(pattern_name):
    """
    Function to execute a drone pattern.
    """
    
    # If the pattern is not already in the patterns dictionary, get it from OpenAI
    if not patterns[pattern_name]:
        patterns[pattern_name] = get_pattern_commands(pattern_name)
    
    # Execute the pattern
    for command in patterns[pattern_name]:
        print(f"Executing command: {command}")
        # Here, you can replace the print statement with actual drone command execution
        # For example: drone.execute(command)

# Example Usage
execute_pattern("box")
execute_pattern("circle")
# For a new pattern
execute_pattern("zigzag")  # This will prompt OpenAI to come up with a zigzag pattern
