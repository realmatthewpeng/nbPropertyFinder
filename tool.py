import nbformat
import ast
import os

class Visitor(ast.NodeVisitor):

    savedLines: set()
    knownFuncNames = ["head", "describe", "dropna", "isnull", "copy", 
                        "astype", "drop", "shape", "index", "mean", "std",
                        "quantile", "size", "rename", "count", "sort_values",
                        "loc", "iloc", "max", "tail", "columns", "fillna"]

    def __init__(self):
        super()
        self.savedLines = set()

    def visit(self, node: ast.AST):
        # print(type(node))
        #if hasattr(node, "attr"):
        #    print(node.attr, end="\n\n")

        if type(node) == ast.Call:
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in self.knownFuncNames:
                    self.savedLines.add((node.lineno, node.end_lineno))
            else:
                args = node.args
                for arg in args:
                    if isinstance(arg, ast.Attribute):
                        if arg.attr in self.knownFuncNames:
                            self.savedLines.add((node.lineno, node.end_lineno))
        elif type(node) == ast.Subscript:
            if isinstance(node.slice, ast.Compare):
                self.savedLines.add((node.lineno, node.end_lineno))
        elif type(node) == ast.Expr:
            if isinstance(node.value, ast.Name):
                self.savedLines.add((node.lineno, node.end_lineno))
            elif isinstance(node.value, ast.Subscript) and isinstance(node.value.slice, ast.List):
                self.savedLines.add((node.lineno, node.end_lineno))
            elif isinstance(node.value, ast.Attribute):
                if node.value.attr in self.knownFuncNames:
                    self.savedLines.add((node.lineno, node.end_lineno))
        elif type(node) == ast.Assign:
            if isinstance(node.value, ast.Subscript):
                self.savedLines.add((node.lineno, node.end_lineno))
            targets = node.targets
            for target in targets:
                if isinstance(target, ast.Subscript):
                    if isinstance(target.slice, ast.Constant):
                        if (isinstance(target.slice.value, str)):
                            self.savedLines.add((node.lineno, node.end_lineno))
                    elif isinstance(target.value, ast.Attribute):
                        if target.value.attr in ["loc", "iloc"]:
                            self.savedLines.add((node.lineno, node.end_lineno))
        
        self.generic_visit(node)

    def getSaved(self):
        return self.savedLines

TEST_SINGLE_NB = False

def main():

    nb_testdir = "notebooks/"
    nb_expectdir = "expected/"
    test_nb = "test.ipynb"

    if (TEST_SINGLE_NB):
        nb = nbformat.read(test_nb, as_version=nbformat.NO_CONVERT)
        processNotebook(nb, test_nb, nb_expectdir)
    else:
        for subdir, dirs, files in os.walk(nb_testdir):
            for file in files:
                notebook = os.path.join(subdir, file)
                nb = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
                processNotebook(nb, file, nb_expectdir)

def processNotebook(nb, file, nb_expectdir):
    outfile = open("output/"+file.removesuffix(".ipynb")+".txt", 'w')

    found_lines = []
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source = cell['source']
            try:
                tree = ast.parse(source)
                if TEST_SINGLE_NB: print(ast.dump(tree, indent=3), end="\n\n")
            except Exception as e:
                continue
          
            visitor = Visitor()
            visitor.visit(tree)

            lines = visitor.getSaved()
            source_split = [line.strip() for line in source.split("\n")]
            if len(lines) != 0:
                if TEST_SINGLE_NB: print(lines)
                for (start,end) in lines:
                    clean = "".join(source_split[start-1:end])
                    if TEST_SINGLE_NB: print(clean)
                    found_lines.append(clean)
                # print("")

    # for line in all_lines:
    #     print(line)
    print("Total number of lines found: " + str(len(found_lines)) + "\n", file=outfile)

    for line in found_lines:
        print(line, file=outfile)

    expected = os.path.join(nb_expectdir, file.removesuffix(".ipynb")+".txt")
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