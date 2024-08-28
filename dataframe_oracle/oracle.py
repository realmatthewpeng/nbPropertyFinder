import json
import re
import subprocess
from textwrap import dedent

def main():
    source = dedent("""
    import pandas as pd
    from sklearn.datasets import load_iris
    
    # Load Iris dataset
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    
    # Calculate mean and standard deviation for sepal length and width
    sepal_length_mean = df['sepal length (cm)'].mean()
    sepal_width_mean = df['sepal width (cm)'].mean()
    sepal_length_std = df['sepal length (cm)'].std()
    sepal_width_std = df['sepal width (cm)'].std()
    
    print(f"Sepal Length - Mean: {sepal_length_mean:.2f}, Std: {sepal_length_std:.2f}")
    print(f"Sepal Width - Mean: {sepal_width_mean:.2f}, Std: {sepal_width_std:.2f}")
    
    my_str = "foo"
    
    my_dict = {}
    my_dict[my_str] = 123

    if True:
        scoped_df = pd.DataFrame()
    """)

    writeContext(source)
    isDFExpr("    scoped_df")


def writeContext(source):
    with open('test.py', 'w') as f:
        f.write(source)


def isDFExpr(source_line):
    if (staticTypeCheck(source_line)):
        return True
    if checkNamingConventions(source_line):
        return True
    if checkDFMethodCall(source_line):
        return True

    return False


def checkDFMethodCall(source_line):
    dfMethods = ["reset_index"]
    
    for method in dfMethods:
        if method in source_line:
            print("Found DataFrame only method call.")
            return True
        
    return False


def checkNamingConventions(source_line):
    source_line = str.lower(source_line)

    if "np." in source_line or "numpy." in source_line:
        print("Found numpy in naming convention.")
        return False
    
    if "df" in source_line or "dataframe" in source_line:
        print("Found dataframe in naming convention.")
        return True
    
    return False


def staticTypeCheck(source_line: str):
    with open('test.py', 'a') as f:        
        target_name = f"__infer_target__"
        indent_level = len(source_line) - len(source_line.lstrip())
        indent = indent_level * " "

        f.write(f"{indent}{target_name} = {source_line.lstrip()}")
        f.write(f"\n{indent}reveal_type({target_name})\n\n")

    result = pyright_run_default()
    print(f"Static Type Analysis: type is {result}.")
    if "DataFrame" in result or "Series" in result:
        return True
    
    return False
    

def pyright_run_default():
    pyright_cmd_base = ['pyright', '--outputjson']
    result_json = None
    try:
        result = subprocess.run([*pyright_cmd_base, "test.py"], check=True, capture_output=True)
        result_json = json.loads(result.stdout)
    except subprocess.CalledProcessError as cpe:
        result_json = json.loads(cpe.output.decode())

    pattern = r'Type of "(?P<target>\w+)" is "(?P<type>.+?)"'
    regex = re.compile(pattern)
        
    for diagnostic in result_json['generalDiagnostics']:
        if diagnostic['severity'] == 'information':
            message = diagnostic['message']
            if (match := regex.fullmatch(message)):
                inferred_type = match.group("type")
                return inferred_type                
            else:
                continue

    return "Error"


if __name__ == "__main__":
    main()

