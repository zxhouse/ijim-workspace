"""Build the submission package from ../manuscript.tex.

Figures are renamed Figure_<n>.pdf in order of first appearance, the
reference list is inlined, and two versions are written: with authors
(\\anonfalse) and anonymised (\\anontrue).  Both are compiled with pdflatex.
"""
import glob
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)


def main():
    src = open(os.path.join(PAPER, "manuscript.tex")).read()
    refs = open(os.path.join(PAPER, "refs.tex")).read()
    for f in glob.glob(os.path.join(HERE, "Figure_*.pdf")):
        os.remove(f)
    order = []
    for m in re.finditer(r"\\includegraphics(\[[^\]]*\])?\{(figures/[^}]+\.pdf)\}", src):
        if m.group(2) not in order:
            order.append(m.group(2))
    mapping = {path: f"Figure_{k}.pdf" for k, path in enumerate(order, 1)}
    for path, new in mapping.items():
        shutil.copy(os.path.join(PAPER, path), os.path.join(HERE, new))
        src = src.replace("{" + path + "}", "{" + new + "}")
    src = src.replace("\\input{refs.tex}", refs.strip())
    with open(os.path.join(HERE, "figure_map.txt"), "w") as f:
        for path, new in mapping.items():
            f.write(f"{new}  <-  paper/{path}\n")
    versions = {"Manuscript_with_authors": "\\anonfalse", "Manuscript_anonymised": "\\anontrue"}
    for name, flag in versions.items():
        txt = re.sub(r"^\\anon(true|false)$", lambda _: flag, src, count=1, flags=re.M)
        with open(os.path.join(HERE, name + ".tex"), "w") as f:
            f.write(txt)
        for _ in range(3):
            subprocess.run(["pdflatex", "-interaction=batchmode", name + ".tex"], cwd=HERE,
                           stdout=subprocess.DEVNULL, timeout=600)
        log = open(os.path.join(HERE, name + ".log"), errors="replace").read()
        und = len(re.findall(r"undefined", log))
        over = len(re.findall(r"Overfull", log))
        print(f"{name}: {len(mapping)} figures, {und} undefined, {over} overfull")
    for ext in ("aux", "log", "out", "spl"):
        for f in glob.glob(os.path.join(HERE, "*." + ext)):
            os.remove(f)


if __name__ == "__main__":
    main()
