def python314_kivy_patch():
    print("Running Kivy on Python 3.14+ detected, checking compatibility patch...")
    import os
    import importlib.util
    from pathlib import Path

    def fail_patch():
        print("Error: Failed to open Kivy's lang/parser.py file for patching.")
        print("Kivy currently has bugs that prevents it from running on Python 3.14")
        print("and above, and this file needs to be patched to run Sideband.")
        print("\nYou can patch this manually by locating the lang/parser.py file")
        print(f"and replacing:\n\n{kivy_target_1}\n\nWith:\n\n{kivy_patch_1}\n")
        os._exit(0)

    kivy_target_1 = """        if isinstance(node, (ast.JoinedStr, ast.BoolOp)):
            for n in node.values:
                if isinstance(n, ast.Str):
                    # NOTE: required for python3.6
                    yield from cls.get_names_from_expression(n.s)
                else:
                    yield from cls.get_names_from_expression(n.value)"""

    kivy_patch_1  = """        if isinstance(node, (ast.JoinedStr, ast.BoolOp)):
            for n in node.values:
                yield from cls.get_names_from_expression(n.value)"""

    spec = importlib.util.find_spec("kivy")
    if spec is None or spec.origin is None or spec.submodule_search_locations is None: fail_patch()
    contents = None

    target_path = f"{spec.submodule_search_locations[0]}/lang/parser.py"
    try:
        with open(target_path, "rb") as fh: contents = fh.read().decode("utf-8")
    except Exception as e:
        print(f"Error while reading Kivy's lang parser file: {e}")

    if not contents: fail_patch()
    contents = contents.replace("\r\n", "\n")

    if kivy_patch_1 in contents: print("Kivy already patched for Python 3.14 compatibility, continuing.")
    if kivy_target_1 in contents:
        print("Patching Kivy for Python 3.14 compatibility...")
        contents = contents.replace(kivy_target_1, kivy_patch_1)
        if not kivy_patch_1 in contents: fail_patch()
        try:
            with open(target_path, "wb") as fh:
                fh.write(contents.encode("utf-8"))
                print("Kivy successfully patched for Python 3.14 compatibility")
        
        except Exception as e:
            print(f"Error while patching Kivy: {e}")
            fail_patch()
