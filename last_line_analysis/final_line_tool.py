import nbformat
import ast
import os
from operator import itemgetter
import pandas as pd

TEST_SINGLE_NB = False
NB_TEST_DIR = "notebooks/"
TEST_NB = "test.ipynb"

sample_funcs = ["head", "tail", "loc", "iloc"]
reduce_funs = ["describe", "mean", "std",
                "size", "count", "max", 
                "unique", "value_counts"]
non_pd_funcs = ["ax", "fig", "plt", "os", "joblib", "utils", "py",
                "sns", "seaborn", "rs", "iplot", "vs"]

def main():
    
    all_last_lines = []
    if (TEST_SINGLE_NB):
        nb = nbformat.read(TEST_NB, as_version=4)
        res = processNotebook(nb, TEST_NB)
        if (res is not None):
            all_last_lines.extend(res)
    else:
        for subdir, _, files in os.walk(NB_TEST_DIR):
            for file in files:
                notebook = os.path.join(subdir, file)
                nb = nbformat.read(notebook, as_version=4)
                res = processNotebook(nb, file)
                if (res is not None):
                    all_last_lines.extend(res)
    
    with open('all_last_lines_data.txt', 'w') as f:
        for line in all_last_lines:
            f.write(f"{line}\n")

    df = pd.DataFrame(all_last_lines)
    df.to_csv('all_last_lines.csv')

def processNotebook(nb, file: str):

    imported_pd = False
    source_dict = {}
    found_line_dict = {}

    cell_count = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source: str = cell['source']
            if (not imported_pd):
                if "pandas" in source:
                    imported_pd = True
            cell_id = cell_count
            try:
                tree = ast.parse(source)
                if (len(tree.body) > 0):
                    node = tree.body[-1]
                    category = "PRINT"
                    if type(node) == ast.Expr:
                        if type(node.value) == ast.Call:
                            if type(node.value.func) == ast.Attribute:
                                if type(node.value.func.value) == ast.Name:
                                    if node.value.func.value.id in non_pd_funcs:
                                        continue
                                if node.value.func.attr in sample_funcs:
                                    category = "SAMPLE"
                                if node.value.func.attr in reduce_funs:
                                    category = "REDUCTION"
                            if type(node.value.func) == ast.Name:
                                if (node.value.func.id == "print" or node.value.func.id == "display" or node.value.func.id == "show"):
                                    if type(node.value.args[0]) == ast.Call:
                                        if type(node.value.args[0].func) == ast.Attribute:
                                            if (node.value.args[0].func.attr in sample_funcs):
                                                category = "SAMPLE"
                                            if (node.value.args[0].func.attr in reduce_funs):
                                                category = "REDUCTION"
                                else:
                                    continue
                        if type(node.value) == ast.Subscript:
                            category = "SAMPLE"
                        if type(node.value) == ast.Name:
                            category = "IMPLICIT SAMPLE"
                        if type(node.value) == ast.Attribute:
                            if node.value.attr in reduce_funs:
                                category = "REDUCTION"
                    elif (type(node) == ast.FunctionDef or type(node) == ast.Import or type(node) == ast.ImportFrom
                          or type(node) == ast.If or type(node) == ast.For):
                        continue
                    else:
                        category = "NO_PRINT"
                    found_line_dict[cell_id] = (node.lineno, node.end_lineno, node.col_offset, node.end_col_offset, category)
                if TEST_SINGLE_NB:
                    print(category)
                    print(ast.dump(tree, indent=3), end="\n\n")
                    pass
            except Exception as e:
                # print(f"Error {e} in file {file}")
                continue

            source_dict[cell_id] = source

        cell_count += 1

    if (not imported_pd):
        return
    
    all_cleaned = []
    for id, source in source_dict.items():
        source_split = [line.strip() for line in source.split("\n")]
        if id in found_line_dict:
            (start_r, end_r, start_c, end_c, category) = found_line_dict[id]
            cut = source_split[start_r-1:end_r]
            if len(cut) > 1:
                cut[0] = cut[0][start_c:]
                cut[-1] = cut[-1][:end_c+1]
            else:
                cut[0] = cut[0][start_c:end_c+1]
            clean = "".join(cut)
            if (clean[-1] != ";"):
                all_cleaned.append({"category":category, "source":clean})
            else:
                all_cleaned.append({"category":"STOP_PRINT", "source":clean})


    return all_cleaned

if __name__ == "__main__":
    main()