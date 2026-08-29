import pathlib
import re
from generateclassdiagram.model import ParsedClass, ClassKind, AccessModifier

CLASS_RE = re.compile(r'\b(class|interface|struct|enum)\s+(\w+)')

def parse_folder(folder_path):
    results = []
    file_paths = list(pathlib.Path(folder_path).rglob("*.cs"))
    for file_path in file_paths:
        text = file_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = CLASS_RE.search(line)
            if match:                
                parsed = ParsedClass(
                    name = match.group(2),
                    access_modifier = AccessModifier.PRIVATE,
                    kind = ClassKind(match.group(1)),
                )
                results.append(parsed)
    return results

# 테스트 코드
if __name__ == "__main__":
    classes = parse_folder(r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor\AIBalanceReview")
    for c in classes:
        print(c)
    print(f"총 {len(classes)}개")
