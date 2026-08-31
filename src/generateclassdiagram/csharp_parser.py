import pathlib
import re
from generateclassdiagram.model import ParsedClass, ClassKind, AccessModifier

import tree_sitter_c_sharp as tscs
from tree_sitter import Language, Parser

CS_LANGUAGE = Language(tscs.language())
parser = Parser(CS_LANGUAGE)

CLASS_RE = re.compile(r'\b(class|interface|struct|enum)\s+(\w+)')
# 상속 / interface 나타내려면 class 이름 뒤에 : 를 찾아내야함
def parse_folder(folder_path):
    results = []
    file_paths = list(pathlib.Path(folder_path).rglob("*.cs"))
    for file_path in file_paths:
        text = file_path.read_text(encoding="utf-8")
        current_top_class = None
        for line in text.splitlines():
            match = CLASS_RE.search(line)
            if match:
                is_nested = bool(line) and line[0].isspace()
                outer = current_top_class if is_nested else None
                base_class = None
                interfaces = []
                after = line[match.end():].split("{", 1)[0].split(" where ", 1)[0].strip()
                if after.startswith(":"):
                    parts = [p.strip() for p in after[1:].split(",") if p.strip()]
                else:
                    parts = [] 
                for parent in parts:
                    if re.match(r'I[A-Z]', parent):
                        interfaces.append(parent)
                    elif base_class is None:
                        base_class = parent
                    else:
                        interfaces.append(parent) 

                modifiers = line[:match.start()].strip()
                mod_tokens = modifiers.split()

                parsed = ParsedClass(
                    name = match.group(2),
                    access_modifier = AccessModifier.from_keyword(modifiers),
                    kind = ClassKind(match.group(1)),
                    base_class = base_class,
                    interfaces = interfaces,
                    is_abstract = "abstract" in mod_tokens,
                    is_static = "static" in mod_tokens,
                    outer = outer,
                )
                results.append(parsed)

                if not is_nested:
                    current_top_class = match.group(2)

    return results

def dump(n, d = 0):
    print("  " * d + n.type + (f'  {n.text.decode()!r}' if n.child_count == 0 else ""))
    for i, c in enumerate(n.children):
        f = n.field_name_for_child(i)
        if f: print("  " * (d + 1) + f"<field = {f}>")
        dump(c, d + 1)

# 테스트 코드
if __name__ == "__main__":
    src = pathlib.Path(r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor\AIBalanceReview\MissionSummaryExtractor.cs")
    tree = parser.parse(src.read_bytes())
    dump(tree.root_node)

