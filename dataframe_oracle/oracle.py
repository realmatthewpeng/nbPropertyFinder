import ast
from collections import defaultdict
from typing import Callable, Literal, NamedTuple, Tuple, TypeAlias

import nbformat

def main():
    flatten_notebook(nbformat.read("test.ipynb", as_version=4))


# We need to take a notebook (array of cells) and get:
# 1. A flat python file (which we can modify, feed to pyright, etc)
# 2. A means of translating back (flat_line_no -> (cell_id, cell_line_no))
def flatten_notebook(nb: nbformat.NotebookNode):

    cell_count = 0
    flat_lineno = 0
    statement_source_to_info = defaultdict(list[tuple[int,int,int]])
    typecheck_file = open("test.py", "w")

    for cell in nb["cells"]:
        if cell["cell_type"] == "code":

            cell_source: str = cell['source']

            try:
                cell_tree = ast.parse(cell_source)
                cell_statement_count = 0

                for statement in cell_tree.body:
                    start_r = statement.lineno
                    end_r = statement.end_lineno
                    start_c = statement.col_offset
                    end_c = statement.end_col_offset

                    total_lines = start_r - end_r + 1

                    source_split = [line for line in cell_source.split("\n")]
                    cut = source_split[start_r-1:end_r]
                    if len(cut) > 1:
                        cut[0] = cut[0][start_c:]
                        cut[-1] = cut[-1][:end_c]
                    else:
                        cut[0] = cut[0][start_c:end_c]
                    statement_source = "\n".join(cut)

                    typecheck_file.write(statement_source + "\n")

                    statement_source_to_info[statement_source].append((flat_lineno, cell_count, cell_statement_count))
                    cell_statement_count += 1
                    flat_lineno += total_lines

            except Exception as e:
                print(e)
                continue

        cell_count += 1

    typecheck_file.close()
    print(f"Processed {cell_count} cells.")
    # print(statement_to_info)

    return statement_source_to_info


# # Don't actually have to use, just for clarity/readability
# # class NotebookCell(NamedTuple):
# #     id: str
# #     source: str

# type CellId = str
# type NotebookCells = list[tuple[CellId, str]]

# class SrcSpan(NamedTuple):
#     ln_start: int
#     ln_end: int
#     col_start: int
#     col_end: int

# # Scan notebook for any assignments
# # Insert reveal types for all above
# # Return dict[str, dict[Span, Literal['frame', 'series', 'other']]
# # name -> span -> type
# # Use for df method call 
# type VarName = str
# type VarAssignmentTypeIndex = dict[VarName, dict[SrcSpan, TypecheckResult]]
# type TypecheckResult = Literal['frame', 'series', 'other']
# def index_var_assignment_types(flat_nb_source: str) -> VarAssignmentTypeIndex:
#     # Get a TypecheckResult for every statement `<var_name> = <some_expr>`
#     # Record <var_name> -> (<span of this assignment> -> result)

#     # 1   | df = None
#     # 2   | x = "hello world"
#     # ... |
#     # 8   | df = pd.DataFrame(some_stuff)

#     # -> {
#     #   "df": {
#     #        SrcSpan(1, 1, 1, 10): "other",
#     #        SrcSpan(8, 8, 1, 20): "frame"
#     #    },
#     #   "x": {
#     #       SrcSpan(2, 2, 1, 15): "other"
#     #   }
#     # }

#     pass

# # d = variable_to_span_to_typecheck_result = index_top_level_variables(...)
# # span_to_typecheck_result = { 
# #     span: result 
# #     for span, result in span_to_result.items() 
# #     for span_to_result in d.values()
# # }
# # 
# # varname_to_typecheck_result = {
# #     varname: result   <- something will get overwritten here if a var is reassigned!
# #     for _, result in span_to_result.items()
# #     for varname, span_to_result in d.values()
# # }

# # Take entire source code, and expression's span (line start, end, col start, end)
# def isDFExpr(src: str, expr_span: SrcSpan, index: VarAssignmentTypeIndex): # pass in the index?

#     # Assert span from source can be parsed as expression
#     # Use temporary file
#     # typeCheckAsDataframe
#     if (staticTypeCheck(src, expr_span)):
#         # needs: whole source
#         return True
#     if checkDFMethodCall(expr_span, index):  # is this a df expr? -> is it called on a df 
#         # needs: variable name -> span (assignment) -> type index
#         # find the most recent typed assignment of the receiver of the method call
#         # was it DF or series? 

#         # I see df.foo()
#         # Look up df in index, find most recent before this mehtod call
#         # Was df a frame (or series?) at that point?
#         return True
#     if checkNamingConventions(expr_span):
#         # needs: just relevant expr/span
#         return True
#     # if isDfOnlyMethodCall(...)
#     # very unlikely something isn't a dataframe if e.g. pivot or select is called on it 

#     return False


# def checkDFMethodCall(source_line: str):
#     dfMethods = ["reset_index", "describe", "sort_values", "head", "tail", "loc", "iloc"]
    
#     for method in dfMethods:
#         if method in source_line:
#             print("Found DataFrame only method call.")
#             return True
        
#     return False


# def checkNamingConventions(source_line: str):
#     source_line = str.lower(source_line)

#     if "np." in source_line or "numpy." in source_line:
#         print("Found numpy in naming convention.")
#         return False
    
#     if "df" in source_line or "dataframe" in source_line:
#         print("Found dataframe in naming convention.")
#         return True
    
#     return False


# def staticTypeCheck(source_line: str):
#     with open('test.py', 'a') as f:        
#         target_name = f"__infer_target__"
#         indent_level = len(source_line) - len(source_line.lstrip())
#         indent = indent_level * " "

#         f.write(f"{indent}{target_name} = {source_line.lstrip()}")
#         f.write(f"\n{indent}reveal_type({target_name})\n\n")

#     result = pyright_run_default()
#     print(f"Static Type Analysis: type is {result}.")
#     if "DataFrame" in result or "Series" in result:
#         return True
    
#     return False
    

# def pyright_run_default():
#     pyright_cmd_base = ['pyright', '--outputjson']
#     result_json = None
#     try:
#         result = subprocess.run([*pyright_cmd_base, "test.py"], check=True, capture_output=True)
#         result_json = json.loads(result.stdout)
#     except subprocess.CalledProcessError as cpe:
#         result_json = json.loads(cpe.output.decode())

#     pattern = r'Type of "(?P<target>\w+)" is "(?P<type>.+?)"'
#     regex = re.compile(pattern)
        
#     for diagnostic in result_json['generalDiagnostics']:
#         if diagnostic['severity'] == 'information':
#             message = diagnostic['message']
#             if (match := regex.fullmatch(message)):
#                 inferred_type = match.group("type")
#                 return inferred_type                
#             else:
#                 continue

#     return "Error"


if __name__ == "__main__":
    main()

