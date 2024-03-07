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

    - `dfTitanic["Age"].describe()`
    - `merged.head()`
    &nbsp;

  -     for arg in node.args:
            if isinstance(arg, ast.Attribute):
                if arg.attr in self.knownFuncNames:

    - `list(merged.columns)`
    - `print(X_F40K.shape, y_F40K.shape)`
    &nbsp;

- `type(node) == ast.Subscript:`
*Looking for subscripts*
  -     if isinstance(node.slice, ast.Compare):

    - `segDF[segDF["SWI_2"]>0]`
    - `teams_all[teams_all.name== 'Boise St.']`
    &nbsp;

- `type(node) == ast.Expr:`
*Looking for an expression statement*
  -     if isinstance(node.value, ast.Name):

    - `df_county_data`
    - `boston_residuals_df`
    &nbsp;

  -     if isinstance(node.value, ast.Subscript):
            if isinstance(node.value.slice, ast.List):

    - `wrong_counter_predictions[['round','seed_t','team_t','seed_o','team_o','game_result','predicted','win_pts','lose_pts']]`
    &nbsp;

  -     if isinstance(node.value, ast.Attribute):
            if node.value.attr in self.knownFuncNames:

    - `boston.columns`
    - `X_season.shape`
    &nbsp;

- `type(node) == ast.Assign:`
*Looking for an assignment statement*
  -     if isinstance(node.value, ast.Subscript):

    - `row["CANDIDATE NAME"] = row["CANDIDATE NAME (Last)"]`
    - `x = segDF["Year"]`
    &nbsp;

  -     for target in node.targets:
            if isinstance(target, ast.Subscript):
                if isinstance(target.slice, ast.Constant):
                    if (isinstance(target.slice.value, str)):

    - `row["CANDIDATE NAME"] = "UNKNOWN"`
    - `dfRow["MARGIN"] = 100`
    &nbsp;

  -     elif isinstance(target.value, ast.Attribute):
            if target.value.attr in ["loc", "iloc"]:

    - `dfNew.loc[district.index[0], \'WINPER\'] = row["GENERAL PERCENT"]`
    - `data.loc[i,'SWI_2'] = swi`
    &nbsp;
