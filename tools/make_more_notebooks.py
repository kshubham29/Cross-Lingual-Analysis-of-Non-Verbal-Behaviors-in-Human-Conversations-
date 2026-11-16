"""Writes notebooks for the remaining steps (04, 06-13, 18, 21-23, 25, 27) into notebooks/.
Each notebook uses the script's own code from src/, split into short cells; the note above
each cell comes from the script's comments. Running a notebook does exactly what the script
does (including saving its results to reports/).
Run from the project folder: python tools/make_more_notebooks.py"""
import ast
import os
import re
import nbformat as nbf

STEPS = ["04", "06", "07", "08", "09", "10", "11", "12", "13", "18", "21", "22", "23", "25", "27"]
DATASET = open("tools/make_notebooks.py", encoding="utf-8").read().split('DATASET = """')[1].split('"""')[0]

SETUP = '''import os, sys
if os.getcwd().endswith("notebooks"):
    os.chdir("..")              # work from the project folder, like the scripts
sys.path.insert(0, "src")       # so helper files in src/ (e.g. splits.py) can be imported'''


def comment_block(lines, start):
    """Comment lines directly above line index `start` (0-based), as plain text."""
    out, i = [], start - 1
    while i >= 0 and lines[i].strip().startswith("#"):
        out.insert(0, lines[i].strip().lstrip("#").strip())
        i -= 1
    out = [l for l in out if l and not set(l) <= set("-=")]
    out = [re.sub(r"^BLOCK \d+\s*-\s*", "", l) for l in out]
    return " ".join(out), i + 1


def default_note(node, src):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "Imports and settings."
    if isinstance(node, ast.FunctionDef):
        doc = ast.get_docstring(node)
        return f"Function `{node.name}`" + (f": {doc.splitlines()[0]}" if doc else ".")
    if isinstance(node, ast.ClassDef):
        return f"Class `{node.name}`."
    if isinstance(node, (ast.For, ast.While)):
        return "Main loop."
    if isinstance(node, ast.If):
        return "Run the step." if "__main__" in ast.get_source_segment(src, node.test) else "Check."
    return None


def convert(path):
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    tree = ast.parse(src)
    body = tree.body
    doc = ast.get_docstring(tree) or ""
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]

    # group top-level statements: defs, classes and loops get their own cell; the rest is grouped
    groups, cur = [], []
    for node in body:
        own = isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.If, ast.With))
        note, _ = comment_block(lines, node.lineno - 1 - (len(node.decorator_list) if hasattr(node, "decorator_list") else 0))
        if own or (note and cur):
            if cur:
                groups.append(cur)
            cur = []
        cur.append(node)
        if own:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    cells = []
    for g in groups:
        first, last = g[0], g[-1]
        start = first.lineno - 1
        note, cstart = comment_block(lines, start)
        end = last.end_lineno
        code = "\n".join(lines[start:end]).strip("\n")
        if not note:
            note = default_note(first, src) or ""
        if not note:
            if "read_parquet" in code or "np.load" in code:
                note = "Load the data."
            elif "to_csv" in code or "savefig" in code or ".save(" in code:
                note = "Print and save the results."
            elif "print(" in code:
                note = "Show the results."
            else:
                note = "Set up for the next step."
        cells.append((note, code))

    name = os.path.splitext(os.path.basename(path))[0]
    title_lines = [l.strip() for l in doc.splitlines() if l.strip()]
    title = title_lines[0] if title_lines else name
    rest = "\n".join(title_lines[1:])
    return name, title, rest, cells


for step in STEPS:
    path = next(os.path.join("src", f) for f in os.listdir("src") if f.startswith(step + "_") and f.endswith(".py"))
    name, title, rest, cells = convert(path)
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_markdown_cell(f"# {title}\n{rest}\n\n*Notebook version of `src/{name}.py`: same code, "
                                             f"split into cells. Running it does exactly what the script does.*"))
    nb.cells.append(nbf.v4.new_markdown_cell(DATASET))
    nb.cells.append(nbf.v4.new_markdown_cell("Go to the project folder."))
    nb.cells.append(nbf.v4.new_code_cell(SETUP))
    for note, code in cells:
        if note:
            nb.cells.append(nbf.v4.new_markdown_cell(note))
        nb.cells.append(nbf.v4.new_code_cell(code))
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, os.path.join("notebooks", name + ".ipynb"))
    print(f"wrote {name}.ipynb  ({len(cells)} code cells)")
