import nbformat
import ast
import os
from operator import itemgetter

class Visitor(ast.NodeVisitor):

    savedLines: set
    knownFuncNames = ["head", "describe", "dropna", "isnull", "copy", 
                        "astype", "drop", "shape", "index", "mean", "std",
                        "quantile", "size", "rename", "count", "sort_values",
                        "loc", "iloc", "max", "tail", "columns", "fillna",
                        "apply"]

    def __init__(self):
        super()
        self.savedLines = set()

    def visit(self, node: ast.AST):
        if type(node) == ast.Call:
            self.visit_Call(node)
        elif type(node) == ast.Subscript:
            self.visit_Subscript(node)
        elif type(node) == ast.Expr:
            self.visit_Expr(node)
        elif type(node) == ast.Assign:
            self.visit_Assign(node)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Subscript):
            self.saveNode(node)
        targets = node.targets
        for target in targets:
            if isinstance(target, ast.Subscript):
                if isinstance(target.slice, ast.Constant):
                    if (isinstance(target.slice.value, str)):
                        self.saveNode(node)
                elif isinstance(target.value, ast.Attribute):
                    if target.value.attr in ["loc", "iloc"]:
                        self.saveNode(node)

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Name):
            self.saveNode(node)
        elif isinstance(node.value, ast.Subscript) and isinstance(node.value.slice, ast.List):
            self.saveNode(node)
        elif isinstance(node.value, ast.Attribute):
            if node.value.attr in self.knownFuncNames:
                self.saveNode(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in self.knownFuncNames:
                self.saveNode(node)
        else:
            args = node.args
            for arg in args:
                if isinstance(arg, ast.Attribute):
                    if arg.attr in self.knownFuncNames:
                        self.saveNode(node)
    
    def visit_Subscript(self, node: ast.Subscript):
        if isinstance(node.slice, ast.Compare):
            self.saveNode(node)

    def saveNode(self, node: ast.AST):
        self.savedLines.add((node.lineno, node.end_lineno, node.col_offset, node.end_col_offset))

    def getSaved(self):
        return self.savedLines

TEST_SINGLE_NB = False
NB_TEST_DIR = "notebooks/"
NB_EXPECTED_DIR = "expected/"
TEST_NB = "test.ipynb"

def main():
    if (TEST_SINGLE_NB):
        nb = nbformat.read(TEST_NB, as_version=nbformat.NO_CONVERT)
        processNotebook(nb, TEST_NB)
    else:
        for subdir, _, files in os.walk(NB_TEST_DIR):
            for file in files:
                notebook = os.path.join(subdir, file)
                nb = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
                processNotebook(nb, file)

def processNotebook(nb, file: str):

    cell_dict = {}
    property_dict = {}
    flattened_data = []

    cell_count = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source: str = cell['source']
            cell_id = cell_count
            try:
                tree = ast.parse(source)
                if TEST_SINGLE_NB: print(ast.dump(tree, indent=3), end="\n\n")
            except Exception as e:
                continue
          
            visitor = Visitor()
            visitor.visit(tree)

            lines = visitor.getSaved()
            cell_dict[cell_id] = source
            property_dict[cell_id] = lines

        cell_count += 1

    for id, source in cell_dict.items():
        source_split = [line for line in source.split("\n")]
        lines = property_dict[id]
        if (len(lines) != 0):
            for (start_r, end_r, start_c, end_c) in lines:
                new_dict = {"cell_id":id, 
                            "lineno":start_r, 
                            "end_lineno":end_r, 
                            "col_offset":start_c, 
                            "end_col_offset":end_c}
                cut = source_split[start_r-1:end_r]
                cut[0] = cut[0][start_c:]
                cut[-1] = cut[-1][:end_c]
                clean = "".join(cut)
                new_dict["code"] = clean
                flattened_data.append(new_dict)
    
    # flattened_data = sorted(flattened_data, key=itemgetter("cell_id", "lineno", "col_offset"))
    # for x in range(len(flattened_data)):
    #     print(flattened_data[x])
    printResults(cell_dict, property_dict, file)


def printResults(cell_dict: dict, property_dict: dict, file: str):

    outfile = open("output/"+file.removesuffix(".ipynb")+".txt", 'w')

    found_lines = []
    for id, source in cell_dict.items():
        source_split = [line.strip() for line in source.split("\n")]
        lines = property_dict[id]
        if len(lines) != 0:
            if TEST_SINGLE_NB: print(lines)
            seen_lines = []
            for (start,end, _, _) in lines:
                if (start,end) in seen_lines: continue
                seen_lines.append((start,end))
                clean = "".join(source_split[start-1:end])
                if TEST_SINGLE_NB: print(clean)
                found_lines.append(clean)

    print("Total number of lines found: " + str(len(found_lines)) + "\n", file=outfile)

    for line in found_lines:
        print(line, file=outfile)

    expected = os.path.join(NB_EXPECTED_DIR, file.removesuffix(".ipynb")+".txt")
    expected_lines = []
    with open(expected) as f:
        expected_lines = f.read().splitlines()
    total_correct = len(expected_lines)

    num_correct = 0
    print("\nIncorrect Lines:\n", file=outfile)
    for line in found_lines:
        if line in expected_lines:
            num_correct += 1
            expected_lines.remove(line)
        else:
            print(line, file=outfile)

    print("\nPrecision = " + str(num_correct/len(found_lines)), file=outfile)
    print("Recall = " + str(num_correct/total_correct) + "\n", file=outfile)

    for line in expected_lines:
        print(line, file=outfile)


if __name__ == "__main__":
    main()