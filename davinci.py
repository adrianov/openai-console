#!/usr/bin/python3

"""OpenAI API wrapper"""

import os
import re
import logging
import openai
import time
import subprocess
from sys import getsizeof
from duckpy import Client
from prompt_toolkit import PromptSession
from whats_that_code.election import guess_language_all_methods
import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters.terminal import TerminalFormatter

openai.api_key = os.environ.get("OPENAI_ACCESS_TOKEN")
MODEL_ENGINE = "gpt-3.5-turbo"
#MODEL_ENGINE = "text-davinci-003"

logging.basicConfig(filename=os.path.expanduser('~/davinci.log'), level=logging.INFO)

def generate_response(prompt_text):
    """Generate response using OpenAI API"""
    try:
        response = ask_question(prompt_text)
    except openai.error.OpenAIError as e:
        response = f"\033[31m{e.__class__.__name__}\033[0m: {e}"

    return response

def query_ai(prompt_text):
    e = None
    for _ in range(3):
        try:
            completions = openai.ChatCompletion.create(
                model=MODEL_ENGINE, messages=[{"role":"user", "content": prompt_text}]
            )
            return completions.choices[0].message.content
        except openai.error.OpenAIError as e:
            if not isinstance(e, openai.error.RateLimitError):
                raise e
            time.sleep(5)
    raise e

def ask_question(question):
    """Ask the given question."""
    if response := calculate(question):
        return str(response)

    if response := solve_eq(question):
        return str(response)

    if is_translation(question):
        return translate(question)

    if is_search_needed(question):
        search_data = search_question(question)
        prompt_text = f'"""\n{search_data}"""\n{question}"'
        return query_ai(prompt_text)

    return query_ai(question)

def calculate(string):
    # Check if the string contains only numbers and arithmetic operators
    if not all(c in '0123456789+-*/(). \n' for c in string):
        return False

    # Calculate the result of the arithmetic expression
    try:
        result = eval(string)
    except:
        return False

    # Return the result
    return result

def solve_eq(eq):
    if '=' not in eq:
        return False
    from sympy import Eq, sympify, solve
    try:
        lhs, rhs = eq.split('=')
        lhs = sympify(lhs)
        rhs = sympify(rhs)
        solution = solve(Eq(lhs, rhs))
        return solution
    except:
        return False

def is_search_needed(question):
    """Check if the search is needed"""
    if '\n' in question.strip():
        return False
    if re.search(r'\b[A-Z]{3}\b|\$|??|???|???', question):
        return True
    search_words = r'search|find|today|current|now|up to date|recent|latest|news|??????????|??????????|????????????|????????????|??????????|????????????????|????????????'
    return bool(re.search(search_words, question, flags=re.IGNORECASE))

def is_translation(question):
    return is_program_installed('trans') and bool(re.search(r'^(trans|??????????)', question.strip(), flags=re.IGNORECASE))

def is_program_installed(program_name):
    """Check whether program_name is installed."""
    import shutil
    return shutil.which(program_name) is not None

def translate(question):
    params = ['trans', '-b']
    question = re.sub(r'\b(trans|??????????)\w*\s+', '', question, flags=re.IGNORECASE).strip()
    # If no Russian letters, translate to Russian
    if not bool(re.search('[\u0400-\u04FF]', question)):
        params.append(':ru')
    params.append(question)
    result = subprocess.run(params, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def search_question(query):
    """Search the given query using DuckDuckGo"""
    client = Client()
    results = client.search(query)
    answers = ""
    for result in results:
        answers += result.description + "\n"
        if getsizeof(answers) > 4600:
            break
    logging.info("Search answers:\n%s", answers)
    return answers

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
    if is_search_needed(question):
        print("A + Internet search:\n", end="")
    else:
        print("A:\n", end="")
    response = generate_response(question)
    logging.info("A:\n%s\n\n", response)
    print_answer(response)
