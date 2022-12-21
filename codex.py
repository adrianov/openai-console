#!/usr/bin/python3

"""OpenAI API wrapper"""

import os
import logging
import re
import openai
from prompt_toolkit import PromptSession
from whats_that_code.election import guess_language_all_methods
import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters.terminal import TerminalFormatter

openai.api_key = os.environ.get("OPENAI_ACCESS_TOKEN")
MODEL_ENGINE = "code-davinci-002"

logging.basicConfig(
    filename=os.path.expanduser("~/code-davinci.log"), level=logging.INFO
)


def generate_response(prompt_text):
    """Generate response using OpenAI API"""
    completions = openai.Completion.create(
        engine=MODEL_ENGINE,
        prompt=prompt_text,
        max_tokens=4000,
        n=1,
        temperature=0.5,
        stop=stop_signature(prompt_text),
    )

    return completions.choices[0].text


def pygmentize(text):
    """Pygmentize the given text"""
    try:
        lexer = get_lexer_by_name(guess_language_all_methods(text))
    except pygments.util.ClassNotFound:
        lexer = guess_lexer(text)
    return pygments.highlight(text, lexer, TerminalFormatter())


def print_answer(answer):
    """Print the answer"""
    print(pygmentize(answer))
    print("\n")


def stop_signature(question):
    """The model tends to repeat itself sometimes. This is a workaround to stop it"""
    return re.search(r"\S+\s*\S*\s*\S*", question).group()


def prepare_question(question):
    """Prepare the question. Inline file contents to the question"""

    # skip if there are no filenames
    if not re.search(r"\/\w", question):
        return question

    lines = question.splitlines()

    # get list of files in home directory descending to inner directories
    if not hasattr(prepare_question, "files"):
        files = []
        for root, _, filenames in os.walk(os.path.expanduser("~")):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        prepare_question.files = files

    for line in lines:
        if any(filename == line.strip() for filename in prepare_question.files):
            with open(line.strip(), "r") as file:
                lines[lines.index(line)] = f"# {line}\n```\n" + file.read() + "\n```\n"

    return "\n".join(lines)


session = PromptSession()

print(f"Session with {MODEL_ENGINE} model.")
print("Press Esc, Enter to finish multiline input. Empty string to exit.\n")

while True:
    question = session.prompt("Q: ", multiline=True)

    if not question.strip():
        break

    question = prepare_question(question)

    logging.info("Q: %s\n", question)
    print("A:\n", end="")
    response = generate_response(question)
    logging.info("A:\n%s\n\n", response)
    print_answer(response)
