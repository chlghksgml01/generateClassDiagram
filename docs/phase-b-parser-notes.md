# Phase B — 파서 심화 작업 노트

Phase A(수직 슬라이스) 완료 후 진행. 파이프라인은 이미 돌므로 `ParsedClass`에 데이터를
더 채우면 emitter가 자동으로 더 풍부한 다이어그램을 낸다. 우선순위 순.

관련: 플랜 파일 `~/.claude/plans/indexed-jumping-forest.md` (Phase A), 로드맵 `C:\AI-Tooling-Study\_private\Plan.md`

---

## B-1. 필드 + 프로퍼티 (`csharp_parser.py` 내부, `parse_folder` 시그니처 불변)

### tree-sitter 트리 읽는 법

| 코드 | 의미 |
|---|---|
| `node.type` | 노드 종류 문자열 |
| `node.children` / `node.named_children` | 자식 노드 (후자는 구두점 제외) |
| `node.child_by_field_name("name")` | 필드 이름으로 자식 하나 꺼내기 |
| `node.text.decode()` | 그 노드가 덮는 원본 소스 구간 문자열 |

`dump` 출력의 `<field = name>` 줄 = 다음 자식이 "name" 필드 → `child_by_field_name("name")`으로 접근.
**핵심**: 타입이 트리에서 잘게 쪼개져 있어도(`generic_name` → `identifier` + `type_argument_list`)
부모에서 `.text.decode()` 하면 `"List<GemTargetDto>"` 통째로 나온다. 재조립 불필요.

### 필드 — 실측 트리

```csharp
public sealed class ClassicSimConfig {
    public int BoardSize = 9;
    private readonly List<GemTargetDto> _targets;
}
```
```
class_declaration
  <field = body>
  declaration_list
    field_declaration                      ← "public int BoardSize = 9;"
      modifier  'public'
      variable_declaration
        <field = type>
        predefined_type  'int'
        variable_declarator
          <field = name>
          identifier  'BoardSize'
          integer_literal  '9'             ← 초기값, 안 씀
    field_declaration                      ← "private readonly List<GemTargetDto> _targets;"
      modifier  'private'
      modifier  'readonly'
      variable_declaration
        <field = type>
        generic_name  'List<GemTargetDto>'
        variable_declarator
          <field = name>
          identifier  '_targets'
```

| `model.Field` 필드 | 트리 위치 |
|---|---|
| `name` | `variable_declarator` → `child_by_field_name("name")` → `.text.decode()` |
| `type` | `variable_declaration` → `child_by_field_name("type")` → `.text.decode()` |
| `access_modifier` | `field_declaration`의 `modifier` 자식들 → `AccessModifier.from_keyword(" ".join(mods))` |
| `is_static` / `is_readonly` / `is_const` | `"static"` / `"readonly"` / `"const" in mods` |

**주의 — `field_declaration` 하나에 필드 여러 개일 수 있음**: `public int a, b, c;` 는
`field_declaration` 1개 안에 `variable_declarator` 3개. 타입/수식어 공유, 이름만 다름.
→ `variable_declarator` 개수만큼 `Field` 생성.

### 프로퍼티 — 실측 트리

```csharp
public int Score { get; private set; }
private Sprite[] BlockSprites => _palette != null ? _palette.sprites : null;
```
```
property_declaration                       ← "{ get; private set; }"
  modifier  'public'
  <field = type>
  predefined_type  'int'
  <field = name>
  identifier  'Score'
  <field = accessors>
  accessor_list
    accessor_declaration → <field = name> get 'get'
    accessor_declaration → modifier 'private', <field = name> set 'set'
property_declaration                        ← "=> ..."
  modifier  'private'
  <field = type>
  array_type  'Sprite[]'
  <field = name>
  identifier  'BlockSprites'
  <field = value>
  arrow_expression_clause
```
(`{ get; }` 만 있으면 `accessor_declaration` 이 `get` 하나. `{ get; init; }` 이면 `get` + `init`.)

| `model.Property` 필드 | 트리 위치 |
|---|---|
| `name` | `property_declaration` → `child_by_field_name("name")` → `.text.decode()` |
| `type` | `property_declaration` → `child_by_field_name("type")` → `.text.decode()` |
| `access_modifier` | `modifier` 자식들 → `from_keyword` (필드와 동일) |
| `is_static` | `"static" in mods` |
| `is_readonly` | 아래 규칙 |

**`is_readonly` 판정**:
1. `pd.child_by_field_name("value")` 가 not None (`arrow_expression_clause`) → `=> ...` 식 본문이므로 True
2. 아니면 `accessors = pd.child_by_field_name("accessors")`(`accessor_list`)의
   `accessor_declaration` 자식들을 순회 → 각 `acc.child_by_field_name("name").text.decode()` 가
   `"set"` 또는 `"init"` 인 게 하나도 없으면 True. (`{ get; private set; }` 는 `name`이 여전히 `set` → False)

### 구현 헬퍼 (csharp_parser.py에 추가)

- `_member_mods(node)` → `[c.text.decode() for c in node.children if c.type == "modifier"]`
  (`_to_parsed_classs`의 인라인 `mods` 줄도 이걸로 교체)
- `_iter_fields(decl_node) -> list[Field]` / `_iter_properties(decl_node) -> list[Property]`:
  `body = decl_node.child_by_field_name("body")`; `None`이면 `[]`. `body.named_children` 중
  `field_declaration` / `property_declaration` 만 필터 후 위 표대로 매핑.
- `_to_parsed_classs`에서 `fields = _iter_fields(node)`, `properties = _iter_properties(node)` 연결.

### 엣지
- 인터페이스: 필드 없음, 프로퍼티는 동일 노드 타입 → 그대로 처리됨
- `enum_member_declaration` 은 `field_declaration` 아님 → 자동 스킵 (의도됨)
- 중첩 DTO의 필드도 `_iter_decls`가 각 선언을 개별 반환하므로 각자 채워짐

### emitter 확장
`class Foo { }` 블록 안에 `        +int BoardSize` (접근제어자 `symbol` + 타입 + 이름),
프로퍼티도 동일. 타입 문자열의 `<`, `>` 는 Mermaid에서 `~T~` 제네릭 표기로 치환 필요:
`List<GemTargetDto>` → `List~GemTargetDto~`.

---

## B-2. 메서드 + 파라미터

`method_declaration`(`<field=returns>` + `<field=name>` + `<field=parameters> parameter_list` →
`parameter` → `<field=type>` / `<field=name>`), 생성자(`constructor_declaration`), `=>` 식 본문.
`model.Method` / `Parameter` 채우기. emitter에 `+DoThing(int x) bool` 형태 추가.

---

## B-3. `relationships.py` — 관계 5종

`model.RelationKind`: 상속/구현(이미 emitter가 base_class·interfaces로 처리) +
연관(필드/프로퍼티 타입이 파싱 대상 클래스) / 의존(메서드 파라미터·반환에만 등장) /
포함(생성·수명 관리 — 판정 어려우면 연관으로). `list[Relationship]` 산출 후 emitter가 화살표로.

최종 목표 형태: `C:\UnityProjects\BlockPuzzle\docs\diagrams\ai-balance-review.md` 의 손으로 쓴
classDiagram (멤버 `+`/`-`/`#`, `$` static, 라벨 붙은 association/dependency 화살표).

---

## B-4. 마무리

실제 81개 파일 왕복 디버깅 + pytest 픽스처 + README + 데모 스크린샷.
