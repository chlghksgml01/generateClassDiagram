from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from generateclassdiagram import emitter
from generateclassdiagram import csharp_parser
import pathlib
import os

def _allowed_roots():
    """읽어도 되는 최상위 폴더(허용 루트) 목록 결정"""
    raw = os.environ.get("GENERATECLASSDIAGRAM_ROOTS")

    if not raw:
        return [pathlib.Path.cwd().resolve()]

    roots = [
        pathlib.Path(p).expanduser().resolve()
        for p in raw.split(os.pathsep)
        if p.strip()
    ]
    roots = [r for r in roots if r.is_dir()]

    if not roots:
        raise RuntimeError(
            "GENERATECLASSDIAGRAM_ROOTS가 설정됐지만 유효한 폴더가 없습니다"
        )
    return roots

_ROOTS = _allowed_roots()

def _resolve_within_roots(path):
    """path가 허용 루트(_ROOTS) 안에 있는지 확인하고 있으면 절대 경로 반환"""
    candidate = pathlib.Path(path).expanduser().resolve()
    for root in _ROOTS:
        if candidate == root or root in candidate.parents:
            return candidate
    raise ToolError(f"'{path}'는 허용된 범위 밖임, 허용 루트: { [str(r) for r in _ROOTS] }")


mcp = MCPServer("generate_class_diagram")

@mcp.tool()
async def generate_class_diagram(path: str) -> str:
    """
    C# 소스 폴더를 분석해 Mermaid classDiagram 텍스트 생성

    Args:
        path: C# 파일(.cs)들이 들어있는 폴더의 절대 경로. 하위 폴더까지 재귀적으로 탐색, 서버가 허용한 루트 폴더 안이어야 하며 벗어나면 거부됨.

    Returns:
        Mermaid classDiagram 문법 텍스트. mermaid.live 등에 붙여넣으면 다이어그램으로 렌더링됨
    """
    folder = _resolve_within_roots(path)
    if not folder.is_dir():
        raise ToolError(f"'{path}'는 존재하는 폴더 아님")
    try:
        parsed_classes = csharp_parser.parse_folder(folder)
    except ValueError as e:
        raise ToolError(str(e))
    return emitter.emit(parsed_classes)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
