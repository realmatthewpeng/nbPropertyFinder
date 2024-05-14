import io
import json
import re
import subprocess
import tempfile as tmp
import nbformat

from collections import defaultdict

TEST_NB = "./infer_test.ipynb"

def main():
    nb = nbformat.read(TEST_NB, as_version=4)
    infer_processNotebook(nb)

def infer_processNotebook(nb):
    with open('test.py', 'w') as f:
        for cell in nb["cells"]:
            if cell["cell_type"] == "code":
                source: str = cell['source']
                f.write(f"{source}\n")
    pyright_run(open("./test.py").read())
    inferred = pyright_infer(open("./test.py").read(), [
        ("aapl", 12),
        ])
    print(inferred)

def clearFile():
    open('test.py', 'w').close()

global_id = 0
global_target_to_expr = {}

def buildNotebook(source_split, exprs):
    global global_id
    global global_target_to_expr
    with open('test.py', 'a') as f:
        f.write("\n")
        # print(source_split)
        for ln_no, source_line in enumerate(source_split):
            ln_no = ln_no + 1
            indent_level = len(source_line) - len(source_line.lstrip())
            indent = indent_level * " "
            f.write(f"{source_line}\n")
            for target_expr in exprs[ln_no]:
                target_name = f"__infer_target_{global_id}__{ln_no}"
                global_id = global_id + 1
                global_target_to_expr[target_name] = target_expr
                f.write(f"{indent}{target_name} = {target_expr}")
                f.write(f"\n{indent}reveal_type({target_name})\n\n")
        f.write("\n")    

def pyright_run_default():
    pyright_cmd_base = ['pyright', '--outputjson']
    global global_target_to_expr
    result_json = None
    try:
        result = subprocess.run([*pyright_cmd_base, "test.py"], check=True, capture_output=True)
        result_json = json.loads(result.stdout)
    except subprocess.CalledProcessError as cpe:
        # print("RETURNING ERROR")
        # print(cpe)
        result_json = json.loads(cpe.output.decode())

    pattern = r'Type of "(?P<target>\w+)" is "(?P<type>.+?)"'
    regex = re.compile(pattern)
    
    informations = defaultdict(list)
    inferred_types = dict.fromkeys(global_target_to_expr)
    
    for diagnostic in result_json['generalDiagnostics']:
        # print(diagnostic)
        if diagnostic['severity'] == 'information':
            message = diagnostic['message']
            if (match := regex.fullmatch(message)):
                target_name = match.group("target")
                inferred_type = match.group("type")
                lineno = re.match('.*?([0-9]+)$', target_name).group(1)
                informations[global_target_to_expr[target_name]].append((inferred_type, lineno))
            else:
                continue

    return informations

def pyright_run(source: str):
    pyright_cmd_base = ['pyright', '--outputjson']
    with tmp.NamedTemporaryFile(mode='w', suffix=".py") as file:
        file.write(source)
        file.flush()

        try:
            result = subprocess.run([*pyright_cmd_base, file.name], check=True, capture_output=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as cpe:
            # print("RETURNING ERROR")
            # print(cpe)
            return json.loads(cpe.output.decode())

def pyright_infer(source: str, targets: list[tuple[str, int]]):
    """
    Infers types for expressions. Each target may have a line number specified, in which case the
    type revelation is inserted after that line. If None, it's inserted at the end.

    :param source: original source to infer
    :param targets: list of target expressions to infer, and the line to do so after (or None for EOF).
    """
    str_io = io.StringIO()
    target_exprs, _ = zip(*targets)  # this is python magic to unzip...

    ln_no_to_target_exprs = defaultdict(list)
    for (target_expr, target_line) in targets:
        ln_no_to_target_exprs[target_line].append(target_expr)


    target_name_to_expr = {}
    next_id = 0
        
    # Iterate through the source line by line, inserting line-specific targets.
    for ln_no, source_line in enumerate(source.splitlines()):

        ln_no = ln_no + 1  # index from 1, not 0!

        # print(f"{source_line}\n")
        
        str_io.write(f"{source_line}\n")

        # Gotcha: make sure to use the _same indentation as the line!_
        indent_level = len(source_line) - len(source_line.lstrip())
        indent = indent_level * " "

        for target_expr in ln_no_to_target_exprs[ln_no]:
            if (ln_no == -1):
                continue

            target_name = f"__infer_target_{next_id}__"
            next_id = next_id + 1

            target_name_to_expr[target_name] = target_expr

            # print(f"\n{indent}{target_name} = {target_expr}")
            # print(f"\n{indent}reveal_type({target_name})")

            str_io.write(f"{indent}{target_name} = {target_expr}")
            str_io.write(f"\n{indent}reveal_type({target_name})\n\n")
    str_io.write("\n")

    # Insert the end-of-file targets.
    for target_expr in ln_no_to_target_exprs[-1]:

        target_name = f"__infer_target_{next_id}__"
        next_id = next_id + 1

        target_name_to_expr[target_name] = target_expr
        
        str_io.write(f"\n{target_name} = {target_expr}")
        str_io.write(f"\nreveal_type({target_name})")
    str_io.write("\n")

    # Rewind and feed the augmented script into pyright.
    str_io.seek(0)
    
    print(str_io.getvalue())
    result = pyright_run(str_io.read())
    # print(result)

    # Pull out what we want to know from the 'information's 
    pattern = r'Type of "(?P<target>\w+)" is "(?P<type>.+?)"'
    regex = re.compile(pattern)
    
    informations = {}
    inferred_types = dict.fromkeys(target_exprs)
    
    for diagnostic in result['generalDiagnostics']:
        # print(diagnostic)
        if diagnostic['severity'] == 'information':
            message = diagnostic['message']
            if (match := regex.fullmatch(message)):
                target_name = match.group("target")
                inferred_type = match.group("type")
                inferred_types[target_name_to_expr[target_name]] = inferred_type
            else:
                continue

    return inferred_types


if __name__ == "__main__":
    main()