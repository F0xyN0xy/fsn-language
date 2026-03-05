# FSN — Freeform Sentence Notation

**A programming language where code reads like plain English.**

```
let name be "Alice".
let age be 25.

if age is greater than or equal to 18 then
  say "Welcome,", name.
otherwise
  say "Sorry, you must be 18 or older.".
end if.
```

No brackets. No semicolons. No symbols. Just sentences.

---

## Features

- ✅ Syntax highlighting for all keywords, strings, numbers, and comments
- ✅ 40+ code snippets (type `if`, `define`, `window`, `random`, and more)
- ✅ Auto-indent inside blocks
- ✅ Run button in the editor title bar
- ✅ `Ctrl+F5` / `Cmd+F5` keybinding to run the current file
- ✅ Integrated terminal output
- ✅ REPL mode (interactive prompt)
- ✅ Status bar run button when a `.fsn` file is open

---

## Requirements

- **Python 3.8 or higher** must be installed on your system
- The FSN interpreter (`fsn.py`) is bundled with the extension — no separate install needed
- For GUI windows: Python's `tkinter` module (included with most Python installs)

---

## Running FSN Files

| Method | How |
|---|---|
| Keyboard | `Ctrl+F5` (Windows/Linux) or `Cmd+F5` (Mac) |
| Title bar | Click the ▶ button when a `.fsn` file is open |
| Right-click | "FSN: Run Current File" |
| Command Palette | `Ctrl+Shift+P` → "FSN: Run Current File" |
| REPL | `Ctrl+Shift+P` → "FSN: Open REPL" |

---

## Extension Settings

| Setting | Default | Description |
|---|---|---|
| `fsn.pythonPath` | `python3` | Python executable to use (e.g. `python`, `python3`, or a full path) |
| `fsn.interpreterPath` | *(bundled)* | Path to a custom `fsn.py`. Leave blank to use the bundled interpreter. |

**Tip for Windows users:** If `python3` doesn't work, set `fsn.pythonPath` to `python` or the full path like `C:\Python312\python.exe`.

---

## Language Reference

### Variables
```
let name be "Alice".
let score be 98.6.
let active be true.
set score to 100.
```

### Arithmetic
```
let total be price plus tax.
let area be width times height.
let half be total divided by 2.
let remainder be total modulo 3.
let cube be 3 to the power of 3.
```

### Output & Input
```
say "Hello,", name.
ask "What is your name" and store it in name.
```

### Conditionals
```
if age is greater than or equal to 18 then
  say "Adult.".
otherwise
  say "Minor.".
end if.
```
Comparisons: `is`, `is not`, `is greater than`, `is less than`,
`is greater than or equal to`, `is less than or equal to`,
`contains`, `starts with`, `ends with`

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
  say "Hello,", name.
end define.

call greet with "Alice".

define add numbers with a, b
  give back a plus b.
end define.

let result be the result of add numbers with 10, 5.
```

### Math
```
let x be the square root of 144.
let y be the absolute value of -42.
let z be round 3.14159 to 2 decimal places.
let lo be the floor of 4.9.
let hi be the ceiling of 4.1.
let small be the minimum of 3 and 7.
let big be the maximum of 3 and 7.
```

### Strings
```
let loud be uppercase of name.
let quiet be lowercase of name.
let clean be trimmed "  hello  ".
let size be length of name.
let flipped be reverse of "FSN".
let joined be "Hello " plus name.
let n be number from "42".
let t be text from 99.
```

### File I/O
```
write "Hello!" to file "notes.txt".
append "More text." to file "notes.txt".
let data be contents of file "notes.txt".
```

### Random
```
let dice be a random number between 1 and 6.
let pct be a random decimal between 0 and 1.
let pick be a random choice from myList.
```

### Date & Time
```
say today.
say now.
say the current year.
say the current month.
say the current day.
say the current hour.
say the current minute.
```

### GUI Windows
```
open window titled "My App" with width 600, height 400.
add label "Enter your name:".
add input as userName.
add button "Say Hello" that calls onGreet.
add label "" as output.

define onGreet
  set label output to "Hello, " plus userName plus "!".
end define.

show window.
```

### Comments
```
note This is a comment and will not run.
```

---

## Updating the Extension

1. Replace `fsn.py` in the extension folder with the new version
2. Bump the `version` field in `package.json` (e.g. `"1.0.0"` → `"1.1.0"`)
3. Run `vsce package` to build a new `.vsix`
4. In VS Code: `Ctrl+Shift+P` → **"Extensions: Install from VSIX..."** → select the new file
5. Reload VS Code when prompted

The old version is automatically replaced.

---

## Known Limitations

- GUI windows use Python's built-in `tkinter`. PNG images are supported natively; JPEG requires the `Pillow` library (`pip install Pillow`).
- FSN is an interpreted language — there is no compilation step.
- The REPL's block detection is heuristic-based; complex nested blocks work best in files.

---

## License

This extension and the FSN language are licensed under the
**Creative Commons Attribution-NonCommercial 4.0 International License**.

You are free to use, share, and modify FSN for personal and educational purposes.
Commercial use requires explicit written permission from the project maintainer.

See [LICENSE](LICENSE) for full terms.
