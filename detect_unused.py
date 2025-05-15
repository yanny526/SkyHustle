# detect_unused.py
import os
import re

MODULES_DIR = "modules"

def list_modules():
    """Return list of module names (without .py) in modules/"""
    return [
        fname[:-3]
        for fname in os.listdir(MODULES_DIR)
        if fname.endswith(".py")
    ]

def scan_references(module_names):
    """
    Walk all .py files outside modules/,
    mark which modules are referenced via 'modules.<modname>'.
    """
    used = {m: False for m in module_names}
    pattern = re.compile(r"modules\.({})\b".format("|".join(module_names)))

    for root, dirs, files in os.walk("."):
        # skip the modules/ folder itself
        if os.path.abspath(root).startswith(os.path.abspath(MODULES_DIR)):
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            try:
                text = open(path, encoding="utf-8").read()
            except Exception:
                continue
            for match in pattern.findall(text):
                used[match] = True

    return used

if __name__ == "__main__":
    mods = list_modules()
    refs = scan_references(mods)
    unused = [m for m, referenced in refs.items() if not referenced]

    print("=== Module Usage Report ===\n")
    print("All modules:")
    for m in sorted(mods):
        print(f"  {'✓' if refs[m] else '✗'}  {m}.py")
    print("\nUnused modules:")
    for m in unused:
        print(f"  - {m}.py")
