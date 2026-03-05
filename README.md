# FSN — Freeform Sentence Notation

A programming language where code reads like plain English.
File extension: `.fsn`

---

## 🚀 Quick Start

```
python3 fsn.py hello.fsn       # Run a file
python3 fsn.py                 # Interactive REPL
```

---

## 📁 What's Included

```
fsn-language/
├── interpreter/
│   ├── fsn.py              ← The interpreter (Python 3.8+)
│   ├── samples.fsn         ← 5 sample programs
│   └── test_acceptance.fsn ← Acceptance test
│
└── fsn-vscode-extension/   ← VS Code extension
    ├── extension.js
    ├── package.json
    ├── language-configuration.json
    ├── fsn.py              ← Bundled interpreter copy
    ├── syntaxes/
    │   └── fsn.tmLanguage.json   ← Syntax highlighting
    └── snippets/
        └── fsn.json              ← Code snippets
```

---


## ⚙️ VS Code Settings

In VS Code settings (`Ctrl+,`), search for `fsn`:

| Setting | Default | Description |
|---|---|---|
| `fsn.pythonPath` | `python3` | Python interpreter to use |
| `fsn.interpreterPath` | *(bundled)* | Path to `fsn.py` (leave blank to use bundled) |

---

## ▶️ Running FSN Files in VS Code

- **Keyboard**: `Ctrl+F5` (Mac: `Cmd+F5`)
- **Title bar**: Click the ▶ play button when a `.fsn` file is open
- **Right-click**: "FSN: Run Current File"
- **Command Palette**: `Ctrl+Shift+P` → "FSN: Run Current File"
- **REPL**: `Ctrl+Shift+P` → "FSN: Open REPL"

---

## 📖 Language Reference

### Variables
```
let name be "Alice".
let age be 25.
let score be 98.6.
let active be true.
set age to 30.
```

### Arithmetic
```
let total be age plus 5.
let half be score divided by 2.
let area be width times height.
let diff be total minus 10.
let rem be total modulo 3.
```

### Output & Input
```
say "Hello, world.".
say "Your score is", score.
ask "What is your name" and store it in name.
```

### Conditionals
```
if age is greater than 18 then
  say "Adult.".
otherwise
  say "Minor.".
end if.
```
Comparisons: `is`, `is not`, `is greater than`, `is less than`,
`is greater than or equal to`, `is less than or equal to`

Logical: `and`, `or`, `not`

### Loops
```
repeat 5 times
  say "Hello.".
end repeat.

keep doing while count is less than 10
  set count to count plus 1.
end keep.

for each item in groceries
  say item.
end for.
```

### Lists
```
let groceries be a list of "apples", "bananas", "milk".
add "eggs" to groceries.
remove "bananas" from groceries.
say the size of groceries.
```

### Functions
```
define greet with name
  say "Hello", name.
end define.

call greet with "Alice".

define add two numbers with a, b
  give back a plus b.
end define.

let result be the result of add two numbers with 3, 4.
```

### Comments
```
note This is a comment and will not run.
```

---

## 💡 VS Code Features

- ✅ Syntax highlighting for all keywords, strings, numbers, booleans
- ✅ Code snippets (type `if`, `define`, `repeat`, `keep`, `let`, etc.)
- ✅ Auto-indent inside blocks
- ✅ Run button in editor title bar
- ✅ Integrated terminal output
- ✅ REPL mode
- ✅ Status bar "Run FSN" button when `.fsn` file is open
