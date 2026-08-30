import pathlib
import re
from generateclassdiagram.model import ParsedClass, ClassKind, AccessModifier

CLASS_RE = re.compile(r'\b(class|interface|struct|enum)\s+(\w+)')
# 상속 / interface 나타내려면 class 이름 뒤에 : 를 찾아내야함
def parse_folder(folder_path):
    results = []
    file_paths = list(pathlib.Path(folder_path).rglob("*.cs"))
    for file_path in file_paths:
        text = file_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = CLASS_RE.search(line)
            if match:
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
                )
                results.append(parsed)
    return results

# 테스트 코드
if __name__ == "__main__":
    classes = parse_folder(r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor\AIBalanceReview")
    for c in classes:
        print(c)
    print(f"총 {len(classes)}개")
