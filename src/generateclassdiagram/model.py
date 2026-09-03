# C#파일에서 어떤 것을 뽑고싶은지 자료구조로 표현
from dataclasses import dataclass, field
from enum import Enum


class ClassKind(Enum):
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"

_RELATION_SYMBOLS = {
    "INHERITANCE": "<|--",
    "REALIZATION": "<|..",
    "ASSOCIATION": "-->",
    "DEPENDENCY":  "..>",
    "COMPOSITION": "*--",
}

_ACCESS_SYMBOLS = {
    "PUBLIC": "+",
    "PRIVATE": "-",
    "PROTECTED": "#",
    "INTERNAL": "~",
}

class RelationKind(Enum):
    INHERITANCE = "inheritance"   # 상속
    REALIZATION = "realization"   # 인터페이스 구현
    ASSOCIATION = "association"   # 필드/프로퍼티로 타입 보유
    DEPENDENCY = "dependency"     # 메서드 파라미터/반환에만 등장
    COMPOSITION = "composition"   # 소유 (생성·수명 관리)

    @property
    def arrow(self):
        return _RELATION_SYMBOLS[self.name]

class AccessModifier(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"

    @property
    def symbol(self):
        return _ACCESS_SYMBOLS[self.name]

    @classmethod
    def from_keyword(cls, kw):
        if not kw:
            return cls.PRIVATE

        tokens = {t.lower() for t in kw.split()}
        access = tokens & {"public", "private", "protected", "internal"}

        if "public" in access:
            return cls.PUBLIC
        if "protected" in access:
            return cls.PROTECTED
        if "internal" in access:
            return cls.INTERNAL
        if "private" in access:
            return cls.PRIVATE
        return cls.PRIVATE


@dataclass
class Parameter:
    type: str
    name: str


@dataclass
class Field:
    name: str
    type: str
    access_modifier: AccessModifier
    is_static: bool = False
    is_readonly: bool = False
    is_const: bool = False


@dataclass
class Property:
    name: str
    type: str
    access_modifier: AccessModifier
    is_static: bool = False
    is_readonly: bool = False


@dataclass
class Method:
    name: str
    return_type: str
    access_modifier: AccessModifier
    parameters: list[Parameter] = field(default_factory=list)
    is_static: bool = False
    is_constructor: bool = False


@dataclass
class ParsedClass:
    name: str
    access_modifier: AccessModifier
    kind: ClassKind
    base_class: str | None = None                        # 부모 클래스 (상속, 최대 1개)
    interfaces: list[str] = field(default_factory=list)  # 구현하는 인터페이스 이름들
    outer: str | None = None                             # 중첩 클래스의 바깥 클래스 이름 (최상위면 None)
    is_abstract: bool = False
    is_static: bool = False
    fields: list[Field] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source: str
    target: str
    kind: RelationKind
