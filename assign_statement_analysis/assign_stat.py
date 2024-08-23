from collections import defaultdict
import nbformat
import ast
import os
from operator import itemgetter
import pandas as pd
import sys

typeinferpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'typeinference'))
sys.path.append(typeinferpath)

import typerinfer_tool as typeinfer

class Visitor(ast.NodeVisitor):

    savedLines: set

    def __init__(self):
        super()
        self.savedLines = set()

    def visit(self, node: ast.AST):
        global notebook_assigns
        if type(node) == ast.Assign:
            self.saveNode(node, "Assign", ast.unparse(node.targets[0]))
            notebook_assigns += 1
            # print(ast.unparse(node.targets[0]))
            # self.visit_Assign_ValueSubscript(node)
            # self.visit_Assign_NodeTargets(node)
        # if type(node) == ast.AugAssign:
        #     self.saveNode(node, "AugAssign", ast.unparse(node.target))
        #     all_assigns += 1

        self.generic_visit(node)

    # def visit_Assign_ValueSubscript(self, node: ast.Assign):
    #     if isinstance(node.value, ast.Subscript):
    #         self.saveNode(node, "Assign1", "", "")

    # def visit_Assign_NodeTargets(self, node: ast.Assign):
    #     targets = node.targets
    #     for target in targets:
    #         if isinstance(target, ast.Subscript):
    #             self.visit_Assign_NodeTargetSubscript_SliceConstant(node, target)
    #             self.visit_Assign_NodeTargetSubscript_ValueAttribute(node, target)

    # def visit_Assign_NodeTargetSubscript_SliceConstant(self, node: ast.Assign, target: ast.Subscript):
    #     if isinstance(target.slice, ast.Constant) and (isinstance(target.slice.value, str)):
    #             self.saveNode(node, "Assign2", "", "")

    # def visit_Assign_NodeTargetSubscript_ValueAttribute(self, node: ast.Assign, target: ast.Subscript):
    #     if isinstance(target.value, ast.Attribute):
    #         if target.value.attr in ["loc", "iloc"]:
    #             self.saveNode(node, "Assign3", target.value.attr, "")

    def saveNode(self, node: ast.Assign, type: str, lval=""):
        self.savedLines.add((node.lineno, node.end_lineno, node.col_offset, node.end_col_offset, type, lval))

    def getSaved(self):
        return self.savedLines

TEST_SINGLE_NB = False
NB_TEST_DIR = "../notebooks/"
NB_EXPECTED_DIR = "expected/"
TEST_NB = "../test.ipynb"
# TEST_NB = "../notebooks/notebook_data_profililng.ipynb"

corpus_total_expected = 0
corpus_total_correct = 0
corpus_total_found = 0
all_assigns = 0
notebook_assigns = 0
all_data = []

def main():
    
    if (TEST_SINGLE_NB):
        nb = nbformat.read(TEST_NB, as_version=4)
        processNotebook(nb, TEST_NB, "")
    else:
        links = {}
        with open("../notebook_links.txt") as f:
            for line in f:
                (notebook, link) = line.split(",")
                links[notebook] = link

        for subdir, _, files in os.walk(NB_TEST_DIR):
            for file in files:
                notebook = os.path.join(subdir, file)
                print("Processing: " + notebook)
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
        print(f"Found {corpus_total_correct} out of {all_assigns} assignment statements to be DataFrame related.")
        print(f"Found {corpus_total_expected} out of {all_assigns} assignment statements should be DataFrame related.")


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
                if TEST_SINGLE_NB: print(e)
                continue
          
            visitor = Visitor()
            visitor.visit(tree)

            lines = visitor.getSaved()
            cell_dict[cell_id] = source
            property_dict[cell_id] = lines

        cell_count += 1

    global all_assigns
    global notebook_assigns

    if (not imported_pd):
        notebook_assigns = 0
        printResults({}, {}, file, {}, False)
        return

    all_assigns += notebook_assigns
    notebook_assigns = 0

    typeinfer.clearFile()
    
    for id, source in cell_dict.items():
        source_split = [line for line in source.split("\n")]
        lines = property_dict[id]
        toTypeCheck = defaultdict(list)
        if (len(lines) != 0):
            for (start_r, end_r, start_c, end_c, type, lval) in lines:
                new_dict = {"notebook":file,
                            "link":link,
                            "cell_id":id, 
                            "lineno":start_r, 
                            "end_lineno":end_r, 
                            "col_offset":start_c, 
                            "end_col_offset":end_c,
                            "type": type,
                            "lval": lval}
                cut = source_split[start_r-1:end_r]
                if len(cut) > 1:
                    cut[0] = cut[0][start_c:]
                    cut[-1] = cut[-1][:end_c]
                else:
                    cut[0] = cut[0][start_c:end_c]
                clean = "".join(cut)
                new_dict["code"] = clean
                flattened_data.append(new_dict)
                toTypeCheck[end_r].append(lval)
        
        typeinfer.buildNotebook(source_split, toTypeCheck)

    types = typeinfer.pyright_run_default()

    printResults(cell_dict, property_dict, file, types)

def printResults(cell_dict: dict, property_dict: dict, file: str, types: dict, has_pandas = True):

    try:
        outfile = open("output/"+file.removesuffix(".ipynb")+".txt", 'w')
    except:
        print("Writing to test.txt")
        outfile = open("test.txt", 'w')

    if (not has_pandas):
        print("Did not find pandas", file=outfile)
        return

    global all_data
    found_lines = []
    for id, source in cell_dict.items():
        source_split = [line.strip() for line in source.split("\n")]
        lines = property_dict[id]
        if len(lines) != 0:
            if TEST_SINGLE_NB: print(lines)
            seen_lines = []
            for (start,end, _, _, type, lval) in lines:
                if (start,end) in seen_lines: continue
                clean = "".join(source_split[start-1:end])

                should_continue = False
                types_list = types[lval]
                for (inferred_type, lineno) in types_list:
                    if (int(lineno) < start or int(lineno) > end):
                        continue
                    if "DataFrame" in inferred_type or "Series" in inferred_type:
                        should_continue = True
                    # elif "list" in inferred_type or "dict" in inferred_type or "Literal" in inferred_type or "float" in inferred_type:
                    #     should_continue = False
                    # elif "Any" != inferred_type and "Unknown" != inferred_type:
                    #     print(inferred_type, file=outfile)
                    #     should_continue = True

                if (not should_continue):
                    continue

                seen_lines.append((start,end))
                if TEST_SINGLE_NB: print(clean)
                found_lines.append(clean)
                all_data.append(clean)


    print("Total number of lines found: " + str(len(found_lines)) + "\n", file=outfile)

    for line in found_lines:
        print(line, file=outfile)

    try:
        expected = os.path.join(NB_EXPECTED_DIR, file.removesuffix(".ipynb")+".txt")
        expected_lines = []
        with open(expected) as f:
            expected_lines = f.read().splitlines()
    except:
        return
    
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