#!/usr/bin/env python3
"""
FSN - Freeform Sentence Notation  v3.0
A programming language where code reads like natural English.
File extension: .fsn

v3 adds: Scratch-style control, list ops, string ops, OS/file system,
         JSON, networking, clipboard, turtle graphics, sound, try/catch,
         timers, type checking, math trig, and more.
"""

import sys, re, os, math, random, datetime, time as _time

# ─────────────────────────────────────────────────────────────────────
#  LEXER
# ─────────────────────────────────────────────────────────────────────

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
    __slots__ = ("type","value","line")
    def __init__(self, t, v, l): self.type=t; self.value=v; self.line=l
    def __repr__(self): return f"Token({self.type},{self.value!r},L{self.line})"

def tokenize(src):
    src = src.replace('\r\n','\n').replace('\r','\n')
    tokens=[]; line=1
    for m in _MASTER.finditer(src):
        k=m.lastgroup; v=m.group()
        if k=="SKIP": continue
        if k=="NEWLINE": line+=1; continue
        if k=="STRING":  v=v[1:-1]
        elif k=="NUMBER": v=float(v) if '.' in v else int(v)
        elif k=="BOOL":   v=(v=="true")
        tokens.append(Token(k,v,line))
    return tokens

# ─────────────────────────────────────────────────────────────────────
#  AST NODES
# ─────────────────────────────────────────────────────────────────────

class Node: pass

# Core
class Program(Node):
    def __init__(self,s): self.stmts=s
class NoteStmt(Node): pass
class LetStmt(Node):
    def __init__(self,n,e,l): self.name=n;self.expr=e;self.line=l
class SetStmt(Node):
    def __init__(self,n,e,l): self.name=n;self.expr=e;self.line=l
class ChangeByStmt(Node):
    def __init__(self,n,e,l): self.name=n;self.expr=e;self.line=l
class SayStmt(Node):
    def __init__(self,es,l): self.exprs=es;self.line=l
class AskStmt(Node):
    def __init__(self,p,v,l): self.prompt=p;self.varname=v;self.line=l

# Control
class IfStmt(Node):
    def __init__(self,c,t,e,l): self.cond=c;self.then_block=t;self.else_block=e;self.line=l
class RepeatStmt(Node):
    def __init__(self,t,b,l): self.times=t;self.body=b;self.line=l
class KeepDoingStmt(Node):
    def __init__(self,c,b,l): self.cond=c;self.body=b;self.line=l
class ForEachStmt(Node):
    def __init__(self,v,le,b,l): self.var=v;self.list_expr=le;self.body=b;self.line=l
class ForRangeStmt(Node):    # repeat with i from 1 to 10
    def __init__(self,v,start,end,step,b,l): self.var=v;self.start=start;self.end=end;self.step=step;self.body=b;self.line=l
class WaitStmt(Node):
    def __init__(self,e,l): self.expr=e;self.line=l
class StopStmt(Node):
    def __init__(self,l): self.line=l
class BreakStmt(Node):
    def __init__(self,l): self.line=l
class ContinueStmt(Node):
    def __init__(self,l): self.line=l
class TryStmt(Node):
    def __init__(self,b,ev,r,l): self.body=b;self.error_var=ev;self.rescue=r;self.line=l

# Functions
class DefineStmt(Node):
    def __init__(self,n,p,b,l): self.name=n;self.params=p;self.body=b;self.line=l
class CallStmt(Node):
    def __init__(self,n,a,l): self.name=n;self.args=a;self.line=l
class GiveBackStmt(Node):
    def __init__(self,e,l): self.expr=e;self.line=l

# Expressions
class Literal(Node):
    def __init__(self,v): self.value=v
class VarRef(Node):
    def __init__(self,n): self.name=n
class BinOp(Node):
    def __init__(self,op,l,r): self.op=op;self.left=l;self.right=r
class UnaryOp(Node):
    def __init__(self,op,o): self.op=op;self.operand=o
class ListLiteral(Node):
    def __init__(self,items): self.items=items
class ResultOf(Node):
    def __init__(self,call): self.call=call

# Lists
class AddToList(Node):
    def __init__(self,e,n,l): self.expr=e;self.list_name=n;self.line=l
class RemoveFromList(Node):
    def __init__(self,e,n,l): self.expr=e;self.list_name=n;self.line=l
class InsertIntoList(Node):
    def __init__(self,e,n,i,l): self.expr=e;self.list_name=n;self.index=i;self.line=l
class ReplaceInList(Node):
    def __init__(self,i,n,e,l): self.index=i;self.list_name=n;self.expr=e;self.line=l
class DeleteItemFromList(Node):
    def __init__(self,i,n,l): self.index=i;self.list_name=n;self.line=l
class SortListStmt(Node):
    def __init__(self,n,rev,l): self.name=n;self.reverse=rev;self.line=l
class ShuffleListStmt(Node):
    def __init__(self,n,l): self.name=n;self.line=l
class SaySize(Node):
    def __init__(self,n,l): self.list_name=n;self.line=l

# File I/O
class WriteFileStmt(Node):
    def __init__(self,c,p,l): self.content=c;self.path=p;self.line=l
class AppendFileStmt(Node):
    def __init__(self,c,p,l): self.content=c;self.path=p;self.line=l
class DeleteFileStmt(Node):
    def __init__(self,p,l): self.path=p;self.line=l
class CreateFolderStmt(Node):
    def __init__(self,p,l): self.path=p;self.line=l
class SaveJsonStmt(Node):
    def __init__(self,e,p,l): self.expr=e;self.path=p;self.line=l
class CopyToClipboardStmt(Node):
    def __init__(self,e,l): self.expr=e;self.line=l

# GUI
class OpenWindowStmt(Node):
    def __init__(self,t,w,h,l): self.title=t;self.width=w;self.height=h;self.line=l
class ShowWindowStmt(Node):
    def __init__(self,l): self.line=l
class ShowPopupStmt(Node):
    def __init__(self,m,l): self.message=m;self.line=l
class AddLabelStmt(Node):
    def __init__(self,t,v,l): self.text=t;self.varname=v;self.line=l
class AddButtonStmt(Node):
    def __init__(self,t,a,l): self.text=t;self.action_name=a;self.line=l
class AddInputStmt(Node):
    def __init__(self,v,l): self.varname=v;self.line=l
class AddImageStmt(Node):
    def __init__(self,p,l): self.path=p;self.line=l
class SetLabelStmt(Node):
    def __init__(self,v,t,l): self.varname=v;self.text=t;self.line=l
class OpenCalculatorStmt(Node):
    def __init__(self,l): self.line=l
class OpenQuizBuilderStmt(Node):
    def __init__(self,l): self.line=l
class OpenQuizPlayerStmt(Node):
    def __init__(self,p,l): self.path=p; self.line=l
# Turtle / Motion
class TurtleStmt(Node):      # generic turtle command
    def __init__(self,cmd,args,l): self.cmd=cmd;self.args=args;self.line=l

# Sound
class PlaySoundStmt(Node):
    def __init__(self,path,l): self.path=path;self.line=l
class StopSoundStmt(Node):
    def __init__(self,l): self.line=l

# ─────────────────────────────────────────────────────────────────────
#  PARSER
# ─────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self,msg,line): super().__init__(f"Line {line}: {msg}"); self.line=line

class Parser:
    def __init__(self,tokens): self.tokens=tokens; self.pos=0

    def peek(self,off=0):
        i=self.pos+off
        return self.tokens[i] if i<len(self.tokens) else None

    def consume(self):
        t=self.tokens[self.pos]; self.pos+=1; return t

    def expect_period(self):
        if self.peek() and self.peek().type=="PERIOD": self.consume()

    def expect_word(self,*words):
        for w in words:
            t=self.peek()
            if not t or t.type!="WORD" or t.value.lower()!=w.lower():
                ln=t.line if t else "?"; got=repr(t.value) if t else "end of file"
                raise ParseError(f"Expected '{w}' but got {got}.",ln)
            self.consume()

    def peek_words(self,*words):
        for i,w in enumerate(words):
            t=self.peek(i)
            if not t or t.type!="WORD" or t.value.lower()!=w.lower(): return False
        return True

    def match_word(self,*words):
        saved=self.pos
        try: self.expect_word(*words); return True
        except: self.pos=saved; return False

    def current_line(self):
        t=self.peek(); return t.line if t else "?"

    # ── Top level ────────────────────────────────────────────────────

    def parse(self):
        stmts=[]
        while self.pos<len(self.tokens):
            s=self.parse_statement()
            if s: stmts.append(s)
        return Program(stmts)

    def parse_statement(self):
        t=self.peek()
        if not t: return None
        if t.type!="WORD": self.consume(); return None
        kw=t.value.lower(); line=t.line

        dispatch = {
            "note":    self.parse_note,
            "let":     self.parse_let,
            "set":     self.parse_set,
            "change":  self.parse_change_by,
            "say":     self.parse_say,
            "ask":     self.parse_ask,
            "if":      self.parse_if,
            "repeat":  self.parse_repeat,
            "keep":    self.parse_keep,
            "for":     self.parse_for,
            "define":  self.parse_define,
            "call":    self.parse_call_stmt,
            "run":     self.parse_call_stmt,
            "give":    self.parse_give_back,
            "add":     self.parse_add,
            "remove":  self.parse_remove,
            "insert":  self.parse_insert,
            "replace": self.parse_replace,
            "delete":  self.parse_delete,
            "sort":    self.parse_sort,
            "shuffle": self.parse_shuffle,
            "write":   self.parse_write_file,
            "append":  self.parse_append_file,
            "save":    self.parse_save_json,
            "copy":    self.parse_copy_clipboard,
            "create":  self.parse_create_folder,
            "open":    self.parse_open,
            "show":    self.parse_show,
            "display": self.parse_display_window,
            "launch":  self.parse_launch,
            "wait":    self.parse_wait,
            "stop":    self.parse_stop,
            "skip":    self.parse_skip,
            "try":     self.parse_try,
            # Turtle / Motion
            "move":    self.parse_turtle,
            "turn":    self.parse_turtle,
            "go":      self.parse_turtle,
            "draw":    self.parse_turtle,
            "stamp":   self.parse_turtle,
            "pen":     self.parse_turtle,
            "hide":    self.parse_turtle,
            "bounce":  self.parse_turtle,
            # Sound
            "play":    self.parse_play_sound,
        }
        if kw in dispatch:
            return dispatch[kw]()
        raise ParseError(f"I don't know what to do with '{t.value}' here.", line)

    # ── Core statements ──────────────────────────────────────────────

    def parse_note(self):
        note_line=self.peek().line if self.peek() else None
        self.consume()
        while self.peek() and self.peek().type!="PERIOD":
            if note_line and self.peek().line!=note_line: break
            self.consume()
        if self.peek() and self.peek().type=="PERIOD": self.consume()
        return NoteStmt()

    def parse_let(self):
        line=self.current_line(); self.consume()
        name=self.parse_identifier(); self.expect_word("be")
        expr=self.parse_expr(); self.expect_period()
        return LetStmt(name,expr,line)

    def parse_set(self):
        line=self.current_line(); self.consume()
        if self.peek_words("label"):
            self.consume(); varname=self.parse_identifier()
            self.expect_word("to"); text=self.parse_expr(); self.expect_period()
            return SetLabelStmt(varname,text,line)
        name=self.parse_identifier(); self.expect_word("to")
        expr=self.parse_expr(); self.expect_period()
        return SetStmt(name,expr,line)

    def parse_change_by(self):
        # change score by 10.
        line=self.current_line(); self.consume()
        name=self.parse_identifier(); self.expect_word("by")
        expr=self.parse_expr(); self.expect_period()
        return ChangeByStmt(name,expr,line)

    def parse_say(self):
        line=self.current_line(); self.consume()
        if self.peek_words("the","size","of"):
            self.consume();self.consume();self.consume()
            name=self.parse_identifier(); self.expect_period()
            return SaySize(name,line)
        exprs=[self.parse_expr()]
        while self.peek() and self.peek().type=="COMMA":
            self.consume(); exprs.append(self.parse_expr())
        self.expect_period()
        return SayStmt(exprs,line)

    def parse_ask(self):
        line=self.current_line(); self.consume()
        prompt=self.parse_primary(); self.expect_word("and","store","it","in")
        name=self.parse_identifier(); self.expect_period()
        return AskStmt(prompt,name,line)

    # ── Control ──────────────────────────────────────────────────────

    def parse_if(self):
        line=self.current_line(); self.consume()
        cond=self.parse_condition(); self.expect_word("then")
        then_block=self.parse_block(end_words=[["end","if"],["otherwise"]])
        else_block=[]
        if self.peek_words("otherwise"):
            self.consume()
            else_block=self.parse_block(end_words=[["end","if"]])
        if self.peek_words("end","if"): self.consume(); self.consume()
        self.expect_period()
        return IfStmt(cond,then_block,else_block,line)

    def parse_repeat(self):
        line=self.current_line(); self.consume()
        # "repeat with i from 1 to 10" — counted for-loop
        if self.peek_words("with"):
            self.consume()
            var=self.parse_identifier(); self.expect_word("from")
            start=self.parse_expr(); self.expect_word("to")
            end=self.parse_expr()
            step=Literal(1)
            if self.peek_words("by"): self.consume(); step=self.parse_expr()
            body=self.parse_block(end_words=[["end","repeat"]])
            self.expect_word("end","repeat"); self.expect_period()
            return ForRangeStmt(var,start,end,step,body,line)
        times=self.parse_primary(); self.expect_word("times")
        body=self.parse_block(end_words=[["end","repeat"]])
        self.expect_word("end","repeat"); self.expect_period()
        return RepeatStmt(times,body,line)

    def parse_keep(self):
        line=self.current_line(); self.consume()
        self.expect_word("doing","while")
        cond=self.parse_condition()
        body=self.parse_block(end_words=[["end","keep"]])
        self.expect_word("end","keep"); self.expect_period()
        return KeepDoingStmt(cond,body,line)

    def parse_for(self):
        line=self.current_line(); self.consume()
        self.expect_word("each"); var=self.parse_identifier(); self.expect_word("in")
        list_expr=self.parse_primary()
        body=self.parse_block(end_words=[["end","for"]])
        self.expect_word("end","for"); self.expect_period()
        return ForEachStmt(var,list_expr,body,line)

    def parse_wait(self):
        line=self.current_line(); self.consume()
        expr=self.parse_expr()
        if self.peek_words("seconds") or self.peek_words("second"): self.consume()
        self.expect_period()
        return WaitStmt(expr,line)

    def parse_stop(self):
        line=self.current_line(); self.consume()
        if self.peek_words("loop") or self.peek_words("repeating"):
            self.consume(); self.expect_period(); return BreakStmt(line)
        # "stop program" or just "stop."
        if self.peek_words("program") or self.peek_words("everything"):
            self.consume()
        self.expect_period(); return StopStmt(line)

    def parse_skip(self):
        line=self.current_line(); self.consume()
        if self.peek_words("to","next"): self.consume(); self.consume()
        self.expect_period(); return ContinueStmt(line)

    def parse_try(self):
        line=self.current_line(); self.consume()
        body=self.parse_block(end_words=[["if","error"],["end","try"]])
        error_var=None; rescue=[]
        if self.peek_words("if","error"):
            self.consume(); self.consume()
            if self.peek_words("store","it","in"):
                self.consume();self.consume();self.consume()
                error_var=self.parse_identifier()
            rescue=self.parse_block(end_words=[["end","try"]])
        if self.peek_words("end","try"): self.consume(); self.consume()
        self.expect_period()
        return TryStmt(body,error_var,rescue,line)

    # ── Functions ────────────────────────────────────────────────────

    def parse_define(self):
        line=self.current_line(); self.consume()
        name=self.parse_func_name(); params=[]
        if self.peek_words("with"):
            self.consume(); params.append(self.parse_identifier())
            while self.peek() and self.peek().type=="COMMA":
                self.consume(); params.append(self.parse_identifier())
        body=self.parse_block(end_words=[["end","define"]])
        self.expect_word("end","define"); self.expect_period()
        return DefineStmt(name,params,body,line)

    def parse_call_stmt(self):
        line=self.current_line(); self.consume()
        name=self.parse_func_name(); args=[]
        if self.peek_words("with"):
            self.consume(); args.append(self.parse_expr())
            while self.peek() and self.peek().type=="COMMA":
                self.consume(); args.append(self.parse_expr())
        self.expect_period(); return CallStmt(name,args,line)

    def parse_give_back(self):
        line=self.current_line(); self.consume()
        self.expect_word("back"); expr=self.parse_expr(); self.expect_period()
        return GiveBackStmt(expr,line)

    # ── Lists ────────────────────────────────────────────────────────

    def parse_add(self):
        line=self.current_line(); self.consume()
        # GUI additions
        if self.peek_words("label"):
            self.consume(); text=self.parse_expr()
            varname=None
            if self.peek_words("as"): self.consume(); varname=self.parse_identifier()
            self.expect_period(); return AddLabelStmt(text,varname,line)
        if self.peek_words("button"):
            self.consume(); text=self.parse_expr(); action=None
            if self.peek_words("that","calls"): self.consume();self.consume(); action=self.parse_func_name()
            self.expect_period(); return AddButtonStmt(text,action,line)
        if self.peek_words("input","as"):
            self.consume();self.consume(); varname=self.parse_identifier()
            self.expect_period(); return AddInputStmt(varname,line)
        if self.peek_words("image"):
            self.consume(); path=self.parse_expr(); self.expect_period()
            return AddImageStmt(path,line)
        # Normal list add
        expr=self.parse_primary(); self.expect_word("to")
        name=self.parse_identifier(); self.expect_period()
        return AddToList(expr,name,line)

    def parse_remove(self):
        line=self.current_line(); self.consume()
        expr=self.parse_primary(); self.expect_word("from")
        name=self.parse_identifier(); self.expect_period()
        return RemoveFromList(expr,name,line)

    def parse_insert(self):
        # insert "eggs" into groceries at 2.
        line=self.current_line(); self.consume()
        expr=self.parse_expr(); self.expect_word("into")
        name=self.parse_identifier(); self.expect_word("at")
        index=self.parse_expr(); self.expect_period()
        return InsertIntoList(expr,name,index,line)

    def parse_replace(self):
        # replace item 2 in myList with "eggs".
        line=self.current_line(); self.consume()
        self.expect_word("item"); index=self.parse_expr(); self.expect_word("in")
        name=self.parse_identifier(); self.expect_word("with")
        expr=self.parse_expr(); self.expect_period()
        return ReplaceInList(index,name,expr,line)

    def parse_delete(self):
        line=self.current_line(); self.consume()
        if self.peek_words("file"):
            self.consume(); path=self.parse_expr(); self.expect_period()
            return DeleteFileStmt(path,line)
        if self.peek_words("item"):
            self.consume(); index=self.parse_expr(); self.expect_word("from")
            name=self.parse_identifier(); self.expect_period()
            return DeleteItemFromList(index,name,line)
        if self.peek_words("folder"):
            self.consume(); path=self.parse_expr(); self.expect_period()
            return DeleteFileStmt(path,line)   # reuse, handled in exec
        raise ParseError("After 'delete' I expected 'file', 'folder', or 'item'.", line)

    def parse_sort(self):
        # sort myList.  /  sort myList in reverse.
        line=self.current_line(); self.consume()
        name=self.parse_identifier(); reverse=False
        if self.peek_words("in","reverse"): self.consume();self.consume(); reverse=True
        self.expect_period(); return SortListStmt(name,reverse,line)

    def parse_shuffle(self):
        line=self.current_line(); self.consume()
        name=self.parse_identifier(); self.expect_period()
        return ShuffleListStmt(name,line)

    # ── File I/O ─────────────────────────────────────────────────────

    def parse_write_file(self):
        line=self.current_line(); self.consume()
        content=self.parse_expr(); self.expect_word("to","file")
        path=self.parse_expr(); self.expect_period()
        return WriteFileStmt(content,path,line)

    def parse_append_file(self):
        line=self.current_line(); self.consume()
        content=self.parse_expr(); self.expect_word("to","file")
        path=self.parse_expr(); self.expect_period()
        return AppendFileStmt(content,path,line)

    def parse_save_json(self):
        # save data as json to file "out.json".
        line=self.current_line(); self.consume()
        expr=self.parse_expr(); self.expect_word("as","json","to","file")
        path=self.parse_expr(); self.expect_period()
        return SaveJsonStmt(expr,path,line)

    def parse_copy_clipboard(self):
        # copy X to clipboard.
        line=self.current_line(); self.consume()
        expr=self.parse_expr(); self.expect_word("to","clipboard")
        self.expect_period(); return CopyToClipboardStmt(expr,line)

    def parse_create_folder(self):
        line=self.current_line(); self.consume()
        self.expect_word("folder"); path=self.parse_expr(); self.expect_period()
        return CreateFolderStmt(path,line)

    # ── GUI ──────────────────────────────────────────────────────────

    def parse_open(self):
        line=self.current_line(); self.consume()
        self.expect_word("window","titled"); title=self.parse_expr()
        width=Literal(600); height=Literal(400)
        if self.peek_words("with","width"):
            self.consume();self.consume(); width=self.parse_primary()
            if self.peek() and self.peek().type=="COMMA":
                self.consume(); self.expect_word("height"); height=self.parse_primary()
        self.expect_period()
        return OpenWindowStmt(title,width,height,line)

    def parse_show(self):
        line=self.current_line(); self.consume()
        if self.peek_words("window"): self.consume(); self.expect_period(); return ShowWindowStmt(line)
        if self.peek_words("popup"):
            self.consume(); msg=self.parse_expr(); self.expect_period(); return ShowPopupStmt(msg,line)
        raise ParseError("After 'show' I expected 'window' or 'popup'.", line)

    def parse_display_window(self):
        line=self.current_line(); self.consume()
        self.expect_word("window"); self.expect_period(); return ShowWindowStmt(line)

    def parse_launch(self):
        line=self.current_line(); self.consume()
        if self.peek_words("calculator"):
            self.consume(); self.expect_period()
            return OpenCalculatorStmt(line)
        if self.peek_words("quiz","builder"):
            self.consume(); self.consume(); self.expect_period()
            return OpenQuizBuilderStmt(line)
        if self.peek_words("quiz"):
            self.consume()
            # optional: launch quiz "myquiz.json".
            if self.peek() and self.peek().type == "STRING":
                path = Literal(self.consume().value)
            else:
                path = Literal("")
            self.expect_period()
            return OpenQuizPlayerStmt(path, line)
        raise ParseError("After 'launch' I expected 'calculator', 'quiz builder', or 'quiz'.", line)

    # ── Turtle / Motion ──────────────────────────────────────────────

    def parse_turtle(self):
        """Parse all turtle/motion statements."""
        line=self.current_line(); kw=self.peek().value.lower(); self.consume()

        if kw=="move":
            # move forward 100.  /  move backward 50.
            if self.peek_words("forward") or self.peek_words("forwards"):
                self.consume(); dist=self.parse_expr(); self.expect_period()
                return TurtleStmt("forward",[dist],line)
            if self.peek_words("backward") or self.peek_words("backwards") or self.peek_words("back"):
                self.consume(); dist=self.parse_expr(); self.expect_period()
                return TurtleStmt("backward",[dist],line)
            dist=self.parse_expr(); self.expect_period()
            return TurtleStmt("forward",[dist],line)

        if kw=="turn":
            # turn right 90.  /  turn left 45.
            if self.peek_words("right"): self.consume(); deg=self.parse_expr(); self.expect_period(); return TurtleStmt("right",[deg],line)
            if self.peek_words("left"):  self.consume(); deg=self.parse_expr(); self.expect_period(); return TurtleStmt("left",[deg],line)
            deg=self.parse_expr(); self.expect_period(); return TurtleStmt("right",[deg],line)

        if kw=="go":
            # go to x 100, y 200.  /  go to center.  /  go home.
            if self.peek_words("home"): self.consume(); self.expect_period(); return TurtleStmt("home",[],line)
            if self.peek_words("to","center"): self.consume();self.consume(); self.expect_period(); return TurtleStmt("home",[],line)
            if self.peek_words("to"):
                self.consume()
                if self.peek_words("x"):
                    self.consume(); x=self.parse_expr()
                    if self.peek() and self.peek().type=="COMMA": self.consume()
                    self.expect_word("y"); y=self.parse_expr(); self.expect_period()
                    return TurtleStmt("goto",[x,y],line)
            self.expect_period(); return TurtleStmt("home",[],line)

        if kw=="draw":
            # draw circle 50.  /  draw dot.  /  draw square 100.
            if self.peek_words("circle"): self.consume(); r=self.parse_expr(); self.expect_period(); return TurtleStmt("circle",[r],line)
            if self.peek_words("dot"):    self.consume(); self.expect_period(); return TurtleStmt("dot",[],line)
            if self.peek_words("square"): self.consume(); s=self.parse_expr(); self.expect_period(); return TurtleStmt("square",[s],line)
            self.expect_period(); return TurtleStmt("dot",[],line)

        if kw=="stamp": self.expect_period(); return TurtleStmt("stamp",[],line)
        if kw=="hide":  self.expect_period(); return TurtleStmt("hideturtle",[],line)
        if kw=="bounce":self.expect_period(); return TurtleStmt("bounce",[],line)

        if kw=="pen":
            # pen down.  /  pen up.  /  pen color "red".  /  pen size 3.
            if self.peek_words("down"):  self.consume(); self.expect_period(); return TurtleStmt("pendown",[],line)
            if self.peek_words("up"):    self.consume(); self.expect_period(); return TurtleStmt("penup",[],line)
            if self.peek_words("color") or self.peek_words("colour"):
                self.consume(); c=self.parse_expr(); self.expect_period(); return TurtleStmt("pencolor",[c],line)
            if self.peek_words("size"):
                self.consume(); s=self.parse_expr(); self.expect_period(); return TurtleStmt("pensize",[s],line)
            self.expect_period(); return TurtleStmt("pendown",[],line)

        self.expect_period(); return TurtleStmt(kw,[],line)

    # ── Sound ────────────────────────────────────────────────────────

    def parse_play_sound(self):
        line=self.current_line(); self.consume()
        if self.peek_words("sound"):
            self.consume(); path=self.parse_expr(); self.expect_period()
            return PlaySoundStmt(path,line)
        # "play note X for Y beats" — future
        path=self.parse_expr(); self.expect_period()
        return PlaySoundStmt(path,line)

    # ── Block ────────────────────────────────────────────────────────

    def parse_block(self, end_words):
        stmts=[]
        while self.pos<len(self.tokens):
            for ew in end_words:
                if self.peek_words(*ew): return stmts
            s=self.parse_statement()
            if s and not isinstance(s, NoteStmt): stmts.append(s)
        return stmts

    # ── Expressions ──────────────────────────────────────────────────

    def parse_expr(self):
        # List literal
        if self.peek_words("a","list","of"):
            self.consume();self.consume();self.consume()
            items=[self.parse_primary()]
            while self.peek() and self.peek().type=="COMMA":
                self.consume(); items.append(self.parse_primary())
            return ListLiteral(items)
        # Empty list
        if self.peek_words("an","empty","list"):
            self.consume();self.consume();self.consume(); return ListLiteral([])
        # "the result of FUNC with ARGS"
        if self.peek_words("the","result","of"):
            self.consume();self.consume();self.consume()
            name=self.parse_func_name(); args=[]
            if self.peek_words("with"):
                self.consume(); args.append(self.parse_expr())
                while self.peek() and self.peek().type=="COMMA":
                    self.consume(); args.append(self.parse_expr())
            return ResultOf(CallStmt(name,args,self.current_line()))

        left=self.parse_primary()
        while True:
            if self.peek_words("plus"):
                self.consume(); left=BinOp("plus",left,self.parse_primary())
            elif self.peek_words("minus"):
                self.consume(); left=BinOp("minus",left,self.parse_primary())
            elif self.peek_words("times"):
                self.consume(); left=BinOp("times",left,self.parse_primary())
            elif self.peek_words("divided","by"):
                self.consume();self.consume(); left=BinOp("divided by",left,self.parse_primary())
            elif self.peek_words("modulo"):
                self.consume(); left=BinOp("modulo",left,self.parse_primary())
            elif self.peek_words("to","the","power","of"):
                self.consume();self.consume();self.consume();self.consume()
                left=BinOp("power",left,self.parse_primary())
            else: break
        return left

    def parse_primary(self):
        t=self.peek()
        if not t: raise ParseError("Expected a value but found end of file.","?")

        # ── List size (usable as expression) ─────────────────────
        if self.peek_words("the","size","of"):
            self.consume(); self.consume(); self.consume()
            return ResultOf(CallStmt("__len__",[self.parse_primary()],self.current_line()))

        # ── Math ──────────────────────────────────────────────────
        if self.peek_words("the","square","root","of"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__sqrt__",[self.parse_primary()],self.current_line()))
        if self.peek_words("the","absolute","value","of"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__abs__",[self.parse_primary()],self.current_line()))
        if self.peek_words("round"):
            self.consume(); operand=self.parse_primary()
            p0=self.peek(0);p1=self.peek(1);p2=self.peek(2);p3=self.peek(3)
            if (p0 and p0.type=="WORD" and p0.value.lower()=="to" and
                p1 and p1.type=="NUMBER" and
                p2 and p2.type=="WORD" and p2.value.lower()=="decimal" and
                p3 and p3.type=="WORD" and p3.value.lower()=="places"):
                self.consume(); places=self.parse_primary(); self.consume(); self.consume()
                return ResultOf(CallStmt("__round__",[operand,places],self.current_line()))
            return ResultOf(CallStmt("__round__",[operand,Literal(0)],self.current_line()))
        if self.peek_words("the","floor","of"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__floor__",[self.parse_primary()],self.current_line()))
        if self.peek_words("the","ceiling","of"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__ceil__",[self.parse_primary()],self.current_line()))
        if self.peek_words("the","minimum","of"):
            for _ in range(3): self.consume()
            a=self.parse_primary(); self.expect_word("and"); b=self.parse_primary()
            return ResultOf(CallStmt("__min__",[a,b],self.current_line()))
        if self.peek_words("the","maximum","of"):
            for _ in range(3): self.consume()
            a=self.parse_primary(); self.expect_word("and"); b=self.parse_primary()
            return ResultOf(CallStmt("__max__",[a,b],self.current_line()))
        if self.peek_words("sine","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__sin__",[self.parse_primary()],self.current_line()))
        if self.peek_words("cosine","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__cos__",[self.parse_primary()],self.current_line()))
        if self.peek_words("tangent","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__tan__",[self.parse_primary()],self.current_line()))
        if self.peek_words("log","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__log10__",[self.parse_primary()],self.current_line()))
        if self.peek_words("natural","log","of"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__ln__",[self.parse_primary()],self.current_line()))
        if self.peek_words("pi"): self.consume(); return Literal(math.pi)
        if self.peek_words("infinity"): self.consume(); return Literal(math.inf)

        # ── Strings ───────────────────────────────────────────────
        if self.peek_words("uppercase","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__upper__",[self.parse_primary()],self.current_line()))
        if self.peek_words("lowercase","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__lower__",[self.parse_primary()],self.current_line()))
        if self.peek_words("trimmed"):
            self.consume()
            return ResultOf(CallStmt("__trim__",[self.parse_primary()],self.current_line()))
        if self.peek_words("length","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__len__",[self.parse_primary()],self.current_line()))
        if self.peek_words("reverse","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__reverse__",[self.parse_primary()],self.current_line()))
        if self.peek_words("words","in"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__word_count__",[self.parse_primary()],self.current_line()))
        if self.peek_words("lines","in"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__line_count__",[self.parse_primary()],self.current_line()))
        if self.peek_words("repeat","text"):
            self.consume();self.consume(); text=self.parse_primary()
            self.expect_word("times"); times=self.parse_primary()
            return ResultOf(CallStmt("__repeat_text__",[text,times],self.current_line()))

        # ── List / string indexing (Scratch style) ────────────────
        if self.peek_words("item"):
            self.consume(); index=self.parse_primary(); self.expect_word("of")
            lst=self.parse_primary()
            return ResultOf(CallStmt("__item_of__",[index,lst],self.current_line()))
        if self.peek_words("letter"):
            self.consume(); index=self.parse_primary(); self.expect_word("of")
            s=self.parse_primary()
            return ResultOf(CallStmt("__letter_of__",[index,s],self.current_line()))
        if self.peek_words("last","item","of"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__last_item__",[self.parse_primary()],self.current_line()))
        if self.peek_words("first","item","of"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__first_item__",[self.parse_primary()],self.current_line()))
        if self.peek_words("position","of"):
            self.consume();self.consume(); needle=self.parse_primary()
            self.expect_word("in"); haystack=self.parse_primary()
            return ResultOf(CallStmt("__position_of__",[needle,haystack],self.current_line()))

        # ── Type conversion ───────────────────────────────────────
        if self.peek_words("number","from"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__to_number__",[self.parse_primary()],self.current_line()))
        if self.peek_words("text","from"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__to_text__",[self.parse_primary()],self.current_line()))
        if self.peek_words("type","of"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__type_of__",[self.parse_primary()],self.current_line()))

        # ── File system ───────────────────────────────────────────
        if self.peek_words("contents","of","file"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__read_file__",[self.parse_primary()],self.current_line()))
        if self.peek_words("file","exists"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__file_exists__",[self.parse_primary()],self.current_line()))
        if self.peek_words("folder","exists"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__folder_exists__",[self.parse_primary()],self.current_line()))
        if self.peek_words("files","in"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__list_files__",[self.parse_primary()],self.current_line()))
        if self.peek_words("folders","in"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__list_folders__",[self.parse_primary()],self.current_line()))
        if self.peek_words("current","folder"):
            self.consume();self.consume()
            return ResultOf(CallStmt("__cwd__",[],self.current_line()))
        if self.peek_words("size","of","file"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__file_size__",[self.parse_primary()],self.current_line()))

        # ── JSON ──────────────────────────────────────────────────
        if self.peek_words("json","from","file"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__load_json__",[self.parse_primary()],self.current_line()))
        if self.peek_words("json","text","from"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__to_json__",[self.parse_primary()],self.current_line()))

        # ── Network ───────────────────────────────────────────────
        if self.peek_words("contents","of","url"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__fetch_url__",[self.parse_primary()],self.current_line()))

        # ── Clipboard ─────────────────────────────────────────────
        if self.peek_words("clipboard"):
            self.consume()
            return ResultOf(CallStmt("__paste__",[],self.current_line()))

        # ── Random ───────────────────────────────────────────────
        if self.peek_words("a","random","number","between"):
            for _ in range(4): self.consume()
            a=self.parse_primary(); self.expect_word("and"); b=self.parse_primary()
            return ResultOf(CallStmt("__random_int__",[a,b],self.current_line()))
        if self.peek_words("a","random","decimal","between"):
            for _ in range(4): self.consume()
            a=self.parse_primary(); self.expect_word("and"); b=self.parse_primary()
            return ResultOf(CallStmt("__random_float__",[a,b],self.current_line()))
        if self.peek_words("a","random","choice","from"):
            for _ in range(4): self.consume()
            return ResultOf(CallStmt("__random_choice__",[self.parse_expr()],self.current_line()))

        # ── Date / time ───────────────────────────────────────────
        if self.peek_words("today"):   self.consume(); return ResultOf(CallStmt("__today__",[],self.current_line()))
        if self.peek_words("now"):     self.consume(); return ResultOf(CallStmt("__now__",[],self.current_line()))
        if self.peek_words("the","current","year"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__year__",[],self.current_line()))
        if self.peek_words("the","current","month"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__month__",[],self.current_line()))
        if self.peek_words("the","current","day"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__day__",[],self.current_line()))
        if self.peek_words("the","current","hour"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__hour__",[],self.current_line()))
        if self.peek_words("the","current","minute"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__minute__",[],self.current_line()))
        if self.peek_words("the","current","second"):
            for _ in range(3): self.consume()
            return ResultOf(CallStmt("__second__",[],self.current_line()))
        if self.peek_words("time","since","start"):
            self.consume();self.consume();self.consume()
            return ResultOf(CallStmt("__elapsed__",[],self.current_line()))

        # ── Literals and variable refs ────────────────────────────
        if t.type=="STRING": self.consume(); return Literal(t.value)
        if t.type=="NUMBER": self.consume(); return Literal(t.value)
        if t.type=="BOOL":   self.consume(); return Literal(t.value)
        if t.type=="WORD":   return VarRef(self.parse_identifier())

        raise ParseError(f"Unexpected token '{t.value}' while reading a value.", t.line)

    # ── Identifier / func name / condition ───────────────────────────

    def parse_identifier(self):
        STOP = {
            "be","to","then","and","or","not","with","in","from","of",
            "plus","minus","times","divided","modulo","is","otherwise",
            "end","give","back","while","each","store","it",
            "the","doing","size","list",
            "if","repeat","keep","for","define","call","run",
            "say","ask","set","let","add","remove","note",
            "write","append","open","show","display","as","that",
            "power","decimal","places","between","file","titled",
            "width","height","popup","window","label","button",
            "input","image","calls","sorted","reversed","at",
            "contains","starts","ends","by","item","into",
            "forward","backward","forwards","backwards","right","left",
            "up","down","home","center","circle","dot","square",
            "color","colour","pen",
            "infinity","pi",
            "loop","repeating","everything","clipboard","json",
            "folder","url","else","change","replace","insert",
            "delete","sort","shuffle","try","skip","wait",
            "move","turn","go","draw","stamp","hide","bounce",
            "launch","calculator","sound","play","stop",
        }
        t=self.peek()
        if not t or t.type!="WORD":
            ln=t.line if t else "?"; got=repr(t.value) if t else "end of file"
            raise ParseError(f"Expected a name but got {got}.",ln)
        parts=[]
        while self.peek() and self.peek().type=="WORD" and self.peek().value.lower() not in STOP:
            parts.append(self.consume().value)
        if not parts:
            raise ParseError(f"Expected a variable name but got '{t.value}'.",t.line)
        return " ".join(parts)

    def parse_func_name(self):
        STOP={"with","then","and","otherwise","end","give","back","while",
              "each","store","it","the","doing"}
        parts=[]
        while self.peek() and self.peek().type=="WORD" and self.peek().value.lower() not in STOP:
            parts.append(self.consume().value)
        if not parts: raise ParseError("Expected a function name.",self.current_line())
        return " ".join(parts)

    def parse_condition(self):
        left=self.parse_comparison()
        while True:
            if self.peek_words("and"): self.consume(); left=BinOp("and",left,self.parse_comparison())
            elif self.peek_words("or"): self.consume(); left=BinOp("or",left,self.parse_comparison())
            else: break
        return left

    def parse_comparison(self):
        if self.peek_words("not"): self.consume(); return UnaryOp("not",self.parse_comparison())
        left=self.parse_expr()
        if self.peek_words("is","greater","than","or","equal","to"):
            for _ in range(6): self.consume()
            return BinOp(">=",left,self.parse_expr())
        if self.peek_words("is","less","than","or","equal","to"):
            for _ in range(6): self.consume()
            return BinOp("<=",left,self.parse_expr())
        if self.peek_words("is","greater","than"):
            for _ in range(3): self.consume()
            return BinOp(">",left,self.parse_expr())
        if self.peek_words("is","less","than"):
            for _ in range(3): self.consume()
            return BinOp("<",left,self.parse_expr())
        if self.peek_words("contains"):
            self.consume(); return BinOp("contains",left,self.parse_expr())
        if self.peek_words("starts","with"):
            self.consume();self.consume(); return BinOp("starts with",left,self.parse_expr())
        if self.peek_words("ends","with"):
            self.consume();self.consume(); return BinOp("ends with",left,self.parse_expr())
        if self.peek_words("is","not"):
            self.consume();self.consume(); return BinOp("!=",left,self.parse_expr())
        if self.peek_words("is","a","number"):
            self.consume();self.consume();self.consume(); return BinOp("is_a","number",left)
        if self.peek_words("is","a","list"):
            self.consume();self.consume();self.consume(); return BinOp("is_a","list",left)
        if self.peek_words("is","a","text"):
            self.consume();self.consume();self.consume(); return BinOp("is_a","text",left)
        if self.peek_words("is"):
            self.consume(); return BinOp("==",left,self.parse_expr())
        return left

# ─────────────────────────────────────────────────────────────────────
#  BUILT-IN FUNCTION TABLE
# ─────────────────────────────────────────────────────────────────────

_START_TIME = _time.time()

def _fsn_builtin(name, args, line):
    """Returns (value, handled)."""
    a=args

    # Math
    if name=="__sqrt__":
        if a[0]<0: raise RuntimeError_(f"Can't take square root of a negative number.",line)
        return math.sqrt(a[0]),True
    if name=="__abs__":    return abs(a[0]),True
    if name=="__round__":
        places=int(a[1]) if len(a)>1 else 0
        r=round(a[0],places); return (int(r) if places==0 else r),True
    if name=="__floor__":  return math.floor(a[0]),True
    if name=="__ceil__":   return math.ceil(a[0]),True
    if name=="__min__":    return min(a[0],a[1]),True
    if name=="__max__":    return max(a[0],a[1]),True
    if name=="__sin__":    return math.sin(math.radians(a[0])),True
    if name=="__cos__":    return math.cos(math.radians(a[0])),True
    if name=="__tan__":    return math.tan(math.radians(a[0])),True
    if name=="__log10__":  return math.log10(a[0]),True
    if name=="__ln__":     return math.log(a[0]),True

    # Strings
    if name=="__upper__":  return str(a[0]).upper(),True
    if name=="__lower__":  return str(a[0]).lower(),True
    if name=="__trim__":   return str(a[0]).strip(),True
    if name=="__len__":    return (len(a[0]) if isinstance(a[0],list) else len(str(a[0]))),True
    if name=="__reverse__":return (list(reversed(a[0])) if isinstance(a[0],list) else str(a[0])[::-1]),True
    if name=="__word_count__": return len(str(a[0]).split()),True
    if name=="__line_count__": return len(str(a[0]).splitlines()),True
    if name=="__repeat_text__":return str(a[0])*int(a[1]),True
    if name=="__replace__":    return str(a[0]).replace(str(a[1]),str(a[2])),True
    if name=="__split__":
        sep=str(a[1]) if len(a)>1 else " "; return str(a[0]).split(sep),True
    if name=="__join__":
        sep=str(a[1]) if len(a)>1 else ""; return sep.join(str(x) for x in a[0]),True
    if name=="__index_of__":
        try:    return str(a[0]).index(str(a[1])),True
        except: return -1,True
    if name=="__substring__":  return str(a[0])[int(a[1]):int(a[2])],True

    # Type conversion
    if name=="__to_number__":
        v=str(a[0]).strip()
        try:    return int(v),True
        except:
            try:    return float(v),True
            except: raise RuntimeError_(f"I can't turn '{a[0]}' into a number.",line)
    if name=="__to_text__":
        v=a[0]
        if isinstance(v,bool): return ("true" if v else "false"),True
        if isinstance(v,float) and v==int(v): return str(int(v)),True
        if isinstance(v,list): return ", ".join(str(x) for x in v),True
        return str(v),True
    if name=="__type_of__":
        v=a[0]
        if isinstance(v,bool): return "boolean",True
        if isinstance(v,int) or isinstance(v,float): return "number",True
        if isinstance(v,str): return "text",True
        if isinstance(v,list): return "list",True
        return "unknown",True

    # List operations (Scratch style)
    if name=="__item_of__":
        idx=int(a[0]); lst=a[1]
        if isinstance(lst,list):
            if idx<1 or idx>len(lst): raise RuntimeError_(f"Item {idx} is out of range.",line)
            return lst[idx-1],True
        elif isinstance(lst,str):
            if idx<1 or idx>len(lst): raise RuntimeError_(f"Letter {idx} is out of range.",line)
            return lst[idx-1],True
        raise RuntimeError_(f"Can't get an item from that.",line)
    if name=="__letter_of__":
        idx=int(a[0]); s=str(a[1])
        if idx<1 or idx>len(s): raise RuntimeError_(f"Letter {idx} is out of range.",line)
        return s[idx-1],True
    if name=="__last_item__":
        lst=a[0]
        if isinstance(lst,(list,str)) and len(lst)>0: return lst[-1],True
        raise RuntimeError_("The list is empty.",line)
    if name=="__first_item__":
        lst=a[0]
        if isinstance(lst,(list,str)) and len(lst)>0: return lst[0],True
        raise RuntimeError_("The list is empty.",line)
    if name=="__position_of__":
        needle=a[0]; hay=a[1]
        if isinstance(hay,list):
            try:    return hay.index(needle)+1,True
            except: return 0,True
        elif isinstance(hay,str):
            idx=hay.find(str(needle)); return (idx+1 if idx>=0 else 0),True
        return 0,True

    # File system
    if name=="__read_file__":
        try:
            with open(str(a[0]),"r",encoding="utf-8") as f: return f.read(),True
        except FileNotFoundError: raise RuntimeError_(f"I can't find the file '{a[0]}'.",line)
        except Exception as e: raise RuntimeError_(f"Problem reading '{a[0]}': {e}",line)
    if name=="__file_exists__":  return os.path.isfile(str(a[0])),True
    if name=="__folder_exists__":return os.path.isdir(str(a[0])),True
    if name=="__list_files__":
        try:    return [f for f in os.listdir(str(a[0])) if os.path.isfile(os.path.join(str(a[0]),f))],True
        except: return [],True
    if name=="__list_folders__":
        try:    return [f for f in os.listdir(str(a[0])) if os.path.isdir(os.path.join(str(a[0]),f))],True
        except: return [],True
    if name=="__cwd__":    return os.getcwd(),True
    if name=="__file_size__":
        try:    return os.path.getsize(str(a[0])),True
        except: raise RuntimeError_(f"Can't get size of '{a[0]}'.",line)

    # JSON
    if name=="__load_json__":
        import json
        try:
            with open(str(a[0]),"r",encoding="utf-8") as f: return json.load(f),True
        except Exception as e: raise RuntimeError_(f"Problem loading JSON from '{a[0]}': {e}",line)
    if name=="__to_json__":
        import json
        try:    return json.dumps(a[0],indent=2),True
        except: return str(a[0]),True

    # Network
    if name=="__fetch_url__":
        try:
            import urllib.request
            with urllib.request.urlopen(str(a[0]),timeout=10) as r:
                return r.read().decode("utf-8","replace"),True
        except Exception as e: raise RuntimeError_(f"Couldn't fetch '{a[0]}': {e}",line)

    # Clipboard
    if name=="__paste__":
        try:
            import tkinter as tk
            r=tk.Tk(); r.withdraw()
            val=r.clipboard_get(); r.destroy(); return val,True
        except: return "",True

    # Random
    if name=="__random_int__":    return random.randint(int(a[0]),int(a[1])),True
    if name=="__random_float__":  return random.uniform(float(a[0]),float(a[1])),True
    if name=="__random_choice__":
        lst=a[0]
        if not isinstance(lst,list) or len(lst)==0:
            raise RuntimeError_("Can't pick from an empty list.",line)
        return random.choice(lst),True

    # Date / time
    if name=="__today__":   return datetime.date.today().strftime("%Y-%m-%d"),True
    if name=="__now__":     return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),True
    if name=="__year__":    return datetime.datetime.now().year,True
    if name=="__month__":   return datetime.datetime.now().month,True
    if name=="__day__":     return datetime.datetime.now().day,True
    if name=="__hour__":    return datetime.datetime.now().hour,True
    if name=="__minute__":  return datetime.datetime.now().minute,True
    if name=="__second__":  return datetime.datetime.now().second,True
    if name=="__elapsed__": return round(_time.time()-_START_TIME,3),True

    return None,False

# ─────────────────────────────────────────────────────────────────────
#  INTERPRETER
# ─────────────────────────────────────────────────────────────────────

class ReturnException(Exception):
    def __init__(self,v): self.value=v

class BreakException(Exception): pass
class ContinueException(Exception): pass

class StopException(Exception): pass

class RuntimeError_(Exception):
    def __init__(self,msg,line):
        super().__init__(f"Line {line}: {msg}"); self.line=line; self.msg=msg

class Environment:
    def __init__(self,parent=None): self.vars={}; self.parent=parent
    def get(self,name):
        if name in self.vars: return self.vars[name]
        if self.parent: return self.parent.get(name)
        raise KeyError(name)
    def set(self,name,value): self.vars[name]=value
    def assign(self,name,value):
        if name in self.vars: self.vars[name]=value
        elif self.parent and self._in_parent(name): self.parent.assign(name,value)
        else: self.vars[name]=value
    def _in_parent(self,name):
        e=self.parent
        while e:
            if name in e.vars: return True
            e=e.parent
        return False


class Interpreter:
    def __init__(self):
        self.global_env  = Environment()
        self.functions   = {}
        self._gui_root   = None
        self._gui_frame  = None
        self._gui_labels = {}
        self._gui_inputs = {}
        self._tk         = None
        self._turtle     = None   # turtle module ref
        self._turtle_scr = None   # turtle screen

    def run(self,program): self.exec_block(program.stmts, self.global_env)

    def exec_block(self,stmts,env):
        for s in stmts: self.exec(s,env)

    def exec(self,node,env):  # noqa: C901
        if isinstance(node,NoteStmt): return

        elif isinstance(node,LetStmt):
            env.set(node.name, self.eval(node.expr,env))

        elif isinstance(node,SetStmt):
            val=self.eval(node.expr,env)
            try: env.assign(node.name,val)
            except: raise RuntimeError_(f"I don't know '{node.name}'. Declare it with 'let' first.",node.line)

        elif isinstance(node,ChangeByStmt):
            try:
                cur=env.get(node.name)
                env.assign(node.name, cur+self.eval(node.expr,env))
            except KeyError:
                raise RuntimeError_(f"I don't know '{node.name}'. Declare it with 'let' first.",node.line)

        elif isinstance(node,SayStmt):
            print(" ".join(self.fsn_str(self.eval(e,env)) for e in node.exprs))

        elif isinstance(node,SaySize):
            try: val=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            print(len(val))

        elif isinstance(node,AskStmt):
            prompt=self.eval(node.prompt,env)
            val=input(str(prompt)+": ")
            try:    val=int(val)
            except:
                try: val=float(val)
                except: pass
            env.set(node.varname,val)

        elif isinstance(node,IfStmt):
            if self.eval(node.cond,env): self.exec_block(node.then_block,Environment(env))
            else:                        self.exec_block(node.else_block,Environment(env))

        elif isinstance(node,RepeatStmt):
            n=int(self.eval(node.times,env))
            for _ in range(n):
                try: self.exec_block(node.body,Environment(env))
                except BreakException: break
                except ContinueException: continue

        elif isinstance(node,ForRangeStmt):
            start=self.eval(node.start,env)
            end  =self.eval(node.end,env)
            step =self.eval(node.step,env)
            # inclusive range
            vals=[]
            v=start
            if step>0:
                while v<=end: vals.append(v); v+=step
            else:
                while v>=end: vals.append(v); v+=step
            for val in vals:
                inner=Environment(env); inner.set(node.var,val)
                try: self.exec_block(node.body,inner)
                except BreakException: break
                except ContinueException: continue

        elif isinstance(node,KeepDoingStmt):
            while self.eval(node.cond,env):
                try: self.exec_block(node.body,Environment(env))
                except BreakException: break
                except ContinueException: continue

        elif isinstance(node,ForEachStmt):
            lst=self.eval(node.list_expr,env)
            for item in lst:
                inner=Environment(env); inner.set(node.var,item)
                try: self.exec_block(node.body,inner)
                except BreakException: break
                except ContinueException: continue

        elif isinstance(node,WaitStmt):
            _time.sleep(float(self.eval(node.expr,env)))

        elif isinstance(node,StopStmt):
            raise StopException()

        elif isinstance(node,BreakStmt):
            raise BreakException()

        elif isinstance(node,ContinueStmt):
            raise ContinueException()

        elif isinstance(node,TryStmt):
            try:
                self.exec_block(node.body,Environment(env))
            except (RuntimeError_,StopException,Exception) as e:
                if node.error_var:
                    msg=e.msg if hasattr(e,"msg") else str(e)
                    env.set(node.error_var,msg)
                self.exec_block(node.rescue,Environment(env))

        elif isinstance(node,DefineStmt):
            self.functions[node.name]=node

        elif isinstance(node,CallStmt):
            self.call_function(node.name,node.args,env,node.line)

        elif isinstance(node,GiveBackStmt):
            raise ReturnException(self.eval(node.expr,env))

        # Lists
        elif isinstance(node,AddToList):
            val=self.eval(node.expr,env)
            try: lst=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            lst.append(val)

        elif isinstance(node,RemoveFromList):
            val=self.eval(node.expr,env)
            try: lst=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            try: lst.remove(val)
            except ValueError: raise RuntimeError_(f"'{val}' is not in the list.",node.line)

        elif isinstance(node,InsertIntoList):
            val=self.eval(node.expr,env); idx=int(self.eval(node.index,env))
            try: lst=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            lst.insert(idx-1,val)  # 1-based

        elif isinstance(node,ReplaceInList):
            idx=int(self.eval(node.index,env)); val=self.eval(node.expr,env)
            try: lst=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            if idx<1 or idx>len(lst): raise RuntimeError_(f"Item {idx} is out of range.",node.line)
            lst[idx-1]=val

        elif isinstance(node,DeleteItemFromList):
            idx=int(self.eval(node.index,env))
            try: lst=env.get(node.list_name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.list_name}'.",node.line)
            if idx<1 or idx>len(lst): raise RuntimeError_(f"Item {idx} is out of range.",node.line)
            lst.pop(idx-1)

        elif isinstance(node,SortListStmt):
            try: lst=env.get(node.name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.name}'.",node.line)
            lst.sort(reverse=node.reverse)

        elif isinstance(node,ShuffleListStmt):
            try: lst=env.get(node.name)
            except KeyError: raise RuntimeError_(f"I don't know '{node.name}'.",node.line)
            random.shuffle(lst)

        # File I/O
        elif isinstance(node,WriteFileStmt):
            content=str(self.eval(node.content,env)); path=str(self.eval(node.path,env))
            try:
                with open(path,"w",encoding="utf-8") as f: f.write(content)
            except Exception as e: raise RuntimeError_(f"Problem writing to '{path}': {e}",node.line)

        elif isinstance(node,AppendFileStmt):
            content=str(self.eval(node.content,env)); path=str(self.eval(node.path,env))
            try:
                with open(path,"a",encoding="utf-8") as f: f.write(content+"\n")
            except Exception as e: raise RuntimeError_(f"Problem appending to '{path}': {e}",node.line)

        elif isinstance(node,DeleteFileStmt):
            path=str(self.eval(node.path,env))
            try:
                if os.path.isdir(path):
                    import shutil; shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e: raise RuntimeError_(f"Problem deleting '{path}': {e}",node.line)

        elif isinstance(node,CreateFolderStmt):
            path=str(self.eval(node.path,env))
            try: os.makedirs(path,exist_ok=True)
            except Exception as e: raise RuntimeError_(f"Problem creating folder '{path}': {e}",node.line)

        elif isinstance(node,SaveJsonStmt):
            import json
            val=self.eval(node.expr,env); path=str(self.eval(node.path,env))
            try:
                with open(path,"w",encoding="utf-8") as f: json.dump(val,f,indent=2)
            except Exception as e: raise RuntimeError_(f"Problem saving JSON to '{path}': {e}",node.line)

        elif isinstance(node,CopyToClipboardStmt):
            text=str(self.eval(node.expr,env))
            try:
                import tkinter as tk
                r=tk.Tk(); r.withdraw(); r.clipboard_clear()
                r.clipboard_append(text); r.update(); r.after(500,r.destroy); r.mainloop()
            except: print(f"[Clipboard] {text}")

        # GUI
        elif isinstance(node,OpenWindowStmt):
            self._gui_open(str(self.eval(node.title,env)),int(self.eval(node.width,env)),int(self.eval(node.height,env)),node.line)
        elif isinstance(node,AddLabelStmt):
            self._gui_add_label(str(self.eval(node.text,env)),node.varname,env,node.line)
        elif isinstance(node,AddButtonStmt):
            self._gui_add_button(str(self.eval(node.text,env)),node.action_name,env,node.line)
        elif isinstance(node,AddInputStmt):
            self._gui_add_input(node.varname,env,node.line)
        elif isinstance(node,AddImageStmt):
            self._gui_add_image(str(self.eval(node.path,env)),node.line)
        elif isinstance(node,ShowPopupStmt):
            self._gui_popup(str(self.eval(node.message,env)),node.line)
        elif isinstance(node,ShowWindowStmt):
            self._gui_show(node.line)
        elif isinstance(node,SetLabelStmt):
            self._gui_set_label(node.varname,str(self.eval(node.text,env)),node.line)
        elif isinstance(node,OpenCalculatorStmt):
            self._launch_calculator(node.line)
        elif isinstance(node,OpenQuizBuilderStmt):
            self._launch_quiz_builder(node.line)
        elif isinstance(node,OpenQuizPlayerStmt):
            path = self.eval(node.path, env) if not isinstance(node.path, Literal) else node.path.value
            self._launch_quiz_player(str(path), node.line)

        # Turtle
        elif isinstance(node,TurtleStmt):
            args=[self.eval(a,env) for a in node.args]
            self._turtle_cmd(node.cmd,args,node.line)

        # Sound
        elif isinstance(node,PlaySoundStmt):
            path=str(self.eval(node.path,env))
            self._play_sound(path,node.line)

    # ── Call / Eval ──────────────────────────────────────────────────

    def call_function(self,name,arg_exprs,env,line):
        args=[self.eval(a,env) for a in arg_exprs]
        result,handled=_fsn_builtin(name,args,line)
        if handled: return result
        if name not in self.functions:
            raise RuntimeError_(f"I don't know a function called '{name}'.",line)
        func=self.functions[name]
        if len(args)!=len(func.params):
            raise RuntimeError_(f"'{name}' needs {len(func.params)} input(s) but got {len(args)}.",line)
        inner=Environment(self.global_env)
        for p,v in zip(func.params,args): inner.set(p,v)
        try: self.exec_block(func.body,inner)
        except ReturnException as r: return r.value
        return None

    def eval(self,node,env):
        if isinstance(node,Literal):     return node.value
        if isinstance(node,VarRef):
            try:    return env.get(node.name)
            except: raise RuntimeError_(f"I don't know what '{node.name}' is. Did you declare it?",0)
        if isinstance(node,ListLiteral): return [self.eval(i,env) for i in node.items]
        if isinstance(node,ResultOf):
            call=node.call
            r=self.call_function(call.name,call.args,env,call.line)
            if r is None: raise RuntimeError_(f"'{call.name}' does not give back a value.",call.line)
            return r
        if isinstance(node,BinOp):
            # Short-circuit logic
            if node.op=="and": return bool(self.eval(node.left,env)) and bool(self.eval(node.right,env))
            if node.op=="or":  return bool(self.eval(node.left,env)) or  bool(self.eval(node.right,env))
            # Type checks
            if node.op=="is_a":
                v=self.eval(node.right,env)
                t=node.left  # the type name string
                if t=="number": return isinstance(v,(int,float)) and not isinstance(v,bool)
                if t=="list":   return isinstance(v,list)
                if t=="text":   return isinstance(v,str)
                return False
            l=self.eval(node.left,env); r=self.eval(node.right,env)
            if node.op=="plus":
                if isinstance(l,str) or isinstance(r,str): return str(l)+str(r)
                return l+r
            if node.op=="minus":        return l-r
            if node.op=="times":        return l*r
            if node.op=="divided by":
                if r==0: raise RuntimeError_("You can't divide by zero.",0)
                return l/r
            if node.op=="modulo":       return l%r
            if node.op=="power":        return l**r
            if node.op=="==":           return l==r
            if node.op=="!=":           return l!=r
            if node.op==">":            return l>r
            if node.op=="<":            return l<r
            if node.op==">=":           return l>=r
            if node.op=="<=":           return l<=r
            if node.op=="contains":     return str(r) in str(l)
            if node.op=="starts with":  return str(l).startswith(str(r))
            if node.op=="ends with":    return str(l).endswith(str(r))
        if isinstance(node,UnaryOp):
            if node.op=="not": return not bool(self.eval(node.operand,env))
        raise RuntimeError_("I don't know how to evaluate this expression.",0)

    def fsn_str(self,val):
        if isinstance(val,bool): return "true" if val else "false"
        if isinstance(val,float) and val==int(val): return str(int(val))
        if isinstance(val,list):  return "["+", ".join(self.fsn_str(v) for v in val)+"]"
        return str(val)

    # ── Turtle ───────────────────────────────────────────────────────

    def _get_turtle(self,line):
        if self._turtle is None:
            try:
                import turtle as _t
                self._turtle=_t
                _t.speed(0)
                _t.title("FSN Turtle")
            except ImportError:
                raise RuntimeError_("Turtle is not available on this system.",line)
        return self._turtle

    def _turtle_cmd(self,cmd,args,line):
        t=self._get_turtle(line)
        if   cmd=="forward":   t.forward(float(args[0]))
        elif cmd=="backward":  t.backward(float(args[0]))
        elif cmd=="right":     t.right(float(args[0]))
        elif cmd=="left":      t.left(float(args[0]))
        elif cmd=="goto":      t.goto(float(args[0]),float(args[1]))
        elif cmd=="home":      t.home()
        elif cmd=="circle":    t.circle(float(args[0]))
        elif cmd=="dot":       t.dot()
        elif cmd=="square":
            s=float(args[0])
            for _ in range(4): t.forward(s); t.right(90)
        elif cmd=="stamp":     t.stamp()
        elif cmd=="hideturtle":t.hideturtle()
        elif cmd=="pendown":   t.pendown()
        elif cmd=="penup":     t.penup()
        elif cmd=="pencolor":  t.pencolor(str(args[0]))
        elif cmd=="pensize":   t.pensize(float(args[0]))
        elif cmd=="bounce":
            x,y=t.xcor(),t.ycor()
            if abs(x)>300: t.setheading(180-t.heading())
            if abs(y)>300: t.setheading(-t.heading())
        try: t.getscreen().update()
        except: pass

    # ── Sound ────────────────────────────────────────────────────────

    def _play_sound(self,path,line):
        played=False
        # Try pygame first
        try:
            import pygame.mixer as mix
            if not mix.get_init(): mix.init()
            mix.music.load(path); mix.music.play(); played=True
        except: pass
        if not played:
            # Try playsound
            try:
                from playsound import playsound
                playsound(path,block=False); played=True
            except: pass
        if not played:
            # Windows winsound fallback
            try:
                import winsound
                winsound.PlaySound(path,winsound.SND_FILENAME|winsound.SND_ASYNC); played=True
            except: pass
        if not played:
            print(f"[Sound] Would play: {path} (no audio library found — install pygame or playsound)")

    # ── GUI ──────────────────────────────────────────────────────────

    def _require_gui(self,line):
        if self._gui_root is None:
            raise RuntimeError_('Open a window first: open window titled "My App".',line)

    def _gui_open(self,title,width,height,line):
        try:
            import tkinter as tk; self._tk=tk
        except ImportError:
            raise RuntimeError_("Tkinter is not available.",line)
        root=tk.Tk(); root.title(title); root.geometry(f"{width}x{height}")
        root.configure(bg="#f5f5f5")
        frame=tk.Frame(root,bg="#f5f5f5",padx=24,pady=20)
        frame.pack(fill=tk.BOTH,expand=True)
        self._gui_root=root; self._gui_frame=frame

    def _gui_add_label(self,text,varname,env,line):
        self._require_gui(line); tk=self._tk
        lbl=tk.Label(self._gui_frame,text=text,bg="#f5f5f5",font=("Segoe UI",12),anchor="w")
        lbl.pack(fill=tk.X,pady=3)
        if varname: self._gui_labels[varname]=lbl; env.set(varname,text)

    def _gui_add_button(self,text,action_name,env,line):
        self._require_gui(line); tk=self._tk; interp=self
        def on_click():
            for vname,entry in interp._gui_inputs.items():
                val=entry.get()
                try:    val=int(val)
                except:
                    try: val=float(val)
                    except: pass
                interp.global_env.set(vname,val)
            if action_name and action_name in interp.functions:
                try: interp.call_function(action_name,[],interp.global_env,line)
                except ReturnException: pass
                except RuntimeError_ as e: print(f"⚠  {e}")
        btn=tk.Button(self._gui_frame,text=text,command=on_click,
                      bg="#4a90d9",fg="white",font=("Segoe UI",11,"bold"),
                      relief="flat",padx=16,pady=7,cursor="hand2",
                      activebackground="#357abd",activeforeground="white")
        btn.pack(pady=6,anchor="w")

    def _gui_add_input(self,varname,env,line):
        self._require_gui(line); tk=self._tk
        entry=tk.Entry(self._gui_frame,font=("Segoe UI",12),relief="solid",bd=1)
        entry.pack(fill=tk.X,pady=4)
        self._gui_inputs[varname]=entry; env.set(varname,"")

    def _gui_add_image(self,path,line):
        self._require_gui(line); tk=self._tk
        try:
            img=tk.PhotoImage(file=path)
            lbl=tk.Label(self._gui_frame,image=img,bg="#f5f5f5")
            lbl.image=img; lbl.pack(pady=4)
        except Exception as e: raise RuntimeError_(f"Could not load image '{path}': {e}",line)

    def _gui_set_label(self,varname,text,line):
        self._require_gui(line)
        if varname not in self._gui_labels:
            raise RuntimeError_(f"I don't know a label called '{varname}'.",line)
        self._gui_labels[varname].config(text=text); self._gui_root.update()

    def _gui_popup(self,message,line):
        try:
            import tkinter.messagebox as mb
            if self._gui_root is None:
                import tkinter as tk; r=tk.Tk(); r.withdraw(); mb.showinfo("FSN",message); r.destroy()
            else: mb.showinfo("FSN",message)
        except: print(f"[Popup] {message}")

    def _gui_show(self,line):
        self._require_gui(line); self._gui_root.mainloop()

    # ── Calculator ───────────────────────────────────────────────────

    def _launch_calculator(self,line):
        try:
            import tkinter as tk
            import math as _math
        except ImportError:
            raise RuntimeError_("Tkinter is not available.",line)

        root=tk.Tk(); root.title("FSN Calculator"); root.resizable(False,False)
        root.configure(bg="#1e1e2e")
        BG="#1e1e2e"; DISP_BG="#13131f"; DISP_FG="#cdd6f4"
        BTN_NUM="#313244"; BTN_OP="#45475a"; BTN_ACTION="#fab387"
        BTN_SCI="#89b4fa"; BTN_MEM="#a6e3a1"; BTN_FG="#cdd6f4"
        BTN_HOV="#585b70"; ACCENT="#fab387"

        state={"expr":"","display":"0","just_equal":False,"memory":0,"error":False}
        disp_var=tk.StringVar(value="0"); expr_var=tk.StringVar(value="")

        disp_frame=tk.Frame(root,bg=DISP_BG,padx=16,pady=10)
        disp_frame.pack(fill=tk.X)
        tk.Label(disp_frame,textvariable=expr_var,bg=DISP_BG,fg="#585b70",
                 font=("Consolas",11),anchor="e").pack(fill=tk.X)
        tk.Label(disp_frame,textvariable=disp_var,bg=DISP_BG,fg=DISP_FG,
                 font=("Consolas",32,"bold"),anchor="e").pack(fill=tk.X)

        btn_container=tk.Frame(root,bg=BG); btn_container.pack(fill=tk.BOTH,expand=True,padx=6,pady=6)

        def upd(val,expr=""): disp_var.set(val); expr_var.set(expr)

        def safe_eval(s):
            c=s.replace("×","*").replace("÷","/").replace("^","**")
            for fn in ["sin","cos","tan","asin","acos","atan","log10","log","sqrt","abs"]:
                c=c.replace(fn,f"_math.{fn}")
            c=c.replace("_math.a_math.sin","_math.asin").replace("_math.a_math.cos","_math.acos").replace("_math.a_math.tan","_math.atan")
            try:
                # wrap trig in radians conversion
                return eval(c,{"__builtins__":{},"_math":_math})
            except: return None

        def press(val):
            s=state
            if s["error"]: s["expr"]=""; s["display"]="0"; s["error"]=False
            if val=="AC": s["expr"]=""; s["display"]="0"; s["just_equal"]=False; upd("0",""); return
            if val=="⌫":
                if s["display"] not in ("0","Error"):
                    s["display"]=s["display"][:-1] or "0"
                    if not s["just_equal"]: s["expr"]=s["expr"][:-1]
                upd(s["display"],s["expr"]); return
            if val=="=":
                if not s["expr"]: return
                expr_var.set(s["expr"]+" =")
                r=safe_eval(s["expr"])
                if r is None: s["display"]="Error"; s["error"]=True; upd("Error",s["expr"]+" =")
                else:
                    r=int(r) if isinstance(r,float) and r==int(r) else r
                    s["display"]=str(r); s["expr"]=str(r); upd(str(r),s["expr_orig"] if "expr_orig" in s else s["expr"]+" =")
                s["just_equal"]=True; return
            if val=="+/-":
                if s["display"] not in ("0","Error"):
                    s["display"]=s["display"][1:] if s["display"].startswith("-") else "-"+s["display"]
                upd(s["display"],s["expr"]); return
            if val=="%":
                r=safe_eval(s["expr"])
                if r is not None:
                    r/=100; s["display"]=str(int(r) if isinstance(r,float) and r==int(r) else r)
                    s["expr"]=s["display"]; upd(s["display"],s["expr"])
                return
            mem_ops={"MC":lambda:state.update({"memory":0}),"M+":lambda:state.update({"memory":state["memory"]+(safe_eval(s["expr"]) or 0)}),
                     "M-":lambda:state.update({"memory":state["memory"]-(safe_eval(s["expr"]) or 0)})}
            if val in mem_ops: mem_ops[val](); return
            if val=="MR":
                m=str(int(state["memory"]) if isinstance(state["memory"],float) and state["memory"]==int(state["memory"]) else state["memory"])
                s["expr"]=(s["expr"] or "")+m; s["display"]=m; s["just_equal"]=False; upd(m,s["expr"]); return
            sci_map={"sin":"sin(","cos":"cos(","tan":"tan(","sin⁻¹":"asin(","cos⁻¹":"acos(","tan⁻¹":"atan(",
                     "log":"log10(","ln":"log(","√":"sqrt(","x²":"**2","x³":"**3","xⁿ":"**","π":"pi","e":"e","10ˣ":"10**","eˣ":"e**"}
            if val in sci_map:
                tok=sci_map[val]
                if s["just_equal"] or s["display"]=="0": s["expr"]=tok
                else: s["expr"]+=tok
                s["display"]=tok.rstrip("("); s["just_equal"]=False; upd(s["display"],s["expr"]); return
            is_op=val in("+","-","×","÷","^","(",")")
            if s["just_equal"] and not is_op: s["expr"]=""; s["just_equal"]=False
            if val==".":
                if "." not in s["display"]: s["display"]+="."; s["expr"]+="."
            elif is_op:
                op_map={"×":"*","÷":"/","^":"**"}
                s["expr"]+=op_map.get(val,val); s["display"]=val; s["just_equal"]=False
            else:
                if s["display"]=="0" and val!=".":
                    s["display"]=val
                    s["expr"]=(s["expr"][:-1] if s["expr"] and s["expr"][-1]=="0" and len(s["expr"])==1 else s["expr"]+val) if s["expr"] else val
                else: s["display"]+=val; s["expr"]+=val
                s["just_equal"]=False
            upd(s["display"],s["expr"])

        def make_btn(parent,text,color,row,col):
            ia=color==BTN_ACTION
            def oe(e): btn.config(bg=ACCENT if ia else BTN_HOV)
            def ol(e): btn.config(bg=color)
            btn=tk.Button(parent,text=text,bg=color,fg=BTN_FG if not ia else "#1e1e2e",
                          font=("Consolas",13,"bold" if ia else "normal"),relief="flat",bd=0,
                          cursor="hand2",activebackground=BTN_HOV,command=lambda t=text:press(t))
            btn.grid(row=row,column=col,padx=3,pady=3,sticky="nsew",ipadx=0,ipady=10)
            btn.bind("<Enter>",oe); btn.bind("<Leave>",ol)

        bf=tk.Frame(btn_container,bg=BG); bf.pack(side=tk.LEFT,fill=tk.BOTH)
        for r,row in enumerate([
            [("AC",BTN_ACTION),("+/-",BTN_OP),("%",BTN_OP),("÷",BTN_ACTION)],
            [("7",BTN_NUM),("8",BTN_NUM),("9",BTN_NUM),("×",BTN_ACTION)],
            [("4",BTN_NUM),("5",BTN_NUM),("6",BTN_NUM),("-",BTN_ACTION)],
            [("1",BTN_NUM),("2",BTN_NUM),("3",BTN_NUM),("+",BTN_ACTION)],
            [("0",BTN_NUM),(".",BTN_NUM),("⌫",BTN_OP),("=",BTN_ACTION)],
        ]):
            bf.rowconfigure(r,weight=1)
            for c,(txt,col) in enumerate(row):
                bf.columnconfigure(c,weight=1); make_btn(bf,txt,col,r,c)

        sf=tk.Frame(btn_container,bg=BG); sf.pack(side=tk.LEFT,fill=tk.BOTH,padx=(4,0))
        for r,row in enumerate([
            [("MC",BTN_MEM),("MR",BTN_MEM),("M+",BTN_MEM),("M-",BTN_MEM)],
            [("sin",BTN_SCI),("cos",BTN_SCI),("tan",BTN_SCI),("π",BTN_SCI)],
            [("sin⁻¹",BTN_SCI),("cos⁻¹",BTN_SCI),("tan⁻¹",BTN_SCI),("e",BTN_SCI)],
            [("log",BTN_SCI),("ln",BTN_SCI),("√",BTN_SCI),("(",BTN_OP)],
            [("x²",BTN_SCI),("x³",BTN_SCI),("xⁿ",BTN_SCI),(")",BTN_OP)],
        ]):
            sf.rowconfigure(r,weight=1)
            for c,(txt,col) in enumerate(row):
                sf.columnconfigure(c,weight=1); make_btn(sf,txt,col,r,c)

        km={"Return":"=","KP_Enter":"=","BackSpace":"⌫","Delete":"AC","Escape":"AC",
            "plus":"+","minus":"-","asterisk":"×","slash":"÷","percent":"%","period":".","parenleft":"(","parenright":")"}
        for d in "0123456789": km[d]=d; km[f"KP_{d}"]=d
        root.bind("<Key>",lambda e: press(km[e.keysym]) if e.keysym in km else None)
        root.mainloop()

        root.bind("<Key>",lambda e: press(km[e.keysym]) if e.keysym in km else None)
        root.mainloop()

    # ── Quiz Builder ─────────────────────────────────────────────────

    def _launch_quiz_builder(self, line):
        try:
            import tkinter as tk
            from tkinter import ttk, filedialog, messagebox
            import json
        except ImportError:
            raise RuntimeError_("Tkinter is not available.", line)

        # ── Palette ──────────────────────────────────────────────
        BG       = "#1a1a2e"
        CARD     = "#16213e"
        ACCENT   = "#e94560"
        ACCENT2  = "#0f3460"
        SUCCESS  = "#4caf50"
        WARNING  = "#ff9800"
        TEXT     = "#eaeaea"
        SUBTEXT  = "#a0a0b0"
        ENTRY_BG = "#0d1b2a"
        BTN_FONT = ("Segoe UI", 11, "bold")
        LBL_FONT = ("Segoe UI", 11)
        HDR_FONT = ("Segoe UI", 18, "bold")

        # ── State ────────────────────────────────────────────────
        questions = []   # list of dicts
        current_edit = [None]  # index being edited, or None

        root = tk.Tk()
        root.title("FSN Quiz Builder")
        root.geometry("960x680")
        root.configure(bg=BG)
        root.minsize(800, 580)

        # ── Helpers ──────────────────────────────────────────────
        def make_btn(parent, text, cmd, color=ACCENT, fg=TEXT, width=None):
            cfg = dict(text=text, command=cmd, bg=color, fg=fg,
                       font=BTN_FONT, relief="flat", cursor="hand2",
                       padx=14, pady=8, activebackground=color, activeforeground=fg,
                       bd=0)
            if width: cfg["width"] = width
            b = tk.Button(parent, **cfg)
            def oe(e, b=b, c=color): b.config(bg=_darken(c))
            def ol(e, b=b, c=color): b.config(bg=c)
            b.bind("<Enter>", oe); b.bind("<Leave>", ol)
            return b

        def _darken(hex_color):
            r = int(hex_color[1:3],16); g = int(hex_color[3:5],16); b2 = int(hex_color[5:7],16)
            r = max(0,r-30); g = max(0,g-30); b2 = max(0,b2-30)
            return f"#{r:02x}{g:02x}{b2:02x}"

        def make_entry(parent, width=40, show=None):
            e = tk.Entry(parent, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                         font=LBL_FONT, relief="flat", bd=6, width=width)
            if show: e.config(show=show)
            return e

        def make_label(parent, text, font=None, fg=None, bg=None, anchor="w"):
            return tk.Label(parent, text=text,
                            font=font or LBL_FONT, fg=fg or TEXT,
                            bg=bg or BG, anchor=anchor)

        # ── Layout: left panel (question list) + right panel (editor) ──
        left = tk.Frame(root, bg=CARD, width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
        left.pack_propagate(False)

        right = tk.Frame(root, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ── Left: quiz meta + question list ──────────────────────
        tk.Label(left, text="📝  Quiz Builder", font=("Segoe UI",14,"bold"),
                 bg=CARD, fg=ACCENT).pack(pady=(16,4), padx=12, anchor="w")

        meta_frame = tk.Frame(left, bg=CARD)
        meta_frame.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(meta_frame, text="Quiz Title:", font=("Segoe UI",10), bg=CARD, fg=SUBTEXT).pack(anchor="w")
        title_var = tk.StringVar(value="My Quiz")
        title_entry = tk.Entry(meta_frame, textvariable=title_var, bg=ENTRY_BG, fg=TEXT,
                               font=("Segoe UI",11), relief="flat", bd=4)
        title_entry.pack(fill=tk.X, pady=(2,8))

        tk.Label(left, text="Questions", font=("Segoe UI",10,"bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", padx=12)

        list_frame = tk.Frame(left, bg=CARD)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        scrollbar = tk.Scrollbar(list_frame, bg=CARD, troughcolor=CARD)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        q_listbox = tk.Listbox(list_frame, bg=ENTRY_BG, fg=TEXT,
                               font=("Segoe UI",10), relief="flat", bd=0,
                               selectbackground=ACCENT, selectforeground=TEXT,
                               activestyle="none", yscrollcommand=scrollbar.set)
        q_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=q_listbox.yview)

        btn_row = tk.Frame(left, bg=CARD)
        btn_row.pack(fill=tk.X, padx=8, pady=(4,8))
        make_btn(btn_row, "+ New", lambda: new_question(), ACCENT).pack(side=tk.LEFT, padx=2)
        make_btn(btn_row, "🗑 Delete", lambda: delete_question(), "#c0392b").pack(side=tk.LEFT, padx=2)

        save_load_row = tk.Frame(left, bg=CARD)
        save_load_row.pack(fill=tk.X, padx=8, pady=(0,12))
        make_btn(save_load_row, "💾 Save", lambda: save_quiz(), SUCCESS).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        make_btn(save_load_row, "📂 Load", lambda: load_quiz(), ACCENT2).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # ── Right: question editor ────────────────────────────────
        tk.Label(right, text="Question Editor", font=HDR_FONT,
                 bg=BG, fg=TEXT).pack(anchor="w", pady=(0,12))

        editor = tk.Frame(right, bg=BG)
        editor.pack(fill=tk.BOTH, expand=True)

        # Question type
        type_row = tk.Frame(editor, bg=BG)
        type_row.pack(fill=tk.X, pady=(0,8))
        tk.Label(type_row, text="Type:", font=LBL_FONT, bg=BG, fg=SUBTEXT).pack(side=tk.LEFT, padx=(0,8))
        q_type = tk.StringVar(value="multiple")
        for val, label in [("multiple","Multiple Choice (A-D)"), ("truefalse","True / False")]:
            tk.Radiobutton(type_row, text=label, variable=q_type, value=val,
                           bg=BG, fg=TEXT, selectcolor=ACCENT2, activebackground=BG,
                           font=LBL_FONT, command=lambda: refresh_answer_area()).pack(side=tk.LEFT, padx=8)

        # Question text
        tk.Label(editor, text="Question:", font=LBL_FONT, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(4,2))
        q_text_entry = tk.Text(editor, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                               font=("Segoe UI",12), relief="flat", bd=6,
                               height=3, wrap=tk.WORD)
        q_text_entry.pack(fill=tk.X, pady=(0,10))

        # Answers area
        ans_frame = tk.Frame(editor, bg=BG)
        ans_frame.pack(fill=tk.X)

        correct_var = tk.StringVar(value="A")
        answer_entries = {}   # label -> Entry widget

        def refresh_answer_area():
            for w in ans_frame.winfo_children(): w.destroy()
            answer_entries.clear()
            if q_type.get() == "multiple":
                tk.Label(ans_frame, text="Answers (select the correct one):",
                         font=LBL_FONT, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(0,6))
                for opt in ["A","B","C","D"]:
                    row = tk.Frame(ans_frame, bg=BG)
                    row.pack(fill=tk.X, pady=3)
                    tk.Radiobutton(row, variable=correct_var, value=opt,
                                   bg=BG, selectcolor=SUCCESS, activebackground=BG).pack(side=tk.LEFT)
                    tk.Label(row, text=f"{opt}:", width=3, font=("Segoe UI",11,"bold"),
                             bg=BG, fg=ACCENT).pack(side=tk.LEFT)
                    e = tk.Entry(row, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                 font=LBL_FONT, relief="flat", bd=4)
                    e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4,0))
                    answer_entries[opt] = e
            else:
                tk.Label(ans_frame, text="Select the correct answer:",
                         font=LBL_FONT, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(0,8))
                for opt, label in [("True","✅  True"), ("False","❌  False")]:
                    row = tk.Frame(ans_frame, bg=BG)
                    row.pack(anchor="w", pady=4)
                    tk.Radiobutton(row, text=label, variable=correct_var, value=opt,
                                   bg=BG, fg=TEXT, selectcolor=SUCCESS, activebackground=BG,
                                   font=("Segoe UI",13)).pack(side=tk.LEFT, padx=8)
                correct_var.set("True")

        refresh_answer_area()

        # Save question button
        btn_area = tk.Frame(editor, bg=BG)
        btn_area.pack(fill=tk.X, pady=16)
        make_btn(btn_area, "✔  Save Question", lambda: save_current_question(), SUCCESS).pack(side=tk.LEFT)
        make_btn(btn_area, "✖  Clear", lambda: clear_editor(), "#555").pack(side=tk.LEFT, padx=8)

        status_var = tk.StringVar(value="")
        status_lbl = tk.Label(btn_area, textvariable=status_var,
                              font=("Segoe UI",10), bg=BG, fg=SUCCESS)
        status_lbl.pack(side=tk.LEFT, padx=12)

        # ── Logic ────────────────────────────────────────────────

        def refresh_list():
            q_listbox.delete(0, tk.END)
            for i, q in enumerate(questions):
                icon = "🔘" if q["type"] == "multiple" else "✅"
                preview = q["question"][:42] + "…" if len(q["question"]) > 42 else q["question"]
                q_listbox.insert(tk.END, f"  {i+1}. {icon} {preview}")

        def clear_editor():
            q_text_entry.delete("1.0", tk.END)
            for e in answer_entries.values(): e.delete(0, tk.END)
            correct_var.set("A" if q_type.get()=="multiple" else "True")
            current_edit[0] = None
            status_var.set("")

        def load_question_into_editor(idx):
            q = questions[idx]
            current_edit[0] = idx
            q_type.set(q["type"])
            refresh_answer_area()
            q_text_entry.delete("1.0", tk.END)
            q_text_entry.insert("1.0", q["question"])
            correct_var.set(q["correct"])
            if q["type"] == "multiple":
                for opt in ["A","B","C","D"]:
                    answer_entries[opt].delete(0, tk.END)
                    answer_entries[opt].insert(0, q["answers"].get(opt,""))
            status_var.set(f"Editing question {idx+1}")

        def on_list_select(evt):
            sel = q_listbox.curselection()
            if sel: load_question_into_editor(sel[0])

        q_listbox.bind("<<ListboxSelect>>", on_list_select)

        def new_question():
            clear_editor()
            q_type.set("multiple")
            refresh_answer_area()
            q_text_entry.focus_set()
            status_var.set("New question — fill in and save")

        def save_current_question():
            text = q_text_entry.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("Missing", "Please enter a question.", parent=root)
                return
            qtype = q_type.get()
            if qtype == "multiple":
                answers = {opt: answer_entries[opt].get().strip() for opt in ["A","B","C","D"]}
                if not all(answers.values()):
                    messagebox.showwarning("Missing", "Please fill in all four answer options.", parent=root)
                    return
                correct = correct_var.get()
            else:
                answers = {"True": "True", "False": "False"}
                correct = correct_var.get()

            q = {"type": qtype, "question": text, "answers": answers, "correct": correct}
            if current_edit[0] is not None:
                questions[current_edit[0]] = q
                status_var.set(f"✔ Question {current_edit[0]+1} updated")
            else:
                questions.append(q)
                current_edit[0] = len(questions) - 1
                status_var.set(f"✔ Question {len(questions)} added")
            refresh_list()
            q_listbox.selection_clear(0, tk.END)
            q_listbox.selection_set(current_edit[0])

        def delete_question():
            sel = q_listbox.curselection()
            if not sel:
                messagebox.showinfo("Select", "Select a question to delete.", parent=root)
                return
            idx = sel[0]
            if messagebox.askyesno("Delete", f"Delete question {idx+1}?", parent=root):
                questions.pop(idx)
                current_edit[0] = None
                clear_editor()
                refresh_list()
                status_var.set("Question deleted")

        def save_quiz():
            if not questions:
                messagebox.showwarning("Empty", "Add at least one question first.", parent=root)
                return
            path = filedialog.asksaveasfilename(
                parent=root, defaultextension=".json",
                filetypes=[("Quiz files","*.json"),("All files","*.*")],
                title="Save Quiz")
            if not path: return
            data = {"title": title_var.get(), "questions": questions}
            with open(path,"w",encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            status_var.set(f"✔ Saved: {os.path.basename(path)}")
            messagebox.showinfo("Saved", f"Quiz saved to:\n{path}", parent=root)

        def load_quiz():
            path = filedialog.askopenfilename(
                parent=root,
                filetypes=[("Quiz files","*.json"),("All files","*.*")],
                title="Load Quiz")
            if not path: return
            try:
                with open(path,"r",encoding="utf-8") as f:
                    data = json.load(f)
                questions.clear()
                questions.extend(data.get("questions",[]))
                title_var.set(data.get("title","My Quiz"))
                clear_editor()
                refresh_list()
                status_var.set(f"✔ Loaded: {os.path.basename(path)} ({len(questions)} questions)")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load quiz:\n{e}", parent=root)

        root.mainloop()

    # ── Quiz Player ──────────────────────────────────────────────────

    def _launch_quiz_player(self, path, line):
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            import json
        except ImportError:
            raise RuntimeError_("Tkinter is not available.", line)

        # Load quiz file
        if path:
            try:
                with open(path,"r",encoding="utf-8") as f:
                    quiz_data = json.load(f)
            except Exception as e:
                raise RuntimeError_(f"Could not load quiz '{path}': {e}", line)
        else:
            # Ask user to pick a file
            root_tmp = tk.Tk(); root_tmp.withdraw()
            path = filedialog.askopenfilename(
                filetypes=[("Quiz files","*.json"),("All files","*.*")],
                title="Open Quiz File")
            root_tmp.destroy()
            if not path: return
            try:
                with open(path,"r",encoding="utf-8") as f:
                    quiz_data = json.load(f)
            except Exception as e:
                raise RuntimeError_(f"Could not load quiz: {e}", line)

        questions = quiz_data.get("questions", [])
        title     = quiz_data.get("title", "Quiz")
        if not questions:
            raise RuntimeError_("The quiz file has no questions.", line)

        # ── Palette ──────────────────────────────────────────────
        BG      = "#1a1a2e"
        CARD    = "#16213e"
        ACCENT  = "#e94560"
        SUCCESS = "#4caf50"
        WRONG   = "#e74c3c"
        TEXT    = "#eaeaea"
        SUBTEXT = "#a0a0b0"
        YELLOW  = "#f0c040"

        # ── State ────────────────────────────────────────────────
        state = {"idx": 0, "score": 0, "answered": False,
                 "user_answers": [], "total": len(questions)}

        root = tk.Tk()
        root.title(f"FSN Quiz — {title}")
        root.geometry("720x540")
        root.configure(bg=BG)
        root.resizable(False, False)

        # ── Frames ───────────────────────────────────────────────
        # Header
        hdr = tk.Frame(root, bg=ACCENT, padx=20, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"🎯  {title}", font=("Segoe UI",16,"bold"),
                 bg=ACCENT, fg=TEXT).pack(side=tk.LEFT)
        progress_var = tk.StringVar(value="Question 1 of " + str(state["total"]))
        tk.Label(hdr, textvariable=progress_var, font=("Segoe UI",11),
                 bg=ACCENT, fg=TEXT).pack(side=tk.RIGHT)

        # Score bar
        score_frame = tk.Frame(root, bg=CARD, padx=20, pady=8)
        score_frame.pack(fill=tk.X)
        score_var = tk.StringVar(value="Score: 0")
        tk.Label(score_frame, textvariable=score_var, font=("Segoe UI",12,"bold"),
                 bg=CARD, fg=YELLOW).pack(side=tk.LEFT)

        # Question area
        q_card = tk.Frame(root, bg=CARD, padx=30, pady=20)
        q_card.pack(fill=tk.X, padx=20, pady=12)

        q_num_var = tk.StringVar()
        tk.Label(q_card, textvariable=q_num_var, font=("Segoe UI",10),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w")

        q_text_var = tk.StringVar()
        q_label = tk.Label(q_card, textvariable=q_text_var, font=("Segoe UI",14),
                           bg=CARD, fg=TEXT, wraplength=620, justify="left", anchor="w")
        q_label.pack(anchor="w", pady=(4,0))

        # Answer buttons area
        ans_frame = tk.Frame(root, bg=BG)
        ans_frame.pack(fill=tk.X, padx=20, pady=4)

        ans_buttons = []

        # Feedback label
        feedback_var = tk.StringVar()
        feedback_lbl = tk.Label(root, textvariable=feedback_var,
                                font=("Segoe UI",13,"bold"), bg=BG, fg=SUCCESS)
        feedback_lbl.pack(pady=8)

        # Next / Finish button
        nav_frame = tk.Frame(root, bg=BG)
        nav_frame.pack(pady=8)

        def load_question():
            # Clear old answer buttons
            for w in ans_frame.winfo_children(): w.destroy()
            ans_buttons.clear()
            feedback_var.set("")
            state["answered"] = False

            idx = state["idx"]
            q = questions[idx]
            q_num_var.set(f"Question {idx+1} of {state['total']}")
            q_text_var.set(q["question"])
            progress_var.set(f"Question {idx+1} of {state['total']}")

            def make_ans_btn(opt, label_text):
                full = f"  {opt}   {label_text}" if q["type"]=="multiple" else f"  {label_text}"
                btn = tk.Button(ans_frame, text=full, font=("Segoe UI",12),
                                bg=CARD, fg=TEXT, relief="flat", bd=0,
                                cursor="hand2", anchor="w", padx=16, pady=10,
                                activebackground="#1e2d50", activeforeground=TEXT,
                                command=lambda o=opt: answer(o))
                btn.pack(fill=tk.X, pady=3, ipady=2)
                ans_buttons.append((opt, btn))
                btn.bind("<Enter>", lambda e,b=btn: b.config(bg="#1e2d50"))
                btn.bind("<Leave>", lambda e,b=btn: b.config(bg=CARD))

            if q["type"] == "multiple":
                for opt in ["A","B","C","D"]:
                    make_ans_btn(opt, q["answers"].get(opt,""))
            else:
                make_ans_btn("True", "✅  True")
                make_ans_btn("False", "❌  False")

            # Update next button visibility
            for w in nav_frame.winfo_children(): w.destroy()

        def answer(chosen):
            if state["answered"]: return
            state["answered"] = True
            idx = state["idx"]
            q = questions[idx]
            correct = q["correct"]
            is_correct = chosen == correct

            if is_correct:
                state["score"] += 1
                feedback_var.set("✅  Correct!")
                feedback_lbl.config(fg=SUCCESS)
            else:
                if q["type"] == "multiple":
                    feedback_var.set(f"❌  Wrong — correct answer was {correct}: {q['answers'].get(correct,'')}")
                else:
                    feedback_var.set(f"❌  Wrong — correct answer was {correct}")
                feedback_lbl.config(fg=WRONG)

            state["user_answers"].append({"q": q["question"], "chosen": chosen,
                                          "correct": correct, "ok": is_correct})
            score_var.set(f"Score: {state['score']} / {idx+1}")

            # Highlight buttons
            for opt, btn in ans_buttons:
                if opt == correct:
                    btn.config(bg=SUCCESS, fg="#111", activebackground=SUCCESS)
                elif opt == chosen and not is_correct:
                    btn.config(bg=WRONG, fg=TEXT, activebackground=WRONG)

            # Show next/finish
            is_last = idx >= state["total"] - 1
            label = "🏁  See Results" if is_last else "Next  ▶"
            color = YELLOW if is_last else ACCENT
            tk.Button(nav_frame, text=label,
                      font=("Segoe UI",12,"bold"),
                      bg=color, fg="#111" if is_last else TEXT,
                      relief="flat", padx=20, pady=10, cursor="hand2",
                      command=show_results if is_last else next_question).pack()

        def next_question():
            state["idx"] += 1
            load_question()

        def show_results():
            # Clear everything
            for w in root.winfo_children(): w.destroy()

            score = state["score"]
            total = state["total"]
            pct   = round(score/total*100)

            if pct >= 80:   grade,color = "Excellent! 🏆", SUCCESS
            elif pct >= 60: grade,color = "Good Job! 👍", YELLOW
            elif pct >= 40: grade,color = "Keep Practising 📚", "#ff9800"
            else:           grade,color = "Better Luck Next Time 💪", WRONG

            # Header
            hdr2 = tk.Frame(root, bg=ACCENT, padx=20, pady=16)
            hdr2.pack(fill=tk.X)
            tk.Label(hdr2, text=f"🎯  {title} — Results",
                     font=("Segoe UI",16,"bold"), bg=ACCENT, fg=TEXT).pack()

            # Score card
            card = tk.Frame(root, bg=CARD, padx=30, pady=20)
            card.pack(fill=tk.X, padx=20, pady=12)
            tk.Label(card, text=f"{score} / {total}", font=("Segoe UI",40,"bold"),
                     bg=CARD, fg=color).pack()
            tk.Label(card, text=f"{pct}%  —  {grade}", font=("Segoe UI",14),
                     bg=CARD, fg=color).pack(pady=(4,0))

            # Scrollable summary
            tk.Label(root, text="Question Summary", font=("Segoe UI",12,"bold"),
                     bg=BG, fg=SUBTEXT).pack(anchor="w", padx=24, pady=(8,2))

            sum_outer = tk.Frame(root, bg=BG)
            sum_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,8))
            sum_scroll = tk.Scrollbar(sum_outer)
            sum_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            canvas = tk.Canvas(sum_outer, bg=BG, highlightthickness=0,
                               yscrollcommand=sum_scroll.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sum_scroll.config(command=canvas.yview)
            inner = tk.Frame(canvas, bg=BG)
            canvas.create_window((0,0), window=inner, anchor="nw")

            for i, ua in enumerate(state["user_answers"]):
                row_bg = "#1a2e1a" if ua["ok"] else "#2e1a1a"
                row = tk.Frame(inner, bg=row_bg, padx=12, pady=8)
                row.pack(fill=tk.X, pady=2)
                icon = "✅" if ua["ok"] else "❌"
                tk.Label(row, text=f"{icon}  Q{i+1}: {ua['q'][:60]}{'…' if len(ua['q'])>60 else ''}",
                         font=("Segoe UI",10), bg=row_bg, fg=TEXT, anchor="w").pack(anchor="w")
                if not ua["ok"]:
                    tk.Label(row, text=f"     Your answer: {ua['chosen']}  |  Correct: {ua['correct']}",
                             font=("Segoe UI",9), bg=row_bg, fg=SUBTEXT).pack(anchor="w")

            inner.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

            # Play again / close
            btn_row = tk.Frame(root, bg=BG)
            btn_row.pack(pady=10)

            def play_again():
                for w in root.winfo_children(): w.destroy()
                state.update({"idx":0,"score":0,"answered":False,"user_answers":[]})
                rebuild_ui()

            def rebuild_ui():
                nonlocal hdr, score_frame, q_card, ans_frame, feedback_lbl, nav_frame
                hdr = tk.Frame(root, bg=ACCENT, padx=20, pady=12); hdr.pack(fill=tk.X)
                tk.Label(hdr, text=f"🎯  {title}", font=("Segoe UI",16,"bold"), bg=ACCENT, fg=TEXT).pack(side=tk.LEFT)
                progress_var.set(f"Question 1 of {state['total']}")
                tk.Label(hdr, textvariable=progress_var, font=("Segoe UI",11), bg=ACCENT, fg=TEXT).pack(side=tk.RIGHT)
                score_frame = tk.Frame(root, bg=CARD, padx=20, pady=8); score_frame.pack(fill=tk.X)
                score_var.set("Score: 0")
                tk.Label(score_frame, textvariable=score_var, font=("Segoe UI",12,"bold"), bg=CARD, fg=YELLOW).pack(side=tk.LEFT)
                q_card = tk.Frame(root, bg=CARD, padx=30, pady=20); q_card.pack(fill=tk.X, padx=20, pady=12)
                tk.Label(q_card, textvariable=q_num_var, font=("Segoe UI",10), bg=CARD, fg=SUBTEXT).pack(anchor="w")
                tk.Label(q_card, textvariable=q_text_var, font=("Segoe UI",14), bg=CARD, fg=TEXT, wraplength=620, justify="left", anchor="w").pack(anchor="w", pady=(4,0))
                ans_frame = tk.Frame(root, bg=BG); ans_frame.pack(fill=tk.X, padx=20, pady=4)
                feedback_lbl = tk.Label(root, textvariable=feedback_var, font=("Segoe UI",13,"bold"), bg=BG, fg=SUCCESS); feedback_lbl.pack(pady=8)
                nav_frame = tk.Frame(root, bg=BG); nav_frame.pack(pady=8)
                load_question()

            tk.Button(btn_row, text="🔁  Play Again", font=("Segoe UI",11,"bold"),
                      bg=ACCENT, fg=TEXT, relief="flat", padx=16, pady=8,
                      cursor="hand2", command=play_again).pack(side=tk.LEFT, padx=8)
            tk.Button(btn_row, text="✖  Close", font=("Segoe UI",11),
                      bg="#333", fg=TEXT, relief="flat", padx=16, pady=8,
                      cursor="hand2", command=root.destroy).pack(side=tk.LEFT, padx=8)

        load_question()
        root.mainloop()

# ─────────────────────────────────────────────────────────────────────
#  RUNNER
# ─────────────────────────────────────────────────────────────────────

def run_source(source,filename="<input>"):
    try:
        tokens=tokenize(source); program=Parser(tokens).parse()
        interp=Interpreter(); interp.run(program)
    except ParseError   as e: print(f"\n⚠  Parse error in {filename}:\n   {e}\n")
    except RuntimeError_ as e: print(f"\n⚠  Runtime error in {filename}:\n   {e}\n")
    except StopException:      pass
    except ReturnException:    pass
    except KeyboardInterrupt:  print("\nProgram stopped.")

def run_repl():
    print("FSN - Freeform Sentence Notation v3.0  (type 'quit.' to exit)")
    print("────────────────────────────────────────────────────────────────")
    interp=Interpreter(); buffer=[]
    while True:
        try: line=input("  ... " if buffer else "fsn> ")
        except (EOFError,KeyboardInterrupt): print("\nBye."); break
        if line.strip().lower() in ("quit.","exit.","quit","exit"): print("Bye."); break
        buffer.append(line); full="\n".join(buffer)
        open_kw =sum(1 for l in buffer for kw in ["then","times","while","each"] if kw in l.lower().split())
        close_kw=sum(1 for l in buffer for kw in ["end if","end repeat","end keep","end for","end define","end try"] if kw in l.lower())
        if full.rstrip().endswith(".") and open_kw<=close_kw:
            try:
                tokens=tokenize(full); program=Parser(tokens).parse()
                interp.exec_block(program.stmts,interp.global_env)
            except ParseError    as e: print(f"⚠  {e}")
            except RuntimeError_  as e: print(f"⚠  {e}")
            except StopException:       print("Program stopped.")
            except ReturnException:     pass
            buffer=[]

def main():
    if len(sys.argv)<2: run_repl(); return
    path=sys.argv[1]
    if not path.endswith(".fsn"): print(f"Warning: '{path}' does not have the .fsn extension.")
    if not os.path.exists(path): print(f"Error: I can't find the file '{path}'."); sys.exit(1)
    with open(path,"r",encoding="utf-8",newline='') as f: source=f.read()
    run_source(source,filename=path)

if __name__=="__main__":
    main()
