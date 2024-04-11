import openai
import os

# Initialize the OpenAI API 
openai.api_key = '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'

PROMPT_STYLES = {
    "1": {
        "desc": "One-word answer", 
        "template": "{message}",
        "prompt_modifier": "Answer in one word:"
    },
    "2": {
        "desc": "Bullet-point response", 
        "template": "• {message}",
        "prompt_modifier": "List the answer(s) in bullet points:"
    },
    "3": {
        "desc": "Table format", 
        "template": "| Response |\n|----------|\n| {message} |",
        "prompt_modifier": "Provide a concise answer suitable for a table format:"
    },
    "4": {
        "desc": "Long repsonse answer", 
        "template": "{message}",
        "prompt_modifier": "Answer in well thought out paragraph:"
    }
}

def get_gpt_response(user_input, style):
    """
    Get a response from GPT based on user input and style.

    Parameters:
    - user_input (str): The input string to be provided to the GPT model.
    - style (str): The style to use for formatting the output.

    Returns:
    - str: The model's response formatted based on the chosen style.
    """
    # Modify the prompt based on the desired style
    prompt = f"{PROMPT_STYLES[style]['prompt_modifier']} {user_input}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    gpt_message = response['choices'][0]['message']['content']
    return PROMPT_STYLES[style]['template'].format(message=gpt_message)

def interactive_chat_with_gpt():
    """
    Start an interactive chat session with GPT.

    Provides a loop where the user can continually input queries and receive responses from GPT based on the chosen style.
    """
    print("Interactive chat with GPT started! (Type 'exit' to stop)\n")
    
    # Display style options
    for key, style in PROMPT_STYLES.items():
        print(f"{key}. {style['desc']}")
    
    style_choice = input("\nChoose a response style from the list above (e.g., '1'): ")

    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            print("Exiting chat. Goodbye!")
            break
        
        gpt_response = get_gpt_response(user_input, style_choice)
        print(f"\nGPT: {gpt_response}\n")

# Starting the interactive session
interactive_chat_with_gpt()
