---
title: "Lean Roguelike (Part 2)"
pubDate: 2026-08-05
updatedDate: 2026-08-26
description: "We start with very simple ambitions."
public: true
notionLastEdited: "2026-08-26T02:38:08.060000+00:00"
heroImage: "/images/covers/1dfe6a5e1404.png"
heroImagePosition: 0.0776
icon: "⚔️"
---
We start with very simple ambitions.

We’ll start with just getting a program that manipulates the terminal. This will include minimal Lean and whatever FFI is required to interface with terminal functions.

## Installing Lean

I won’t be going through the Lean installation. There are [good instructions](https://lean-lang.org/install/) on the Lean website. I would recommend the VS Code installation if you can, but it won’t be required.

For this setup we’ll be using the command line tools, so Visual Studio Code won’t provide any benefit.

## Build Setup

We are going to set up the command line build first. Lean has a make utility called `lake` that we will use.

Using `lake init` in a directory of your choice, you should see something akin to

```bash
drwxr-xr-x 10 me me 320 Aug  6 02:22 .
drwxr-xr-x 22 me me 704 Aug  6 02:19 ..
drwxr-xr-x  3 me me  96 Aug  6 02:22 .github
-rw-r--r--  1 me me   7 Aug  6 02:22 .gitignore
-rw-r--r--  1 me me  76 Aug  6 02:22 Main.lean
-rw-r--r--  1 me me  15 Aug  6 02:22 README.md
drwxr-xr-x  3 me me  96 Aug  6 02:22 TermTutorial
-rw-r--r--  1 me me 159 Aug  6 02:22 TermTutorial.lean
-rw-r--r--  1 me me 163 Aug  6 02:22 lakefile.toml
-rw-r--r--  1 me me  29 Aug  6 02:22 lean-toolchain
```

To test out the simple build, `lake exe <directory>` where the directory name is the directory you’re in. You should see  `Hello, world` from the `Main.lean` file compiled.

## Coming to Terms

Our initial exploration will be simply to work with the terminal in a minimal capacity.

We want to be enable raw mode, switch to the alternate screen, print a message, wait for a keystroke, and then return to the original screen, disable raw mode, and then quit.

ChatGPT determined that Lean doesn’t have a function to set the terminal in raw mode. So our first order of business is to write one in C and link it in.

Here is our terminal interface, with 4 functions. Save this as `c/terminal.c`.

```bash
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include <lean/lean.h>

static struct termios original_termios;
static int original_termios_saved = 0;

static lean_obj_res io_error_from_errno(const char *operation)
{
    char buffer[256];

    snprintf(
        buffer,
        sizeof(buffer),
        "%s: %s",
        operation,
        strerror(errno)
    );

    lean_object *message = lean_mk_string(buffer);
    lean_object *error = lean_mk_io_user_error(message);

    return lean_io_result_mk_error(error);
}

LEAN_EXPORT lean_obj_res
lean_terminal_enable_raw(lean_obj_arg world)
{
    (void)world;

    struct termios raw;

    if (tcgetattr(STDIN_FILENO, &original_termios) == -1) {
        return io_error_from_errno("tcgetattr");
    }

    original_termios_saved = 1;
    raw = original_termios;

    /* Equivalent to the usual portable POSIX raw-mode setup. */
    raw.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
    raw.c_oflag &= ~(OPOST);
    raw.c_cflag |= CS8;
    raw.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG);

    raw.c_cc[VMIN] = 1;
    raw.c_cc[VTIME] = 0;

    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) {
        return io_error_from_errno("lean_terminal_enable_raw:tcsetattr");
    }

    return lean_io_result_mk_ok(lean_box(0));
}

LEAN_EXPORT lean_obj_res
lean_terminal_restore(lean_obj_arg world)
{
    (void)world;

    /* Restore kernel TTY state. */
    if (original_termios_saved) {
        if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_termios) == -1) {
            return io_error_from_errno("tcsetattr");
        }

        original_termios_saved = 0;
    }

    return lean_io_result_mk_ok(lean_box(0));
}
```

Since we’re linking C code, we’ll need to change our build configuration a bit.

Besides a `lakefile.toml` file, Lean can use its own language to describe builds, which is required when linking C code.

Delete (or rename) the `lakefile.toml` file since it will no longer be used.

Next, we need to create a `lakefile.lean` to let `lake` build the C code and include it in the executable. Here is the `lakefile.lean`.

```bash
import Lake

open System Lake DSL

def ch : Nat :=
  ((get_config? ch).bind String.toNat?).getD 0

def chapterFile : Lean.Name :=
  s!"ch{ch}.Main".toName

def chapterConfigFile : Lean.Name :=
    s!"ch{ch}.build.Config".toName

def tutorial.section : Nat :=
  ((get_config? tutorial.section).bind String.toNat?).getD 0

package «rogue» where
  srcDir := "src"
  leanOptions := #[
    ⟨`weak.tutorial.section, .ofNat tutorial.section⟩
  ]

lean_lib chapterConfig where
  roots := #[chapterConfigFile]

input_file terminal.c where
  path := "src" / ("ch" ++ toString ch) / "c" / "terminal.c"
  text := true

target terminal.o pkg : FilePath := do
  let srcJob ← terminal.c.fetch
  let objectFile := pkg.buildDir / "c" / "terminal.o"

  let weakArgs := #[
    "-I",
    (← getLeanIncludeDir).toString
  ]

  buildO
    objectFile
    srcJob
    weakArgs
    #["-fPIC"]
    "cc"
    getLeanTrace

@[default_target]
lean_exe «rogue» where
  root := chapterFile
  moreLinkObjs := #[terminal.o]
```

Hopefully the build script is not inscrutable. There is some additional code here not directly related to the C linking. My article [Conditional Compilation in Lean](/conditional-compilation-in-lean/) explains more about Lean build scripts. Email me if you wish me to write a more detailed explanation of this file (see the About page for my email address). 

Now to expose these functions to Lean so we can call them. Our `Main.lean` should now look like:

```bash
@[extern "lean_terminal_enable_raw"]
opaque enableRawMode : IO Unit

@[extern "lean_terminal_restore"]
opaque restoreTermios : IO Unit

def main : IO Unit :=
  IO.println s!"Hello, world!"
```

There are a few things to unpack in the Lean code:

- The `extern` declarations make the C functions visible.
  - The names Lean uses don’t have to match the C names.

- The lack of parameters mean that the C functions take `void`, and `IO Unit` return values are the Lean equivalent to C’s `void`.

If this is your first exposure to Lean, then don’t worry about the above statements. It’s early to be introducing these concepts, but we need them since Lean’s standard library doesn’t have this functionality.

Use `lake exe main` to build the program. This should just output `Hello, world!` .

## Call Terminal Functions

We want to actually use these functions though, and do some additional things with the terminal.

We will use ESC codes to

- Switch screens

- Print a message

- Wait for a key press

- Restore the screen and terminal state

Here are the functions that will be using.

```haskell
def restoreTerminal : IO Unit := do
  let stdout ← IO.getStdout
  -- Restore the original screen.
  stdout.putStr "\x1b[?1049l"
  stdout.putStr "\x1b[?25h"
  stdout.putStr "\x1b[0m"
  stdout.flush
  restoreTermios

def switchScreen : IO Unit := do
  let stdout ← IO.getStdout
  -- switch to the alternate screen
  stdout.putStr "\x1b[?1049h\x1b[2J\x1b[H"
  stdout.putStr "\x1b[?25l"
  stdout.flush

def initTerminal : IO Bool := do
  enableRawMode
  switchScreen

  return true

def waitForKey : IO Unit := do
  let stdin ← IO.getStdin
  let _ ← stdin.read 1
```

These functions just send escape codes to the terminal via `stdout`, nothing fancy.

Couple this with a new `Main` function, and we can see the terminal in action.

Running this with `lake exe main` and you should see the screen clear, `Hello, world (press any key)` in the upper left corner. Press a key and it should return to the prompt.

```haskell
def main : IO Unit := do
  let _ ← initTerminal
  IO.println s!"Hello, world (press any key)"
  waitForKey
  restoreTerminal
```

Running this with `lake exe main` and you should see the screen clear, `Hello, world` in the upper left corner. Press a key and it should return to the prompt.

## Up Next

We’ll continue with our prototype with the terminal, moving a `@` around the screen.

:::callout{icon="🤖"}

This article and code were authored by me, with proofreading and editorial suggestions by AI.

:::
