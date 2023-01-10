#!/usr/bin/python3

"""OpenAI API wrapper"""

import os
import re
import logging
import openai
from prompt_toolkit import PromptSession
from whats_that_code.election import guess_language_all_methods
import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters.terminal import TerminalFormatter

openai.api_key = os.environ.get("OPENAI_ACCESS_TOKEN")
MODEL_ENGINE = "text-davinci-003"
# MODEL_ENGINE = "code-davinci-002"

logging.basicConfig(filename=os.path.expanduser('~/davinci.log'), level=logging.INFO)

def generate_response(prompt_text):
    """Generate response using OpenAI API"""
    try:
        completions = openai.Completion.create(
            engine=MODEL_ENGINE, prompt=prompt_text, max_tokens=1024, n=1, temperature=0.5
        )
        response = completions.choices[0].text
    except openai.error.OpenAIError as e:
        response = f"{e.__class__.__name__}: {e}"

    return response

def pygmentize(text):
    """Pygmentize the given text"""
    try:
        lexer = get_lexer_by_name(guess_language_all_methods(text))
    except pygments.util.ClassNotFound:
        lexer = guess_lexer(text)
    return pygments.highlight(text, lexer, TerminalFormatter())

def print_answer(answer):
    """Print the answer"""
    width, _ = os.get_terminal_size()
    print(wrap_text(pygmentize(answer), width))
    print("\n")


def wrap_text(text, max_width):
    """Wrap the given text"""
    lines = text.split("\n")
    result = []
    for line in lines:
        if len(line) <= max_width:
            result.append(line)
        else:
            words = re.findall(r"\s+|\S+", line)
            current_line = ""
            for word in words:
                # Exclude ANSI color codes from a word length
                if len(re.sub(r'\x1b[^m]*m', '', current_line + word)) > max_width:
                    if current_line:
                        result.append(current_line)
                    current_line = word.strip()
                else:
                    current_line += word
            if current_line:
                result.append(current_line)
    return "\n".join(result)


session = PromptSession()

print(f"Session with {MODEL_ENGINE} model.")
print("Press Esc, Enter to finish multiline input. Empty string to exit.\n")

while True:
    question = session.prompt("Q: ", multiline=True)

    if not question.strip():
        break

    logging.info("Q: %s\n", question)
    print("A:\n", end="")
    response = generate_response(question)
    logging.info("A:\n%s\n\n", response)
    print_answer(response)
