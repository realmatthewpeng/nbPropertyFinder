# README

## AST Tree Pattern Matching

    knownFuncNames = ["head", "describe", "dropna", "isnull", "copy", 
                        "astype", "drop", "shape", "index", "mean", "std",
                        "quantile", "size", "rename", "count", "sort_values",
                        "loc", "iloc", "max", "tail", "columns", "fillna",
                        "apply", "unique", "value_counts", "reshape", 
                        "reset_index", "replace", "drop_duplicates", "concat"]

- `type(node) == ast.Call:`
*Looking for a function call*
  -     if isinstance(node.func, ast.Attribute):
            if node.func.attr in self.knownFuncNames:
    - Example 1
    - Example 2
    &nbsp;
  -     for arg in node.args:
            if isinstance(arg, ast.Attribute):
                if arg.attr in self.knownFuncNames:

    - Example 1
    - Example 2
    &nbsp;

- `type(node) == ast.Subscript:`
*Looking for subscripts*
  -     if isinstance(node.slice, ast.Compare):

    - Example 1
    - Example 2
    &nbsp;

- `type(node) == ast.Expr:`
*Looking for an expression statement*
  -     if isinstance(node.value, ast.Name):

    - Example 1
    - Example 2
    &nbsp;

  -     if isinstance(node.value, ast.Subscript):
            if isinstance(node.value.slice, ast.List):

    - Example 1
    - Example 2
    &nbsp;

  -     if isinstance(node.value, ast.Attribute):
            if node.value.attr in self.knownFuncNames:

    - Example 1
    - Example 2
    &nbsp;

- `type(node) == ast.Assign:`
*Looking for an assignment statement*
  -     if isinstance(node.value, ast.Subscript):

    - Example 1
    - Example 2
    &nbsp;

  -     for target in node.targets:
            if isinstance(target, ast.Subscript):
                if isinstance(target.slice, ast.Constant):
                    if (isinstance(target.slice.value, str)):

    - Example 1
    - Example 2
    &nbsp;

  -     elif isinstance(target.value, ast.Attribute):
            if target.value.attr in ["loc", "iloc"]:

    - Example 1
    - Example 2
    &nbsp;
