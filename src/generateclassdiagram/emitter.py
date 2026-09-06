from generateclassdiagram.model import ParsedClass, ClassKind

_GENERIC = str.maketrans({"<": "~", ">": "~"})

def _safe(name: str) -> str:
    return name.translate(_GENERIC)

_KIND_MARK = {
    ClassKind.INTERFACE: "interface",
    ClassKind.STRUCT: "struct",
    ClassKind.ENUM: "enumeration",
}

def _mark(c: ParsedClass) -> str | None:
    """이 클래스에 붙일 << >> 표시 하나, 없으면 None(kind가 우선, 그다음 abstract, static)"""
    if c.kind in _KIND_MARK:
        return _KIND_MARK[c.kind]
    if c.is_abstract:
        return "abstract"
    if c.is_static:
        return "static"
    return None

def _member_lines(c: ParsedClass) -> list[str]:
    """필드, 프로퍼티를 '<symbol><type> <name>' 멤버 줄로, static이면 끝에 $"""
    lines = []
    for f in c.fields:
        s = f"        {f.access_modifier.symbol}{_safe(f.type)} {f.name}"
        if f.is_static:
            s += "$"
        lines.append(s)
    for p in c.properties:
        s = f"        {p.access_modifier.symbol}{_safe(p.type)} {p.name}"
        if p.is_static:
            s += "$"
        lines.append(s)
    return lines


def _declaration_lines(c: ParsedClass) -> list[str]:
    """class 선언. << >> 표시나 멤버가 있으면 블록 형태({ }), 둘 다 없으면 한 줄"""
    name = _safe(c.name)
    mark = _mark(c)
    members = _member_lines(c)

    if mark is None and not members:
        return [f"    class {name}"]

    body = []
    if mark is not None:
        body.append(f"        <<{mark}>>")
    body += members
    return [f"    class {name} {{", *body, "    }"]


def _relation_lines(c: ParsedClass) -> list[str]:
    """이 클래스가 만드는 관계 줄, 값 없으면 안 만듦"""
    name = _safe(c.name)
    lines = []
    if c.base_class:
        lines.append(f"    {_safe(c.base_class)} <|-- {name}")     # 상속
    for iface in c.interfaces:
        lines.append(f"    {_safe(iface)} <|.. {name}")            # 구현
    if c.outer:
        lines.append(f"    {_safe(c.outer)} *-- {name}")           # 중첩
    return lines


def emit(classes: list[ParsedClass]) -> str:
    """파서가 뽑은 클래스 목록을 Mermaid classDiagram 텍스트로 변환"""
    classes = sorted(classes, key = lambda c: (c.outer or "", c.name))
    lines = ["classDiagram"]

    seen = set()
    for c in classes:
        name = _safe(c.name)
        if name in seen:
            continue
        seen.add(name)
        lines += _declaration_lines(c)

    rel = []
    for c in classes:
        rel += _relation_lines(c)
    lines += list(dict.fromkeys(rel))

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    from generateclassdiagram.csharp_parser import parse_folder

    folder = r"C:\UnityProjects\BlockPuzzle\Assets\1.Scripts\Editor\AIBalanceReview"
    print(emit(parse_folder(folder)))
