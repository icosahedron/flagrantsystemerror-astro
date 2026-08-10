---
title: "Lean Roguelike (Part 2)"
pubDate: 2026-08-05
updatedDate: 2026-08-24
description: "We start with very simple ambitions."
public: false
notionLastEdited: "2026-08-24T04:52:20.129000+00:00"
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

    if (!original_termios_saved) {
        return lean_io_result_mk_ok(lean_box(0));
    }

    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_termios) == -1) {
        return io_error_from_errno("tcsetattr");
    }

    original_termios_saved = 0;

    return lean_io_result_mk_ok(lean_box(0));
}
```

Since we’re linking C code, we’ll need to change our build configuration a bit.

Besideds a `lakefile.toml` file, Lean can use its own language to describe builds, which is required when linking C code.

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

Now to expose these functions to Lean so we can call them. Our `Main.lean` should now look like:

```bash
if_section = 1
def main : IO Unit :=
  IO.println s!"Hello, world!"
```

There are a few things to unpack in the Lean code:

- The `extern` declarations make the C functions visible.
  - The names Lean uses don’t have to match the C names.

- The lack of parameters mean that the C functions take `void`, and `IO Unit` return values are the Lean equivalent to C’s `void`.

- `namespace` and `end` introduce a namespace. 

If this is your first exposure to Lean, then don’t worry about the above statements. It’s early to really be introducing these concepts. 

Use `lake exe main` to build the program. This should just output `Hello, world!` .

## Call Terminal Functions

We want to actually use these functions though, and do some additional things with the terminal.

We will use ESC codes to

- Switch screens

- Clear the screen

- Move the cursor to a specific location

- Print a message

Here are the functions that will be using.

```bash

```
