import pathlib
import re
from generateclassdiagram.model import ParsedClass, ClassKind, AccessModifier

import tree_sitter_c_sharp as tscs
from tree_sitter import Language, Parser

CS_LANGUAGE = Language(tscs.language())
parser = Parser(CS_LANGUAGE)


def dump(n, d = 0):
    print("  " * d + n.type + (f'  {n.text.decode()!r}' if n.child_count == 0 else ""))
    for i, c in enumerate(n.children):
        f = n.field_name_for_child(i)
        if f: print("  " * (d + 1) + f"<field = {f}>")
        dump(c, d + 1)


DECL_KINDS = {
    "class_declaration": ClassKind.CLASS,
    "interface_declaration": ClassKind.INTERFACE,
    "struct_declaration": ClassKind.STRUCT,
    "enum_declaration": ClassKind.ENUM,
}

# C# 구문 트리에서 클래스, 인터페이스, 구조체, 열거형 선언 노드를 순회하며 반환하는 제너레이터 함수
def _iter_decls(node):
    for child in node.children:
        if child.type in DECL_KINDS:
            yield child
        yield from _iter_decls(child)

# C# 구문 트리에서 중첩 클래스/인터페이스/구조체/열거형의 바깥쪽 이름 찾아 반환하는 함수
def _outer_name(node):
    p = node.parent
    while p is not None:
        if p.type in DECL_KINDS:
            return p.child_by_field_name("name").text.decode()
        p = p.parent
    return None

# C# 구문 트리에서 상속받은 부모 클래스와 구현한 인터페이스 정보를 추출하는 함수
def _split_bases(node, kind):
    bn = next((c for c in node.children if c.type == "base_list"), None)
    if bn is None or kind is ClassKind.ENUM:
        return None, []
    base_class, interfaces = None, []
    for t in bn.named_children:
        text = t.text.decode()
        if re.match(r"I[A-Z]", text):
            interfaces.append(text)
        elif base_class is None:
            base_class = text
        else:
            interfaces.append(text)
    return base_class, interfaces

def _to_parsed_classs(node):
    kind = DECL_KINDS[node.type]
    name = node.child_by_field_name("name").text.decode()
    mods = [c.text.decode() for c in node.children if c.type == "modifier"]
    base_class, interfaces = _split_bases(node, kind)

    return ParsedClass(
        name = name,
        access_modifier = AccessModifier.from_keyword(" ".join(mods)),
        kind = kind,
        base_class = base_class,
        interfaces = interfaces,
        is_abstract = "abstract" in mods,
        is_static = "static" in mods,
        outer = _outer_name(node),
    )

# 폴더 내의 C# 파일 찾아서 파싱 후 클래스나 선언 정보 객체 목록으로 반환
def parse_folder(folder_path):
    results = []
    for file_path in pathlib.Path(folder_path).rglob("*.cs"):
        tree = parser.parse(file_path.read_bytes())
        for decl in _iter_decls(tree.root_node):
            results.append(_to_parsed_classs(decl))
    return results

# 테스트 코드
if __name__ == "__main__":
    folders = [
        r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor\AIBalanceReview",
        r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor",
    ]
    for f in folders:
        parsed_classes = parse_folder(f)
        # outer 및 name 기준 정렬 후 출력
        parsed_classes.sort(key=lambda c: (c.outer or "", c.name))
        print(f"=== Folder: {f} ===")
        for c in parsed_classes:
            print(c)
