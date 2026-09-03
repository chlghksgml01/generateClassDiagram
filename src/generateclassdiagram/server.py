from mcp.server import MCPServer
from generateclassdiagram import emitter
from generateclassdiagram import csharp_parser
import pathlib

# MCPServer 인스턴스 생성
mcp = MCPServer("generate_class_diagram")

@mcp.tool()
async def generate_class_diagram(path: str) -> str:
    """
    C# 소스 폴더를 분석해 Mermaid classDiagram 텍스트 생성

    Args:
        path: C# 파일(.cs)들이 들어있는 폴더의 절대 경로. 하위 폴더까지 재귀적으로 탐색

    Returns:
        Mermaid classDiagram 문법 텍스트. mermaid.live 등에 붙여넣으면 다이어그램으로 렌더링됨
    """
    folder = pathlib.Path(path)
    if not folder.is_dir():
        raise ValueError(f"'{path}'는 존재하는 폴더 아님")
    
    parsed_classes = csharp_parser.parse_folder(path)
    return emitter.emit(parsed_classes)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
