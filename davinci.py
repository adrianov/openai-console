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
        prompt_text = prepare_question(prompt_text)
        completions = openai.Completion.create(
            engine=MODEL_ENGINE, prompt=prompt_text, max_tokens=1024, n=1, temperature=0.5
        )
        response = completions.choices[0].text
    except openai.error.OpenAIError as e:
        response = f"\033[31m{e.__class__.__name__}\033[0m: {e}"

    return response

def prepare_question(question):
    """Prepare the question. Inline file contents to the question"""
    if is_search_needed(question) and are_search_utils_installed():
        search_data = search_question(question)
        return f'"""\n{search_data}\n"""\n{question}"'
    return question

def is_search_needed(question):
    if '\n' in question.strip():
        return False
    search_words = r'search|today|current|now|up to date|recent|latest|найди|сегодня|сейчас|текущий|актуальный'
    return bool(re.search(search_words, question, flags=re.IGNORECASE))

def are_search_utils_installed():
    """Check if ddgr is installed"""
    import shutil
    return shutil.which('ddgr')

def search_question(query):
    """Search the given query using ddgr"""
    import shlex
    import subprocess
    import json
    command = f'ddgr -n 10 --json {shlex.quote(query)}'
    output = subprocess.check_output(command, shell=True).decode('utf-8')
    results = []
    decoded_output = json.loads(output)
    for result in decoded_output:
        results.append(result['abstract'])
    print(f"Search results:\n")
    print_answer("\n".join(results))
    return "\n".join(results)

def pygmentize(text):
    """Pygmentize the given text"""
    if '\x1b[' in text:
        return text
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
        if len_without_ansi(line) <= max_width:
            result.append(line)
        else:
            words = re.findall(r"\s+|\S+", line)
            current_line = ""
            line_len = 0
            for word in words:
                word_len = len_without_ansi(word)
                if line_len + word_len > max_width:
                    if current_line:
                        result.append(current_line)
                    current_line = word.strip()
                    line_len = len_without_ansi(current_line)
                else:
                    current_line += word
                    line_len += word_len
            if current_line:
                result.append(current_line)
    return "\n".join(result)

def len_without_ansi(text):
    """Return the length of the given text without ANSI codes"""
    return len(re.sub(r'\x1b[^m]*m', '', text))


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
