import nbformat
import ast
import os
from operator import itemgetter
import pandas as pd

class Visitor(ast.NodeVisitor):

    savedLines: set
    # TODO: distinguish between Dataframe and Series value_counts?
    knownFuncNames = ["head", "describe", "dropna", "isnull", "copy", 
                        "astype", "drop", "shape", "index", "mean", "std",
                        "quantile", "size", "rename", "count", "sort_values",
                        "loc", "iloc", "max", "tail", "columns", "fillna",
                        "apply", "unique", "value_counts", "reshape", "reset_index", 
                        "replace", "drop_duplicates", "concat"]
    
    revealingFuncs = ["describe", "isnull",
                     "shape", "mean", "std",
                     "quantile", "size", "count",
                     "max", "unique", "value_counts"]
    
    enforcingFuncs = ["dropna", "astype", "drop", 
                      "rename", "sort_values", "fillna", "apply", 
                      "replace", "drop_duplicates", "concat"]

    def __init__(self):
        super()
        self.savedLines = set()

    def visit(self, node: ast.AST):
        if type(node) == ast.Call:
            self.visit_Call_FuncAttribute(node)
            self.visit_Call_NodeArgs(node)
        elif type(node) == ast.Subscript:
            self.visit_Subscript(node)
        elif type(node) == ast.Expr:
            self.visit_Expr_ValueName(node)
            self.visit_Expr_ValueSubscript(node)
            self.visit_Expr_ValueAttribute(node)
        elif type(node) == ast.Assign:
            self.visit_Assign_ValueSubscript(node)
            self.visit_Assign_NodeTargets(node)
        elif type(node) == ast.Delete:
            self.visit_Delete(node)

        self.generic_visit(node)

    def visit_Assign_ValueSubscript(self, node: ast.Assign):
        if isinstance(node.value, ast.Subscript):
            self.saveNode(node, "Assign1", "", "reduction")

    def visit_Assign_NodeTargets(self, node: ast.Assign):
        targets = node.targets
        for target in targets:
            if isinstance(target, ast.Subscript):
                self.visit_Assign_NodeTargetSubscript_SliceConstant(node, target)
                self.visit_Assign_NodeTargetSubscript_ValueAttribute(node, target)

    def visit_Assign_NodeTargetSubscript_SliceConstant(self, node: ast.Assign, target: ast.Subscript):
        if isinstance(target.slice, ast.Constant):
            if (isinstance(target.slice.value, str)):
                self.saveNode(node, "Assign2", "", "enforcing")

    def visit_Assign_NodeTargetSubscript_ValueAttribute(self, node: ast.Assign, target: ast.Subscript):
        if isinstance(target.value, ast.Attribute):
            if target.value.attr in ["loc", "iloc"]:
                self.saveNode(node, "Assign3", target.value.attr, "enforcing")

    def visit_Expr_ValueName(self, node: ast.Expr):
        if isinstance(node.value, ast.Name):
            self.saveNode(node, "Expr1", "", "sampling")
    
    def visit_Expr_ValueSubscript(self, node: ast.Expr):
        if isinstance(node.value, ast.Subscript): 
            if isinstance(node.value.slice, ast.List):
                self.saveNode(node, "Expr2", "", "sampling")

    def visit_Expr_ValueAttribute(self, node: ast.Expr):
        if isinstance(node.value, ast.Attribute):
            if node.value.attr in self.revealingFuncs:
                self.saveNode(node, "Expr3", node.value.attr, "revealing")

    def visit_Call_FuncAttribute(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in self.knownFuncNames:
                isReveal = "uncategorized"
                if node.func.attr in self.revealingFuncs:
                    isReveal = "revealing"
                if node.func.attr in self.enforcingFuncs:
                    isReveal = "enforcing"
                self.saveNode(node, "Call1", node.func.attr, isReveal)
    
    def visit_Call_NodeArgs(self, node: ast.Call):
        args = node.args
        for arg in args:
            if isinstance(arg, ast.Attribute):
                if arg.attr in self.knownFuncNames:
                    isReveal = "uncategorized"
                    if arg.attr in self.revealingFuncs:
                        isReveal = "revealing"
                    if arg.attr in self.enforcingFuncs:
                        isReveal = "enforcing"
                    self.saveNode(node, "Call2", arg.attr, isReveal)
    
    def visit_Subscript(self, node: ast.Subscript):
        if isinstance(node.slice, ast.Compare):
            self.saveNode(node, "Subscript1", "", "reduction")

    def visit_Delete(self, node: ast.Delete):
        if isinstance(node.targets[0], ast.Subscript):
            if isinstance(node.targets[0].slice, ast.Constant):
                self.saveNode(node, "Delete1", "", "enforcing")

    def saveNode(self, node: ast.AST, type: str, type_details="", effectType=""):
        self.savedLines.add((node.lineno, node.end_lineno, node.col_offset, node.end_col_offset, type, type_details, effectType))

    def getSaved(self):
        return self.savedLines

TEST_SINGLE_NB = False
NB_TEST_DIR = "notebooks/"
NB_EXPECTED_DIR = "expected/"
TEST_NB = "test.ipynb"

corpus_total_expected = 0
corpus_total_correct = 0
corpus_total_found = 0
all_data = []

def main():
    
    if (TEST_SINGLE_NB):
        nb = nbformat.read(TEST_NB, as_version=4)
        processNotebook(nb, TEST_NB)
    else:
        links = {}
        with open("notebook_links.txt") as f:
            for line in f:
                (notebook, link) = line.split(",")
                links[notebook] = link

        for subdir, _, files in os.walk(NB_TEST_DIR):
            for file in files:
                notebook = os.path.join(subdir, file)
                nb = nbformat.read(notebook, as_version=4)
                processNotebook(nb, file, links[file])

        precision = 0
        recall = 0
        if corpus_total_found != 0:
            precision = corpus_total_correct/corpus_total_found
        if corpus_total_expected != 0:
            recall = corpus_total_correct/corpus_total_expected
            
        print("Precision = " + str(precision))
        print("Recall = " + str(recall))

        # with open("all_data.txt", "w") as f:
        #     for x in range(len(all_data)):
        #         print(all_data[x], file=f)

        df = pd.DataFrame(all_data)
        df.to_csv('all_data.csv')

def processNotebook(nb, file: str, link: str):

    cell_dict = {}
    property_dict = {}
    flattened_data = []
    imported_pd = False

    cell_count = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source: str = cell['source']
            if (not imported_pd):
                if "pandas" in source:
                    imported_pd = True
                    # print("found pandas")
            cell_id = cell_count
            try:
                tree = ast.parse(source)
                if TEST_SINGLE_NB: print(ast.dump(tree, indent=3), end="\n\n")
            except Exception as e:
                # print(f"Error {e} in file {file}")
                continue
          
            visitor = Visitor()
            visitor.visit(tree)

            lines = visitor.getSaved()
            cell_dict[cell_id] = source
            property_dict[cell_id] = lines

        cell_count += 1

    if (not imported_pd):
        printResults({}, {}, file, False)
        return

    for id, source in cell_dict.items():
        source_split = [line for line in source.split("\n")]
        lines = property_dict[id]
        if (len(lines) != 0):
            for (start_r, end_r, start_c, end_c, type, type_details, effectType) in lines:
                new_dict = {"notebook":file,
                            "link":link,
                            "cell_id":id, 
                            "lineno":start_r, 
                            "end_lineno":end_r, 
                            "col_offset":start_c, 
                            "end_col_offset":end_c,
                            "type": type,
                            "type_details": type_details,
                            "effect_type": effectType}
                cut = source_split[start_r-1:end_r]
                if len(cut) > 1:
                    cut[0] = cut[0][start_c:]
                    cut[-1] = cut[-1][:end_c]
                else:
                    cut[0] = cut[0][start_c:end_c]
                clean = "".join(cut)
                new_dict["code"] = clean
                flattened_data.append(new_dict)
    
    flattened_data = sorted(flattened_data, key=itemgetter("cell_id", "lineno", "col_offset"))
    global all_data
    all_data.extend(flattened_data) 
    # for x in range(len(flattened_data)):
    #     print(flattened_data[x])
    printResults(cell_dict, property_dict, file)

def printResults(cell_dict: dict, property_dict: dict, file: str, has_pandas = True):

    outfile = open("output/"+file.removesuffix(".ipynb")+".txt", 'w')
    if (not has_pandas):
        print("Did not find pandas", file=outfile)
        return

    found_lines = []
    for id, source in cell_dict.items():
        source_split = [line.strip() for line in source.split("\n")]
        lines = property_dict[id]
        if len(lines) != 0:
            if TEST_SINGLE_NB: print(lines)
            seen_lines = []
            for (start,end, _, _, _, _, _) in lines:
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
    total_expected = len(expected_lines)

    num_correct = 0
    print("\nIncorrect Lines:\n", file=outfile)
    for line in found_lines:
        if line in expected_lines:
            num_correct += 1
            expected_lines.remove(line)
        else:
            print(line, file=outfile)

    precision = 0
    recall = 0
    if len(found_lines) != 0:
        precision = num_correct/len(found_lines)
    if total_expected != 0:
        recall = num_correct/total_expected
        
    print("\nPrecision = " + str(precision), file=outfile)
    print("Recall = " + str(recall) + "\n", file=outfile)

    for line in expected_lines:
        print(line, file=outfile)

    global corpus_total_expected 
    global corpus_total_correct
    global corpus_total_found
    corpus_total_expected += total_expected
    corpus_total_correct += num_correct
    corpus_total_found += len(found_lines)

if __name__ == "__main__":
    main()