---
title: "Lean Roguelike (Part 3)"
pubDate: 2026-08-29
updatedDate: 2026-10-25
description: "Welcome back. We’ll continue our journey creating a roguelike in Lean with a little more terminal work, focusing on rudimentary input and output using Lean’s…"
public: true
notionLastEdited: "2026-10-25T15:41:25.517000+00:00"
heroImage: "/images/covers/2a0faf6738d0.png"
heroImagePosition: 1
icon: "💻"
---
Welcome back. We’ll continue our journey creating a roguelike in Lean with a little more terminal work, focusing on rudimentary input and output using Lean’s foreign function interface (FFI).

:::callout{icon="🧑‍💻"}

The code for this series is avaialble at [lean-rogue](https://codeberg.org/icosahedron/lean-rogue)

:::

I would prefer to get on with the game, so I decided to incorporate a cross platform terminal library rather than writing one from scratch in Lean. This article explains how I interfaced Lean with the Crossterm terminal library.

## Lean At Large

Before getting to that, I found several articles mentioning and projects using Lean. 

The first two articles describe a team building a product around Lean.

[LeanDB: A strongly typed SQL Frontend | Theoric](https://theoric.com/blog/drafts/leandb_a_strongly_typed_sql_frontend/)

[Why am I betting on Lean 4 for agentic coding? | Theoric](https://theoric.com/blog/why-lean-4-for-agentic-coding/)

The next article is about how Lean’s proof obligations help AI create more sound software.

[A Type System Is a Search Oracle](https://hiraditya.github.io/posts/a-type-system-is-a-search-oracle/?utm_source=tldrnewsletter)

And this article is a has created a “provable infrastructure” with Lean.

[Like Terraform, but in Lean 4](https://ngrislain.github.io/blog/2026-9-6-like-terraform-but-in-lean-4/)

Someone implemented the *RealWorld* reference web application in Lean 4. I’ll be using this as a reference.

[I built the RealWorld app in Lean 4](https://leangineer.com/blog/realworld-in-lean/)

Here someone demonstrates that Lean can write performant code by porting and profiling the the `deflate` compression algorithm and comparing it against popular implementations.

[Why Lean is faster than Rust — kim@lean](https://kim-em.github.io/blog/2026-7-24-why-lean-is-faster-than-rust/)

And even Anthropic has an article extolling the virtues of formal verification, though it doesn’t use Lean to accomplish that.

[LLMs are making formal software verification feasible at a much larger scale](https://www.anthropic.com/research/formal-verification)

And to add our little corner to the growing “Lean for applications rather than just math” articles, let’s proceed.

## Lean FFI

Lean is a capable language, but its ecosystem for application development is small. However, it has a robust foreign function interface based on the C ABI (function calling standard). Using the C ABI opens up almost any library for use, though a small layer of code is necessary to translate from C data types to Lean types. This is what we do for our terminal library.

The caveat is that Lean can’t guarantee the properties of the C code the way it can its own, so we have to be careful. Choosing a language like Rust, with its memory safety, can help alleviate some of these concerns.

Our code will layer like this.

:::figure{src="/images/posts/64421fc8d8b1.png"}
:::

We have a simple C layer that calls a Rust layer that wraps Crossterm with higher level functions.

## Crossterm

I chose [Crossterm](https://github.com/crossterm-rs/crossterm#feature-flags) since it’s cross platform, has a well structured event stream for input, and supports window resizing, extended keyboard information, mouse input, etc.

For a simple test, we’ll exercise the following:

- Initialize the terminal
  - Switch to raw mode - most terminals are in “cooked” mode, meaning that programs don’t receive any input until Enter is pressed. Raw mode passes the keys directly to the program as soon as they are pressed.
  - Switch to the alternate screen - the alternate screen is a second screen that a terminal uses to be able to not disturb the original screen. Programs such as Vim frequently use this.
  - Set extra attributes for keyboards, etc.

- Print a message to stdout

- Wait for a keypress from stdin - Crossterm returns events, which can be keys, window resizing, mouse events, etc.

- Restore the terminal
  - Switch back to cooked mode
  - Switch back to the main screen - this restores what the screen looked like when the application was launched
  - Reset the attributes/etc. back to original

We’ll just create a “lean” test function:

```javascript
def TermTest : TerminalM Unit := do
  let _ ← enterTerminal
  write "Hello, world"
  let x ← nextEvent
  let _ ← restoreTerminal
  match x with 
  | .none => write "read: .none"
  | .key k => write s!"read: {k.code}"
  | .resize _ => write "read: resize"
  pure ()
```

This only exercises the minimal functionality. We’ll be adding more as necessary.

### Building

To include Crossterm will require a few small changes to the build setup. If we’re going to be making significant changes like this, then we’ll keep them close to each chapter code. Now each `src/ch#` directory (`src/ch2` for this article) contains the build files instead of the root, so each build must be run from these directories, as follows.

```bash
cd src/ch2
lake exe build
```

The changes to `lakefile.lean` create a new target that runs `cargo build` to build the Rust library that wraps Crossterm, `lean_terminal.a`. The default target includes it.

```haskell
  Job.async do
    let rustDir := pkg.dir / "terminal-rs"
    let targetDir := pkg.buildDir / "rust"

    IO.FS.createDirAll targetDir

    proc {
      cmd := "cargo"
      args := #[
        "build",
        "--release",
        "--target-dir",
        targetDir.toString
      ]
      cwd := some rustDir
      -- Make sure that Cargo environment variables are included if set.
      env := #[("CARGO_BUILD_TARGET", none), ("CARGO_TARGET_DIR", none)]
    }

    return targetDir /
      "release" /
      nameToStaticLib "lean_terminal"
```

### Rust Layer

This library Rust crate wraps Crossterm functions at a higher level. As an example, this is the `ct_enter_terminal` function from the `src/ch2/terminal-rs/lib.rs` file. It’s exposed as a C compatible function that slimly wraps `crossterm`:

```haskell
#[unsafe(no_mangle)]
pub extern "C" fn ct_enter_terminal() -> i32 {
    // let _ = init_tracing();

    match enable_raw_mode() {
        Ok(()) => (),
        Err(_) => return TerminalError::RawMode as i32,
    }
    TERMINAL_STATE.fetch_or(RAW_MODE, Ordering::SeqCst);

    match execute!(stdout(), EnterAlternateScreen) {
        Ok(()) => (),
        Err(_) => return TerminalError::AlternateScreen as i32,
    }
    TERMINAL_STATE.fetch_or(ALT_SCREEN, Ordering::SeqCst);

    match execute!(stdout(), cursor::Hide) {
        Ok(()) => (),
        Err(_) => return TerminalError::CursorVisibility as i32,
    }
    TERMINAL_STATE.fetch_or(CURSOR_HIDDEN, Ordering::SeqCst);

    let supports_keyboard_enhancement = matches!(
        crossterm::terminal::supports_keyboard_enhancement(),
        Ok(true)
    );

    if supports_keyboard_enhancement {
        match queue!(
            stdout(),
            PushKeyboardEnhancementFlags(
                KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES
                    | KeyboardEnhancementFlags::REPORT_ALL_KEYS_AS_ESCAPE_CODES
                    | KeyboardEnhancementFlags::REPORT_ALTERNATE_KEYS
                    | KeyboardEnhancementFlags::REPORT_EVENT_TYPES
            )
        ) {
            Ok(()) => (),
            Err(_) => return TerminalError::KeyboardEnhancement as i32,
        }
    }

    0
}
```

### C Layer

After which we’ll need another layer in C that exposes the Rust library to Lean. This mostly just marshals the C types to their Lean types. As an example, `lean_terminal_try_next_event`:

```haskell
LEAN_EXPORT lean_obj_res
lean_terminal_try_next_event(lean_obj_arg world) {
  (void)world;

  CtEvent event = ct_read_event();
  lean_object *lean_event = ct_event_to_lean(&event);
  return io_result_except_ok(lean_event);
}
```

The functions `lean_

### Lean Declarations

And finally the Lean declarations for those functions.

```haskell
structure KeyEvent where
  code : Char
  modifiers : UInt8

structure ResizeEvent where
  width : UInt16
  height : UInt16

-- We have a none event since it's possible that no events are available.
-- This is what is returned from the C FFI terminal interface, meant to be translated to Lean friendly events.
inductive CTerminalEvent : Type where
  | none : CTerminalEvent
  | Key : UInt32 → UInt8 → CTerminalEvent
  | Resize : UInt16 → UInt16 → CTerminalEvent

inductive TerminalEvent : Type where
  | none : TerminalEvent
  | key : KeyEvent → TerminalEvent
  | resize : ResizeEvent → TerminalEvent

@[extern "lean_terminal_enter"]
opaque terminalEnter : IO (Except String Unit)

@[extern "lean_terminal_restore"]
opaque terminalRestore : IO Unit

@[extern "lean_terminal_try_next_event"]
opaque terminalTryNextEvent : IO (Except String CTerminalEvent)

@[extern "lean_terminal_next_event"]
opaque terminalNextEvent : IO (Except String CTerminalEvent)
```

Now that we have a terminal interface for our basics, we can actually do something on the screen. It’s not much, but it’s a start. We will need to add cursor support, support for window resizing, flesh out the `modifiers` member of `KeyEvent`, and eventually add things like mouse support.

## Next Time

If you  looked at the source code in `ch2`, you undoubtedly noticed that there is more plumbing than what is presented here.  We are going to introduce that in our next article.

:::callout{icon="🤖"}

This article and code were authored by me, with proofreading and editorial suggestions by AI.

:::

<div id="cast-demo" style="width: 100%"></div>
<script src="https://cdn.jsdelivr.net/npm/asciinema-player@3.17.0/dist/bundle/asciinema-player.min.js"></script>
<script>
  AsciinemaPlayer.create('/casts/demo.cast', document.getElementById('cast-demo'), {
    idleTimeLimit: 2,
  });
</script>
