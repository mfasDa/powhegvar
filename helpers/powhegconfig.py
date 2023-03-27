#! /usr/bin/env python3

def replace_value(input: str, newvalue: str):
    command = input
    if "!" in command:
        command = command[:command.find("!")-1]
    if "#" in command:
        command = command[:command.find("#")-1]
    tokens = command.split(" ")
    stripped_tokens = []
    for tok in tokens:
        if len(tok):
            stripped_tokens.append(tok)
    oldvalue = stripped_tokens[1]
    print(f"Replaceing {oldvalue} with {newvalue}")
    output = input.replace(oldvalue, newvalue)
    print(f"New line: {output}")
    return output