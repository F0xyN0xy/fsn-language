#!/usr/bin/env python3
"""
FSN - Freeform Sentence Notation  v2.0
A programming language where code reads like natural English.
File extension: .fsn

New in v2: math, strings, file I/O, GUI windows, date/time, random numbers
"""

import sys
import re
import os
import math
import random
import datetime

# ─────────────────────────────────────────────
#  LEXER
# ─────────────────────────────────────────────

TOKEN_PATTERNS = [
    ("STRING",  r'"[^"]*"'),
    ("NUMBER",  r'\d+\.\d+|\d+'),
    ("BOOL",    r'\b(true|false)\b'),
    ("WORD",    r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ("COMMA",   r','),
    ("PERIOD",  r'\.'),
    ("NEWLINE", r'\n'),
    ("SKIP",    r'[ \t]+'),
]

_MASTER = re.compile('|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_PATTERNS))

class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"

def tokenize(source: str):
    source = source.replace('\r\n', '\n').replace('\r', '\n')  # normalize Windows line endings
    tokens = []
    line   = 1
    for m in _MASTER.finditer(source):
        kind  = m.lastgroup
        value = m.group()
        if kind == "SKIP":    continue
        if kind == "NEWLINE": line += 1; continue
        if kind == "STRING":  value = value[1:-1]
        elif kind == "NUMBER": value = float(value) if '.' in value else int(value)
        elif kind == "BOOL":   value = (value == "true")
        tokens.append(Token(kind, value, line))
    return tokens

# ─────────────────────────────────────────────
#  AST NODES
# ─────────────────────────────────────────────

class Node: pass

class Program(Node):
    def __init__(self, stmts): self.stmts = stmts

class LetStmt(Node):
    def __init__(self, name, expr, line): self.name=name; self.expr=expr; self.line=line

class SetStmt(Node):
    def __init__(self, name, expr, line): self.name=name; self.expr=expr; self.line=line

class SayStmt(Node):
    def __init__(self, exprs, line): self.exprs=exprs; self.line=line

class AskStmt(Node):
    def __init__(self, prompt, varname, line): self.prompt=prompt; self.varname=varname; self.line=line

class IfStmt(Node):
    def __init__(self, cond, then_block, else_block, line):
        self.cond=cond; self.then_block=then_block; self.else_block=else_block; self.line=line

class RepeatStmt(Node):
    def __init__(self, times, body, line): self.times=times; self.body=body; self.line=line

class KeepDoingStmt(Node):
    def __init__(self, cond, body, line): self.cond=cond; self.body=body; self.line=line

class ForEachStmt(Node):
    def __init__(self, var, list_expr, body, line):
        self.var=var; self.list_expr=list_expr; self.body=body; self.line=line

class DefineStmt(Node):
    def __init__(self, name, params, body, line):
        self.name=name; self.params=params; self.body=body; self.line=line

class CallStmt(Node):
    def __init__(self, name, args, line): self.name=name; self.args=args; self.line=line

class GiveBackStmt(Node):
    def __init__(self, expr, line): self.expr=expr; self.line=line

class ListLiteral(Node):
    def __init__(self, items): self.items=items

class AddToList(Node):
    def __init__(self, expr, list_name, line): self.expr=expr; self.list_name=list_name; self.line=line

class RemoveFromList(Node):
    def __init__(self, expr, list_name, line): self.expr=expr; self.list_name=list_name; self.line=line

class SaySize(Node):
    def __init__(self, list_name, line): self.list_name=list_name; self.line=line

class BinOp(Node):
    def __init__(self, op, left, right): self.op=op; self.left=left; self.right=right

class UnaryOp(Node):
    def __init__(self, op, operand): self.op=op; self.operand=operand

class VarRef(Node):
    def __init__(self, name): self.name=name

class Literal(Node):
    def __init__(self, value): self.value=value

class ResultOf(Node):
    def __init__(self, call): self.call=call

class NoteStmt(Node): pass

# File I/O
class WriteFileStmt(Node):
    def __init__(self, content, path, line): self.content=content; self.path=path; self.line=line

class AppendFileStmt(Node):
    def __init__(self, content, path, line): self.content=content; self.path=path; self.line=line

# GUI
class OpenWindowStmt(Node):
    def __init__(self, title, width, height, line):
        self.title=title; self.width=width; self.height=height; self.line=line

class AddLabelStmt(Node):
    def __init__(self, text, varname, line): self.text=text; self.varname=varname; self.line=line

class AddButtonStmt(Node):
    def __init__(self, text, action_name, line): self.text=text; self.action_name=action_name; self.line=line

class AddInputStmt(Node):
    def __init__(self, varname, line): self.varname=varname; self.line=line

class AddImageStmt(Node):
    def __init__(self, path, line): self.path=path; self.line=line

class ShowPopupStmt(Node):
    def __init__(self, message, line): self.message=message; self.line=line

class ShowWindowStmt(Node):
    def __init__(self, line): self.line=line

class SetLabelStmt(Node):
    def __init__(self, varname, text, line): self.varname=varname; self.text=text; self.line=line

# ─────────────────────────────────────────────
#  PARSER
# ─────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg, line): super().__init__(f"Line {line}: {msg}"); self.line=line

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def peek(self, offset=0):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else None

    def consume(self):
        t = self.tokens[self.pos]; self.pos += 1; return t

    def expect_period(self):
        if self.peek() and self.peek().type == "PERIOD": self.consume()

    def expect_word(self, *words):
        for w in words:
            t = self.peek()
            if not t or t.type != "WORD" or t.value.lower() != w.lower():
                line = t.line if t else "?"
                got  = repr(t.value) if t else "end of file"
                raise ParseError(f"Expected '{w}' but got {got}.", line)
            self.consume()

    def peek_words(self, *words):
        for i, w in enumerate(words):
            t = self.peek(i)
            if not t or t.type != "WORD" or t.value.lower() != w.lower():
                return False
        return True

    def current_line(self):
        t = self.peek(); return t.line if t else "?"

    # ── Top level ───────────────────────────────

    def parse(self):
        stmts = []
        while self.pos < len(self.tokens):
            stmt = self.parse_statement()
            if stmt: stmts.append(stmt)
        return Program(stmts)

    def parse_statement(self):
        t = self.peek()
        if not t: return None
        if t.type != "WORD": self.consume(); return None

        kw = t.value.lower(); line = t.line

        if   kw == "note":    return self.parse_note()
        elif kw == "let":     return self.parse_let()
        elif kw == "set":     return self.parse_set()
        elif kw == "say":     return self.parse_say()
        elif kw == "ask":     return self.parse_ask()
        elif kw == "if":      return self.parse_if()
        elif kw == "repeat":  return self.parse_repeat()
        elif kw == "keep":    return self.parse_keep()
        elif kw == "for":     return self.parse_for_each()
        elif kw == "define":  return self.parse_define()
        elif kw in ("call","run"): return self.parse_call_stmt()
        elif kw == "give":    return self.parse_give_back()
        elif kw == "add":     return self.parse_add()
        elif kw == "remove":  return self.parse_remove_from_list()
        elif kw == "write":   return self.parse_write_file()
        elif kw == "append":  return self.parse_append_file()
        elif kw == "open":    return self.parse_open_window()
        elif kw == "show":    return self.parse_show()
        elif kw == "display": return self.parse_display_window()
        else:
            raise ParseError(f"I don't know what to do with '{t.value}' here.", line)

    # ── Statements ──────────────────────────────

    def parse_note(self):
        note_line = self.peek().line if self.peek() else None
        self.consume()
        while self.peek() and self.peek().type != "PERIOD":
            if note_line and self.peek().line != note_line: break
            self.consume()
        if self.peek() and self.peek().type == "PERIOD": self.consume()
        return NoteStmt()

    def parse_let(self):
        line = self.current_line(); self.consume()
        name = self.parse_identifier(); self.expect_word("be")
        expr = self.parse_expr(); self.expect_period()
        return LetStmt(name, expr, line)

    def parse_set(self):
        line = self.current_line(); self.consume()
        if self.peek_words("label"):
            self.consume()
            varname = self.parse_identifier(); self.expect_word("to")
            text = self.parse_expr(); self.expect_period()
            return SetLabelStmt(varname, text, line)
        name = self.parse_identifier(); self.expect_word("to")
        expr = self.parse_expr(); self.expect_period()
        return SetStmt(name, expr, line)

    def parse_say(self):
        line = self.current_line(); self.consume()
        if self.peek_words("the","size","of"):
            self.consume(); self.consume(); self.consume()
            name = self.parse_identifier(); self.expect_period()
            return SaySize(name, line)
        exprs = [self.parse_expr()]
        while self.peek() and self.peek().type == "COMMA":
            self.consume(); exprs.append(self.parse_expr())
        self.expect_period()
        return SayStmt(exprs, line)

    def parse_ask(self):
        line = self.current_line(); self.consume()
        prompt = self.parse_primary()
        self.expect_word("and","store","it","in")
        name = self.parse_identifier(); self.expect_period()
        return AskStmt(prompt, name, line)

    def parse_if(self):
        line = self.current_line(); self.consume()
        cond = self.parse_condition(); self.expect_word("then")
        then_block = self.parse_block(end_words=[["end","if"],["otherwise"]])
        else_block = []
        if self.peek_words("otherwise"):
            self.consume()
            else_block = self.parse_block(end_words=[["end","if"]])
        if self.peek_words("end","if"): self.consume(); self.consume()
        self.expect_period()
        return IfStmt(cond, then_block, else_block, line)

    def parse_repeat(self):
        line = self.current_line(); self.consume()
        times_expr = self.parse_primary(); self.expect_word("times")
        body = self.parse_block(end_words=[["end","repeat"]])
        self.expect_word("end","repeat"); self.expect_period()
        return RepeatStmt(times_expr, body, line)

    def parse_keep(self):
        line = self.current_line(); self.consume()
        self.expect_word("doing","while")
        cond = self.parse_condition()
        body = self.parse_block(end_words=[["end","keep"]])
        self.expect_word("end","keep"); self.expect_period()
        return KeepDoingStmt(cond, body, line)

    def parse_for_each(self):
        line = self.current_line(); self.consume()
        self.expect_word("each"); var = self.parse_identifier(); self.expect_word("in")
        list_expr = self.parse_primary()
        body = self.parse_block(end_words=[["end","for"]])
        self.expect_word("end","for"); self.expect_period()
        return ForEachStmt(var, list_expr, body, line)

    def parse_define(self):
        line = self.current_line(); self.consume()
        name = self.parse_func_name()
        params = []
        if self.peek_words("with"):
            self.consume()
            params.append(self.parse_identifier())
            while self.peek() and self.peek().type == "COMMA":
                self.consume(); params.append(self.parse_identifier())
        body = self.parse_block(end_words=[["end","define"]])
        self.expect_word("end","define"); self.expect_period()
        return DefineStmt(name, params, body, line)

    def parse_call_stmt(self):
        line = self.current_line(); self.consume()
        name = self.parse_func_name()
        args = []
        if self.peek_words("with"):
            self.consume()
            args.append(self.parse_expr())
            while self.peek() and self.peek().type == "COMMA":
                self.consume(); args.append(self.parse_expr())
        self.expect_period()
        return CallStmt(name, args, line)

    def parse_give_back(self):
        line = self.current_line(); self.consume()
        self.expect_word("back"); expr = self.parse_expr(); self.expect_period()
        return GiveBackStmt(expr, line)

    def parse_add(self):
        line = self.current_line(); self.consume()
        # GUI additions
        if self.peek_words("label"):
            self.consume(); text = self.parse_expr()
            varname = None
            if self.peek_words("as"): self.consume(); varname = self.parse_identifier()
            self.expect_period(); return AddLabelStmt(text, varname, line)
        if self.peek_words("button"):
            self.consume(); text = self.parse_expr()
            action = None
            if self.peek_words("that","calls"): self.consume(); self.consume(); action = self.parse_func_name()
            self.expect_period(); return AddButtonStmt(text, action, line)
        if self.peek_words("input","as"):
            self.consume(); self.consume()
            varname = self.parse_identifier(); self.expect_period()
            return AddInputStmt(varname, line)
        if self.peek_words("image"):
            self.consume(); path = self.parse_expr(); self.expect_period()
            return AddImageStmt(path, line)
        # Normal list add
        expr = self.parse_primary(); self.expect_word("to")
        name = self.parse_identifier(); self.expect_period()
        return AddToList(expr, name, line)

    def parse_remove_from_list(self):
        line = self.current_line(); self.consume()
        expr = self.parse_primary(); self.expect_word("from")
        name = self.parse_identifier(); self.expect_period()
        return RemoveFromList(expr, name, line)

    def parse_write_file(self):
        line = self.current_line(); self.consume()
        content = self.parse_expr(); self.expect_word("to","file")
        path = self.parse_expr(); self.expect_period()
        return WriteFileStmt(content, path, line)

    def parse_append_file(self):
        line = self.current_line(); self.consume()
        content = self.parse_expr(); self.expect_word("to","file")
        path = self.parse_expr(); self.expect_period()
        return AppendFileStmt(content, path, line)

    def parse_open_window(self):
        line = self.current_line(); self.consume()
        self.expect_word("window","titled"); title = self.parse_expr()
        width = Literal(600); height = Literal(400)
        if self.peek_words("with","width"):
            self.consume(); self.consume(); width = self.parse_primary()
            if self.peek() and self.peek().type == "COMMA":
                self.consume(); self.expect_word("height"); height = self.parse_primary()
        self.expect_period()
        return OpenWindowStmt(title, width, height, line)

    def parse_show(self):
        line = self.current_line(); self.consume()
        if self.peek_words("window"):
            self.consume(); self.expect_period(); return ShowWindowStmt(line)
        if self.peek_words("popup"):
            self.consume(); msg = self.parse_expr(); self.expect_period()
            return ShowPopupStmt(msg, line)
        raise ParseError("After 'show' I expected 'window' or 'popup'.", line)

    def parse_display_window(self):
        line = self.current_line(); self.consume()
        self.expect_word("window"); self.expect_period()
        return ShowWindowStmt(line)

    # ── Block ────────────────────────────────────

    def parse_block(self, end_words):
        stmts = []
        while self.pos < len(self.tokens):
            for ew in end_words:
                if self.peek_words(*ew): return stmts
            stmt = self.parse_statement()
            if stmt and not isinstance(stmt, NoteStmt): stmts.append(stmt)
        return stmts

    # ── Expressions ──────────────────────────────

    def parse_expr(self):
        # List literal
        if self.peek_words("a","list","of"):
            self.consume(); self.consume(); self.consume()
            items = [self.parse_primary()]
            while self.peek() and self.peek().type == "COMMA":
                self.consume(); items.append(self.parse_primary())
            return ListLiteral(items)

        # "the result of FUNC with ARGS"
        if self.peek_words("the","result","of"):
            self.consume(); self.consume(); self.consume()
            name = self.parse_func_name()
            args = []
            if self.peek_words("with"):
                self.consume()
                args.append(self.parse_expr())
                while self.peek() and self.peek().type == "COMMA":
                    self.consume(); args.append(self.parse_expr())
            return ResultOf(CallStmt(name, args, self.current_line()))

        left = self.parse_primary()

        while True:
            if self.peek_words("plus"):
                self.consume(); left = BinOp("plus", left, self.parse_primary())
            elif self.peek_words("minus"):
                self.consume(); left = BinOp("minus", left, self.parse_primary())
            elif self.peek_words("times"):
                self.consume(); left = BinOp("times", left, self.parse_primary())
            elif self.peek_words("divided","by"):
                self.consume(); self.consume(); left = BinOp("divided by", left, self.parse_primary())
            elif self.peek_words("modulo"):
                self.consume(); left = BinOp("modulo", left, self.parse_primary())
            elif self.peek_words("to","the","power","of"):
                self.consume(); self.consume(); self.consume(); self.consume()
                left = BinOp("power", left, self.parse_primary())
            else:
                break
        return left

    def parse_primary(self):
        t = self.peek()
        if not t: raise ParseError("Expected a value but found end of file.", "?")

        # ── Math builtins ──────────────────────────
        if self.peek_words("the","square","root","of"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__sqrt__", [self.parse_primary()], self.current_line()))
        if self.peek_words("the","absolute","value","of"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__abs__", [self.parse_primary()], self.current_line()))
        if self.peek_words("round"):
            self.consume()
            operand = self.parse_primary()
            # Check for "to N decimal places"
            # peek(0)=to, peek(1)=N (number), peek(2)=decimal, peek(3)=places
            p0 = self.peek(0); p1 = self.peek(1); p2 = self.peek(2); p3 = self.peek(3)
            is_decimal_form = (
                p0 and p0.type == "WORD" and p0.value.lower() == "to" and
                p1 and p1.type == "NUMBER" and
                p2 and p2.type == "WORD" and p2.value.lower() == "decimal" and
                p3 and p3.type == "WORD" and p3.value.lower() == "places"
            )
            if is_decimal_form:
                self.consume()  # to
                places = self.parse_primary()  # N
                self.consume()  # decimal
                self.consume()  # places
                return ResultOf(CallStmt("__round__", [operand, places], self.current_line()))
            return ResultOf(CallStmt("__round__", [operand, Literal(0)], self.current_line()))
        if self.peek_words("the","floor","of"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__floor__", [self.parse_primary()], self.current_line()))
        if self.peek_words("the","ceiling","of"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__ceil__", [self.parse_primary()], self.current_line()))
        if self.peek_words("the","minimum","of"):
            for _ in range(3): self.consume()
            a = self.parse_primary(); self.expect_word("and"); b = self.parse_primary()
            return ResultOf(CallStmt("__min__", [a, b], self.current_line()))
        if self.peek_words("the","maximum","of"):
            for _ in range(3): self.consume()
            a = self.parse_primary(); self.expect_word("and"); b = self.parse_primary()
            return ResultOf(CallStmt("__max__", [a, b], self.current_line()))

        # ── String builtins ────────────────────────
        if self.peek_words("uppercase","of"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__upper__", [self.parse_primary()], self.current_line()))
        if self.peek_words("lowercase","of"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__lower__", [self.parse_primary()], self.current_line()))
        if self.peek_words("trimmed"):
            self.consume()
            return ResultOf(CallStmt("__trim__", [self.parse_primary()], self.current_line()))
        if self.peek_words("length","of"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__len__", [self.parse_primary()], self.current_line()))
        if self.peek_words("reverse","of"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__reverse__", [self.parse_primary()], self.current_line()))
        if self.peek_words("number","from"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__to_number__", [self.parse_primary()], self.current_line()))
        if self.peek_words("text","from"):
            self.consume(); self.consume()
            return ResultOf(CallStmt("__to_text__", [self.parse_primary()], self.current_line()))

        # ── File reading ───────────────────────────
        if self.peek_words("contents","of","file"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__read_file__", [self.parse_primary()], self.current_line()))

        # ── Random ────────────────────────────────
        if self.peek_words("a","random","number","between"):
            for _ in range(4): self.consume()
            a = self.parse_primary(); self.expect_word("and"); b = self.parse_primary()
            return ResultOf(CallStmt("__random_int__", [a, b], self.current_line()))
        if self.peek_words("a","random","decimal","between"):
            for _ in range(4): self.consume()
            a = self.parse_primary(); self.expect_word("and"); b = self.parse_primary()
            return ResultOf(CallStmt("__random_float__", [a, b], self.current_line()))
        if self.peek_words("a","random","choice","from"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__random_choice__", [self.parse_expr()], self.current_line()))

        # ── Date/time ─────────────────────────────
        if self.peek_words("today"):
            self.consume(); return ResultOf(CallStmt("__today__", [], self.current_line()))
        if self.peek_words("now"):
            self.consume(); return ResultOf(CallStmt("__now__", [], self.current_line()))
        if self.peek_words("the","current","year"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__year__", [], self.current_line()))
        if self.peek_words("the","current","month"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__month__", [], self.current_line()))
        if self.peek_words("the","current","day"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__day__", [], self.current_line()))
        if self.peek_words("the","current","hour"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__hour__", [], self.current_line()))
        if self.peek_words("the","current","minute"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__minute__", [], self.current_line()))

        # ── Literals & vars ────────────────────────
        if t.type == "STRING": self.consume(); return Literal(t.value)
        if t.type == "NUMBER": self.consume(); return Literal(t.value)
        if t.type == "BOOL":   self.consume(); return Literal(t.value)
        if t.type == "WORD":   return VarRef(self.parse_identifier())

        raise ParseError(f"Unexpected token '{t.value}' while reading a value.", t.line)

    def parse_identifier(self):
        STOP = {"be","to","then","and","or","not","with","in","from","of",
                "plus","minus","times","divided","modulo","is","otherwise",
                "end","give","back","while","each","store","it",
                "the","doing","size","list",
                "if","repeat","keep","for","define","call","run",
                "say","ask","set","let","add","remove","note",
                "write","append","open","show","display","as","that",
                "power","decimal","places","between","file","titled",
                "width","height","popup","window","label","button",
                "input","image","calls","sorted","reversed",
                "contains","starts","ends"}
        t = self.peek()
        if not t or t.type != "WORD":
            line = t.line if t else "?"
            got  = repr(t.value) if t else "end of file"
            raise ParseError(f"Expected a name but got {got}.", line)
        parts = []
        while self.peek() and self.peek().type == "WORD" and self.peek().value.lower() not in STOP:
            parts.append(self.consume().value)
        if not parts:
            raise ParseError(f"Expected a variable name but got '{t.value}'.", t.line)
        return " ".join(parts)

    def parse_func_name(self):
        STOP = {"with","then","and","otherwise","end","give","back","while",
                "each","store","it","the","doing"}
        parts = []
        while self.peek() and self.peek().type == "WORD" and self.peek().value.lower() not in STOP:
            parts.append(self.consume().value)
        if not parts:
            raise ParseError("Expected a function name.", self.current_line())
        return " ".join(parts)

    def parse_condition(self):
        left = self.parse_comparison()
        while True:
            if self.peek_words("and"):
                self.consume(); left = BinOp("and", left, self.parse_comparison())
            elif self.peek_words("or"):
                self.consume(); left = BinOp("or", left, self.parse_comparison())
            else: break
        return left

    def parse_comparison(self):
        if self.peek_words("not"):
            self.consume(); return UnaryOp("not", self.parse_comparison())
        left = self.parse_expr()
        if self.peek_words("is","greater","than","or","equal","to"):
            for _ in range(6): self.consume()
            return BinOp(">=", left, self.parse_expr())
        if self.peek_words("is","less","than","or","equal","to"):
            for _ in range(6): self.consume()
            return BinOp("<=", left, self.parse_expr())
        if self.peek_words("is","greater","than"):
            for _ in range(3): self.consume()
            return BinOp(">", left, self.parse_expr())
        if self.peek_words("is","less","than"):
            for _ in range(3): self.consume()
            return BinOp("<", left, self.parse_expr())
        if self.peek_words("contains"):
            self.consume(); return BinOp("contains", left, self.parse_expr())
        if self.peek_words("starts","with"):
            self.consume(); self.consume(); return BinOp("starts with", left, self.parse_expr())
        if self.peek_words("ends","with"):
            self.consume(); self.consume(); return BinOp("ends with", left, self.parse_expr())
        if self.peek_words("is","not"):
            self.consume(); self.consume(); return BinOp("!=", left, self.parse_expr())
        if self.peek_words("is"):
            self.consume(); return BinOp("==", left, self.parse_expr())
        return left

# ─────────────────────────────────────────────
#  BUILT-IN FUNCTION TABLE
# ─────────────────────────────────────────────

def _fsn_builtin(name, args, line):
    """Returns (value, handled)."""
    a = args

    # Math
    if name == "__sqrt__":
        if a[0] < 0: raise RuntimeError_(f"You can't take the square root of a negative number.", line)
        return math.sqrt(a[0]), True
    if name == "__abs__":   return abs(a[0]), True
    if name == "__round__":
        places = int(a[1]) if len(a) > 1 else 0
        r = round(a[0], places)
        return (int(r) if places == 0 else r), True
    if name == "__floor__": return math.floor(a[0]), True
    if name == "__ceil__":  return math.ceil(a[0]), True
    if name == "__min__":   return min(a[0], a[1]), True
    if name == "__max__":   return max(a[0], a[1]), True

    # String
    if name == "__upper__": return str(a[0]).upper(), True
    if name == "__lower__": return str(a[0]).lower(), True
    if name == "__trim__":  return str(a[0]).strip(), True
    if name == "__len__":
        return (len(a[0]) if isinstance(a[0], list) else len(str(a[0]))), True
    if name == "__reverse__":
        return (list(reversed(a[0])) if isinstance(a[0], list) else str(a[0])[::-1]), True
    if name == "__replace__":  return str(a[0]).replace(str(a[1]), str(a[2])), True
    if name == "__split__":
        sep = str(a[1]) if len(a) > 1 else " "
        return str(a[0]).split(sep), True
    if name == "__join__":
        sep = str(a[1]) if len(a) > 1 else " "
        return sep.join(str(x) for x in a[0]), True
    if name == "__index_of__":
        try:    return str(a[0]).index(str(a[1])), True
        except: return -1, True
    if name == "__substring__":
        return str(a[0])[int(a[1]):int(a[2])], True

    # Type conversion
    if name == "__to_number__":
        v = str(a[0]).strip()
        try:    return int(v), True
        except:
            try:    return float(v), True
            except: raise RuntimeError_(f"I can't turn '{a[0]}' into a number.", line)
    if name == "__to_text__":
        v = a[0]
        if isinstance(v, bool): return ("true" if v else "false"), True
        if isinstance(v, float) and v == int(v): return str(int(v)), True
        return str(v), True

    # File reading
    if name == "__read_file__":
        try:
            with open(str(a[0]), "r", encoding="utf-8") as f: return f.read(), True
        except FileNotFoundError:
            raise RuntimeError_(f"I can't find the file '{a[0]}'.", line)
        except Exception as e:
            raise RuntimeError_(f"Problem reading '{a[0]}': {e}", line)

    # Random
    if name == "__random_int__":    return random.randint(int(a[0]), int(a[1])), True
    if name == "__random_float__":  return random.uniform(float(a[0]), float(a[1])), True
    if name == "__random_choice__":
        lst = a[0]
        if not isinstance(lst, list) or len(lst) == 0:
            raise RuntimeError_("I can't pick from an empty list.", line)
        return random.choice(lst), True

    # Date/time
    if name == "__today__":   return datetime.date.today().strftime("%Y-%m-%d"), True
    if name == "__now__":     return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), True
    if name == "__year__":    return datetime.datetime.now().year, True
    if name == "__month__":   return datetime.datetime.now().month, True
    if name == "__day__":     return datetime.datetime.now().day, True
    if name == "__hour__":    return datetime.datetime.now().hour, True
    if name == "__minute__":  return datetime.datetime.now().minute, True

    return None, False

# ─────────────────────────────────────────────
#  INTERPRETER
# ─────────────────────────────────────────────

class ReturnException(Exception):
    def __init__(self, value): self.value = value

class RuntimeError_(Exception):
    def __init__(self, msg, line): super().__init__(f"Line {line}: {msg}"); self.line=line

class Environment:
    def __init__(self, parent=None):
        self.vars = {}; self.parent = parent

    def get(self, name):
        if name in self.vars:  return self.vars[name]
        if self.parent:        return self.parent.get(name)
        raise KeyError(name)

    def set(self, name, value): self.vars[name] = value

    def assign(self, name, value):
        if name in self.vars: self.vars[name] = value
        elif self.parent and self._in_parent(name): self.parent.assign(name, value)
        else: self.vars[name] = value

    def _in_parent(self, name):
        env = self.parent
        while env:
            if name in env.vars: return True
            env = env.parent
        return False


class Interpreter:
    def __init__(self):
        self.global_env   = Environment()
        self.functions    = {}
        self._gui_root    = None
        self._gui_frame   = None
        self._gui_labels  = {}
        self._gui_inputs  = {}
        self._tk          = None

    def run(self, program): self.exec_block(program.stmts, self.global_env)

    def exec_block(self, stmts, env):
        for stmt in stmts: self.exec(stmt, env)

    def exec(self, node, env):
        if isinstance(node, NoteStmt): return

        elif isinstance(node, LetStmt):
            env.set(node.name, self.eval(node.expr, env))

        elif isinstance(node, SetStmt):
            val = self.eval(node.expr, env)
            try: env.assign(node.name, val)
            except: raise RuntimeError_(
                f"I don't know the variable '{node.name}'. Declare it with 'let' first.", node.line)

        elif isinstance(node, SayStmt):
            print(" ".join(self.fsn_str(self.eval(e, env)) for e in node.exprs))

        elif isinstance(node, SaySize):
            try: val = env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.", node.line)
            print(len(val))

        elif isinstance(node, AskStmt):
            prompt = self.eval(node.prompt, env)
            val = input(str(prompt) + ": ")
            try:    val = int(val)
            except:
                try: val = float(val)
                except: pass
            env.set(node.varname, val)

        elif isinstance(node, IfStmt):
            if self.eval(node.cond, env): self.exec_block(node.then_block, Environment(env))
            else:                         self.exec_block(node.else_block, Environment(env))

        elif isinstance(node, RepeatStmt):
            for _ in range(int(self.eval(node.times, env))):
                self.exec_block(node.body, Environment(env))

        elif isinstance(node, KeepDoingStmt):
            while self.eval(node.cond, env): self.exec_block(node.body, Environment(env))

        elif isinstance(node, ForEachStmt):
            lst = self.eval(node.list_expr, env)
            for item in lst:
                inner = Environment(env); inner.set(node.var, item)
                self.exec_block(node.body, inner)

        elif isinstance(node, DefineStmt):
            self.functions[node.name] = node

        elif isinstance(node, CallStmt):
            self.call_function(node.name, node.args, env, node.line)

        elif isinstance(node, GiveBackStmt):
            raise ReturnException(self.eval(node.expr, env))

        elif isinstance(node, AddToList):
            val = self.eval(node.expr, env)
            try: lst = env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.", node.line)
            lst.append(val)

        elif isinstance(node, RemoveFromList):
            val = self.eval(node.expr, env)
            try: lst = env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.", node.line)
            try: lst.remove(val)
            except ValueError: raise RuntimeError_(f"'{val}' is not in the list.", node.line)

        # File I/O
        elif isinstance(node, WriteFileStmt):
            content = str(self.eval(node.content, env))
            path    = str(self.eval(node.path, env))
            try:
                with open(path, "w", encoding="utf-8") as f: f.write(content)
            except Exception as e:
                raise RuntimeError_(f"Problem writing to '{path}': {e}", node.line)

        elif isinstance(node, AppendFileStmt):
            content = str(self.eval(node.content, env))
            path    = str(self.eval(node.path, env))
            try:
                with open(path, "a", encoding="utf-8") as f: f.write(content + "\n")
            except Exception as e:
                raise RuntimeError_(f"Problem appending to '{path}': {e}", node.line)

        # GUI
        elif isinstance(node, OpenWindowStmt):
            self._gui_open(str(self.eval(node.title, env)),
                           int(self.eval(node.width, env)),
                           int(self.eval(node.height, env)), node.line)

        elif isinstance(node, AddLabelStmt):
            self._gui_add_label(str(self.eval(node.text, env)), node.varname, env, node.line)

        elif isinstance(node, AddButtonStmt):
            self._gui_add_button(str(self.eval(node.text, env)), node.action_name, env, node.line)

        elif isinstance(node, AddInputStmt):
            self._gui_add_input(node.varname, env, node.line)

        elif isinstance(node, AddImageStmt):
            self._gui_add_image(str(self.eval(node.path, env)), node.line)

        elif isinstance(node, ShowPopupStmt):
            self._gui_popup(str(self.eval(node.message, env)), node.line)

        elif isinstance(node, ShowWindowStmt):
            self._gui_show(node.line)

        elif isinstance(node, SetLabelStmt):
            self._gui_set_label(node.varname, str(self.eval(node.text, env)), node.line)

    def call_function(self, name, arg_exprs, env, line):
        args = [self.eval(a, env) for a in arg_exprs]
        result, handled = _fsn_builtin(name, args, line)
        if handled: return result

        if name not in self.functions:
            raise RuntimeError_(f"I don't know a function called '{name}'.", line)
        func = self.functions[name]
        if len(args) != len(func.params):
            raise RuntimeError_(f"'{name}' needs {len(func.params)} input(s) but got {len(args)}.", line)
        inner = Environment(self.global_env)
        for p, v in zip(func.params, args): inner.set(p, v)
        try: self.exec_block(func.body, inner)
        except ReturnException as r: return r.value
        return None

    def eval(self, node, env):
        if isinstance(node, Literal):     return node.value
        if isinstance(node, VarRef):
            try:    return env.get(node.name)
            except: raise RuntimeError_(f"I don't know what '{node.name}' is. Did you declare it?", 0)
        if isinstance(node, ListLiteral): return [self.eval(i, env) for i in node.items]
        if isinstance(node, ResultOf):
            call = node.call
            r = self.call_function(call.name, call.args, env, call.line)
            if r is None: raise RuntimeError_(f"'{call.name}' does not give back a value.", call.line)
            return r
        if isinstance(node, BinOp):
            if node.op == "and": return bool(self.eval(node.left, env)) and bool(self.eval(node.right, env))
            if node.op == "or":  return bool(self.eval(node.left, env)) or  bool(self.eval(node.right, env))
            l = self.eval(node.left, env); r = self.eval(node.right, env)
            if node.op == "plus":
                if isinstance(l, str) or isinstance(r, str): return str(l) + str(r)
                return l + r
            if node.op == "minus":       return l - r
            if node.op == "times":       return l * r
            if node.op == "divided by":
                if r == 0: raise RuntimeError_("You can't divide by zero.", 0)
                return l / r
            if node.op == "modulo":      return l % r
            if node.op == "power":       return l ** r
            if node.op == "==":          return l == r
            if node.op == "!=":          return l != r
            if node.op == ">":           return l > r
            if node.op == "<":           return l < r
            if node.op == ">=":          return l >= r
            if node.op == "<=":          return l <= r
            if node.op == "contains":    return str(r) in str(l)
            if node.op == "starts with": return str(l).startswith(str(r))
            if node.op == "ends with":   return str(l).endswith(str(r))
        if isinstance(node, UnaryOp):
            if node.op == "not": return not bool(self.eval(node.operand, env))
        raise RuntimeError_("I don't know how to evaluate this expression.", 0)

    def fsn_str(self, val):
        if isinstance(val, bool): return "true" if val else "false"
        if isinstance(val, float) and val == int(val): return str(int(val))
        if isinstance(val, list):  return ", ".join(self.fsn_str(v) for v in val)
        return str(val)

    # ── GUI ───────────────────────────────────────

    def _require_gui(self, line):
        if self._gui_root is None:
            raise RuntimeError_('Open a window first: open window titled "My App".', line)

    def _gui_open(self, title, width, height, line):
        try:
            import tkinter as tk
            self._tk = tk
        except ImportError:
            raise RuntimeError_("Tkinter is not available on this system.", line)
        root = tk.Tk()
        root.title(title)
        root.geometry(f"{width}x{height}")
        root.configure(bg="#f5f5f5")
        frame = tk.Frame(root, bg="#f5f5f5", padx=24, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        self._gui_root  = root
        self._gui_frame = frame

    def _gui_add_label(self, text, varname, env, line):
        self._require_gui(line)
        tk = self._tk
        lbl = tk.Label(self._gui_frame, text=text, bg="#f5f5f5",
                       font=("Segoe UI", 12), anchor="w")
        lbl.pack(fill=tk.X, pady=3)
        if varname:
            self._gui_labels[varname] = lbl
            env.set(varname, text)

    def _gui_add_button(self, text, action_name, env, line):
        self._require_gui(line)
        tk = self._tk; interp = self
        def on_click():
            for vname, entry in interp._gui_inputs.items():
                val = entry.get()
                try:    val = int(val)
                except:
                    try:    val = float(val)
                    except: pass
                interp.global_env.set(vname, val)
            if action_name and action_name in interp.functions:
                try:
                    interp.call_function(action_name, [], interp.global_env, line)
                except ReturnException: pass
                except RuntimeError_ as e: print(f"⚠  {e}")
        btn = tk.Button(self._gui_frame, text=text, command=on_click,
                        bg="#4a90d9", fg="white", font=("Segoe UI", 11, "bold"),
                        relief="flat", padx=16, pady=7, cursor="hand2",
                        activebackground="#357abd", activeforeground="white")
        btn.pack(pady=6, anchor="w")

    def _gui_add_input(self, varname, env, line):
        self._require_gui(line)
        tk = self._tk
        entry = tk.Entry(self._gui_frame, font=("Segoe UI", 12),
                         relief="solid", bd=1, highlightthickness=1,
                         highlightcolor="#4a90d9")
        entry.pack(fill=tk.X, pady=4)
        self._gui_inputs[varname] = entry
        env.set(varname, "")

    def _gui_add_image(self, path, line):
        self._require_gui(line)
        tk = self._tk
        try:
            img = tk.PhotoImage(file=path)
            lbl = tk.Label(self._gui_frame, image=img, bg="#f5f5f5")
            lbl.image = img; lbl.pack(pady=4)
        except Exception as e:
            raise RuntimeError_(f"Could not load image '{path}': {e}", line)

    def _gui_set_label(self, varname, text, line):
        self._require_gui(line)
        if varname not in self._gui_labels:
            raise RuntimeError_(f"I don't know a label called '{varname}'.", line)
        self._gui_labels[varname].config(text=text)
        self._gui_root.update()

    def _gui_popup(self, message, line):
        try:
            import tkinter.messagebox as mb
            if self._gui_root is None:
                import tkinter as tk
                r = tk.Tk(); r.withdraw(); mb.showinfo("FSN", message); r.destroy()
            else:
                mb.showinfo("FSN", message)
        except ImportError:
            print(f"[Popup] {message}")

    def _gui_show(self, line):
        self._require_gui(line)
        self._gui_root.mainloop()


# ─────────────────────────────────────────────
#  RUNNER
# ─────────────────────────────────────────────

def run_source(source: str, filename="<input>"):
    try:
        tokens  = tokenize(source)
        parser  = Parser(tokens)
        program = parser.parse()
        interp  = Interpreter()
        interp.run(program)
    except ParseError   as e: print(f"\n⚠  Parse error in {filename}:\n   {e}\n")
    except RuntimeError_ as e: print(f"\n⚠  Runtime error in {filename}:\n   {e}\n")
    except ReturnException:    pass
    except KeyboardInterrupt:  print("\nProgram stopped.")

def run_repl():
    print("FSN - Freeform Sentence Notation v2.0  (type 'quit.' to exit)")
    print("───────────────────────────────────────────────────────────────")
    interp = Interpreter()
    buffer = []
    while True:
        try:
            line = input("  ... " if buffer else "fsn> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye."); break
        if line.strip().lower() in ("quit.", "exit.", "quit", "exit"):
            print("Bye."); break
        buffer.append(line)
        full     = "\n".join(buffer)
        open_kw  = sum(1 for l in buffer for kw in ["then","times","while","each"] if kw in l.lower().split())
        close_kw = sum(1 for l in buffer for kw in ["end if","end repeat","end keep","end for","end define"] if kw in l.lower())
        if full.rstrip().endswith(".") and open_kw <= close_kw:
            try:
                tokens  = tokenize(full); program = Parser(tokens).parse()
                interp.exec_block(program.stmts, interp.global_env)
            except ParseError    as e: print(f"⚠  {e}")
            except RuntimeError_  as e: print(f"⚠  {e}")
            except ReturnException:     pass
            buffer = []

def main():
    if len(sys.argv) < 2:
        run_repl(); return
    path = sys.argv[1]
    if not path.endswith(".fsn"):
        print(f"Warning: '{path}' does not have the .fsn extension.")
    if not os.path.exists(path):
        print(f"Error: I can't find the file '{path}'."); sys.exit(1)
    with open(path, "r", encoding="utf-8", newline='') as f:
        source = f.read()
    run_source(source, filename=path)

if __name__ == "__main__":
    main()
