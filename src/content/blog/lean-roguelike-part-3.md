---
title: "Lean Roguelike (Part 3)"
pubDate: 2026-08-29
updatedDate: 2026-10-20
description: "Welcome back. We’ll continue our journey with a little more terminal work, focusing on rudimentary input and output."
public: true
notionLastEdited: "2026-10-20T06:34:19.828000+00:00"
heroImage: "/images/covers/2a0faf6738d0.png"
heroImagePosition: 1
icon: "💻"
---
Welcome back. We’ll continue our journey with a little more terminal work, focusing on rudimentary input and output.

Before getting to that, I found someone else who is of like mind with Lean and AI generated code. They are actually building a product interface around Lean. Hope it succeeds.

[LeanDB: A strongly typed SQL Frontend | Theoric](https://theoric.com/blog/drafts/leandb_a_strongly_typed_sql_frontend/)

[Why am I betting on Lean 4 for agentic coding? | Theoric](https://theoric.com/blog/why-lean-4-for-agentic-coding/)

This is also a good article about how Lean’s proof obligations create more sound software written by AI.

[A Type System Is a Search Oracle](https://hiraditya.github.io/posts/a-type-system-is-a-search-oracle/?utm_source=tldrnewsletter)

And this person has created a “provable infrastructure” with Lean.

[Like Terraform, but in Lean 4](https://ngrislain.github.io/blog/2026-9-6-like-terraform-but-in-lean-4/)

Last, but not least, someone implemented the *RealWorld* reference web application in Lean 4.

[I built the RealWorld app in Lean 4](https://leangineer.com/blog/realworld-in-lean/)

## Crossterm

I would prefer to get on with the game, so I decided to incorporate a cross platform terminal library rather than writing one from scratch in Lean. I chose [Crossterm](https://github.com/crossterm-rs/crossterm#feature-flags) since it’s precisely that, cross platform, has a well structured event stream for input, and support for window resizing, mouse input, etc.

I figured it would also be a good opportunity to showcase the Lean Foreign Function Interface (FFI).

For a small test, we’ll using this very basic functionality:

- Initialize the terminal
  - Switch to raw mode
  - Switch to the alternate screen

- Print a message

- Wait for a keypress

- Restore the terminal
  - Switch back to cooked mode
  - Switch back to the main screens
  - Reset the attributes/etc.

We’ll just create a simple test function for this:

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

This exercises the minimal functionality, but should be enough to at least continue building on.

### Building

To include Crossterm will require a few small changes to the build setup. If we’re going to be making significant changes like this, then we’ll keep them close to each chapter code. Now each `src/ch#` directory contains the build files instead of the root, so each build must be run from these directories. Use `lake` as before.

The changes to `lakefile.lean` create a new target that runs `cargo build` to build the library, `lean_terminal.a`. The default target includes it.

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

From there we’ll create a library Rust crate that will expose the functions we want. As an example, this is the `ct_enter_terminal` function from the `src/ch2/terminal-rs/lib.rs` file. It’s exposed as a C compatible function that  slimly wraps `crossterm`:

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

After which we’ll need another layer in C that exposes the Rust library to Lean. This mostly just marshals the C types to their Lean types. As an example, `lean_

```javascript
LEAN_EXPORT lean_obj_res lean_terminal_enter(lean_obj_arg world) {
  (void)world;

  int32_t status = ct_enter_terminal();
  // printf("Terminal enter status: %d\n", status);
  if (status != 0) {
    if (status > 3 || status < 0) {
      return io_result_except_error("Unknown terminal error");
    }

    return io_result_except_error(ct_error_messages[status]);
  }

  return io_result_except_ok(lean_box(0));
  // This is to test the error handling.
  // return io_result_except_error("Terminal enter not implemented yet");
}
```

And finally the Lean declarations for those functions.

```javascript
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

Now that we have a terminal interface for our basics, we can actually do something on the screen.

## Next Time

If you looked at the source code `ch2`, you undoubtedly noticed that there is more plumbing than what is presented here.  We are going to introduce that in our next article.

:::callout{icon="🤖"}

This article and code were authored by me, with proofreading and editorial suggestions by AI.

:::
