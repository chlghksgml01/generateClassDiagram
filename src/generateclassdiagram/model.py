# C#파일에서 어떤 것을 뽑고싶은지 자료구조로 표현
from dataclasses import dataclass, field
from enum import Enum

class ClassKind(Enum):
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    RECORD = "record"
    ENUM = "enum"

class AccessModifier(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    @property
    def symbol(self):
        if self == AccessModifier.PUBLIC:
            return "+"
        elif self == AccessModifier.PRIVATE:
            return "-"
        elif self == AccessModifier.PROTECTED:
            return "#"
        elif self == AccessModifier.INTERNAL:
            return "~"

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
    base_class: str | None = None # 부모 클래스
    fields: list[Field] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)

@dataclass
class Relationship:
    source: str
    target: str
    kind: str  # 상속 / 구현 / 참조 / 의존 / 포함
