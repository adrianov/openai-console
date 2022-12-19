#!/usr/bin/python3

"""OpenAI API wrapper"""

import os
import re
import openai
from prompt_toolkit import PromptSession
import pygments
from pygments.lexers import guess_lexer
from pygments.formatters.terminal import TerminalFormatter

openai.api_key = os.environ.get("OPENAI_ACCESS_TOKEN")
MODEL_ENGINE = "text-davinci-003"
# MODEL_ENGINE = "code-davinci-002"


def generate_response(prompt_text):
    """Generate response using OpenAI API"""
    completions = openai.Completion.create(
        engine=MODEL_ENGINE, prompt=prompt_text, max_tokens=1024, n=1, temperature=0.5
    )

    return completions.choices[0].text


def pygmentize(text):
    """Pygmentize the given text"""
    lexer = guess_lexer(text)
    return pygments.highlight(text, lexer, TerminalFormatter())


def print_answer(answer):
    """Print the answer"""
    width, _ = os.get_terminal_size()
    print(pygmentize(wrap_text(answer, width)))
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
                if len(current_line) + len(word) > max_width:
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
print("Press Esc, Enter to finish multiline input.\n")

while True:
    question = session.prompt("Q: ", multiline=True)

    if not question.strip():
        break

    print("A:\n", end="")
    response = generate_response(question)
    print_answer(response)
