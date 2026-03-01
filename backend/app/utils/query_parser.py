"""布尔查询解析器（P2）。"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class QueryParser:
    _ops = {"AND", "OR", "NOT"}
    _precedence = {"NOT": 3, "AND": 2, "OR": 1}

    def _tokenize(self, query: str) -> List[str]:
        spaced = re.sub(r"([()])", r" \1 ", query)
        return [t for t in spaced.split() if t]

    def parse_query(self, query: str) -> Dict[str, Any]:
        tokens = self._tokenize(query)
        if not tokens:
            return {"type": "term", "value": ""}

        output: List[str] = []
        ops: List[str] = []

        for raw in tokens:
            token = raw.upper()
            if token in self._ops:
                while ops and ops[-1] in self._ops and self._precedence[ops[-1]] >= self._precedence[token]:
                    output.append(ops.pop())
                ops.append(token)
            elif raw == "(":
                ops.append(raw)
            elif raw == ")":
                while ops and ops[-1] != "(":
                    output.append(ops.pop())
                if ops and ops[-1] == "(":
                    ops.pop()
            else:
                output.append(raw)

        while ops:
            output.append(ops.pop())

        stack: List[Dict[str, Any]] = []
        for tok in output:
            if tok in self._ops:
                if tok == "NOT":
                    node = stack.pop() if stack else {"type": "term", "value": ""}
                    stack.append({"type": "not", "child": node})
                else:
                    right = stack.pop() if stack else {"type": "term", "value": ""}
                    left = stack.pop() if stack else {"type": "term", "value": ""}
                    stack.append({"type": tok.lower(), "left": left, "right": right})
            else:
                stack.append({"type": "term", "value": tok})

        return stack[-1] if stack else {"type": "term", "value": ""}

    def to_search_query(self, node: Dict[str, Any]) -> str:
        ntype = node.get("type")
        if ntype == "term":
            return node.get("value", "")
        if ntype == "not":
            return f"NOT ({self.to_search_query(node['child'])})"
        if ntype in {"and", "or"}:
            left = self.to_search_query(node["left"])
            right = self.to_search_query(node["right"])
            return f"({left} {ntype.upper()} {right})"
        return ""


query_parser = QueryParser()
