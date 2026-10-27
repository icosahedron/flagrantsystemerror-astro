---
title: "Lean Roguelike (Part 3)"
pubDate: 2026-08-29
updatedDate: 2026-11-03
description: "Welcome back. We’ll continue our journey creating a roguelike in Lean with a little more terminal work, focusing on rudimentary input and output using Lean’s…"
public: true
notionLastEdited: "2026-11-03T03:01:46.179000+00:00"
heroImage: "/images/covers/2a0faf6738d0.png"
heroImagePosition: 1
icon: "💻"
---
Welcome back. We’ll continue our journey creating a roguelike in Lean with a little more terminal work, focusing on rudimentary input and output using Lean’s foreign function interface (FFI).

:::callout{icon="🧑‍💻"}

This is not a tutorial per se. It’s an exposition on what I did to write a roguelike in Lean. As such, the code listings here are not complete. The completed code is available at [lean-rogue](https://codeberg.org/icosahedron/lean-rogue).

:::

Rather than creating a complete terminal library in Lean, I would prefer to get on with the game, so I decided to incorporate a cross-platform terminal library. This article explains how I interfaced Lean with the [Crossterm](https://crates.io/crates/crossterm) library.

Here’s an example of what we’re building in this article. (Impressive, I know 😅.)

<div id="cast-demo" style="width: 100%"></div>
<script src="https://cdn.jsdelivr.net/npm/asciinema-player@3.17.0/dist/bundle/asciinema-player.min.js"></script>
<script>
  AsciinemaPlayer.create('/casts/demo.cast', document.getElementById('cast-demo'), {
    idleTimeLimit: 2,
  });
</script>

This shows the build finishing, displaying “Hello, world”, waiting for a keypress, and finally returning to the prompt.

## Lean FFI

Lean is a capable language, but its ecosystem for application development is comparatively small. However, it has a robust FFI using the C application binary interface (ABI) standard. Using the C ABI opens up almost any library for use, though a small layer of code is necessary to translate from C data types to Lean types. This is what we do for our terminal library.

The caveat is that Lean can’t guarantee the properties of the C code the way it can its own, so we have to be careful. Choosing a language like Rust, with its memory safety, can help alleviate some of these concerns.

Our code will layer like this.

:::figure{src="/images/posts/64421fc8d8b1.png"}
:::

The architecture consists of these 5 layers. We're implementing the first three, from left to right.

- The application is within Lean

- The C only translates from Rust to Lean. Exported Lean functions construct the values returned to the application.

- The Rust is a higher level layer of terminal control useful for this application.

## Crossterm

I chose [Crossterm](https://github.com/crossterm-rs/crossterm#feature-flags) since it’s cross-platform, has a well-structured event stream for input, and supports window resizing, extended keyboard information, mouse input, etc.

For a simple test, we’ll exercise the following:

- Initialize the terminal
  - Switch to raw mode - most terminals are in “cooked” mode, meaning that programs don’t receive any input until Enter is pressed. Raw mode passes the keys directly to the program without waiting for Enter.
  - Switch to the alternate screen - the alternate screen is a second screen that a terminal uses to not disturb the original screen. Programs like Vim use this.
  - Other miscellaneous settings for attributes

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

### Building

We are going to focus on building first, so we can iterate as we integrate Crossterm.

To build, you’ll need to install the Rust toolchain. Then carry over the files from the `src/ch1` directory into `src/ch2`.

In the `src/ch2` directory, create a new Rust library using [Cargo](https://doc.rust-lang.org/cargo/guide/creating-a-new-project.html?utm_source=chatgpt.com) called `terminal-rs` and add the Crossterm crate as a dependency to its `Cargo.toml`. Build it with `cargo build` to verify. The repo has custom code in a [`build.rs`](http://build.rs) file that creates the C header file we will use later.

Next, we need to have `lake` include the crate into the build, linking the C and Rust libraries into the Lean binary.

The following changes to `lakefile.lean` create a new target that runs `cargo build` to build the Rust library, `lean_terminal.a`. The default target includes it.

```haskell
  Job.async do
    let rustDir := pkg.dir / "terminal-rs"
    let targetDir := pkg.buildDir / "rust"

    IO.FS.createDirAll targetDir

    proc {
      cmd := "cargo"
      args := #[
        "build",
        "--target-dir",
        targetDir.toString
      ]
      cwd := some rustDir
      -- Make sure that Cargo environment variables are included if set.
      env := #[("CARGO_BUILD_TARGET", none), ("CARGO_TARGET_DIR", none)]
    }

    return targetDir /
      "debug" /
      nameToStaticLib "lean_terminal"
```

(This is not the complete change. It only illustrates how `cargo build` is called from the build. See the [lakefile.lean file in ch2](https://codeberg.org/icosahedron/lean-rogue/src/branch/main/src/ch2/lakefile.lean) for the complete changes necessary to integrate the Rust crate.)

### Rust Layer

This library Rust library wraps Crossterm functions at a higher level. As an example, this is the `ct_enter_terminal` function from the `src/ch2/terminal-rs/lib.rs` file. It’s exposed as a C-compatible function that is a thin wrapper around initialization in Crossterm.

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
        match execute!(
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

I won’t explain anything here since this isn’t the focus of the article. It suffices to say that the Rust functions just provide a high level interface to the terminal to support the Lean roguelike.

### Lean Layer

On the other side of the bridge we have the Lean code that represents the Crossterm events.

```javascript
structure KeyEvent where
  code : Char
  modifiers : UInt8

structure ResizeEvent where
  width : Nat 
  height : Nat

inductive TerminalEvent : Type where
  | none : TerminalEvent
  | key : KeyEvent → TerminalEvent
  | resize : ResizeEvent → TerminalEvent

-- constructor functions called from C
@[export mk_event_none]
def mkNoneEvent : TerminalEvent :=
  .none

@[export mk_event_key]
def mkKeyEvent (ch : UInt32) (modifiers : UInt8) : TerminalEvent :=
  if ch.isValidChar then
    .key (KeyEvent.mk (Char.ofNat ch.toNat) modifiers)
  else
    .none

@[export mk_event_resize]
def mkResizeEvent (width height : UInt16) : TerminalEvent :=
  .resize (ResizeEvent.mk width.toNat height.toNat)
```

These definitions represent the terminal events and helper functions that can create them from and for Lean. The functions are called from the C code and return the Lean `TerminalEvent` that represents the Crossterm event, created from the C-compatible data returned by Crossterm.

Using the Lean constructors saves us from having to construct the objects in C, which can be a finicky process. To see what that would entail, [this skill](https://askill.sh/skills/gh/majiayu000/claude-skill-registry-data/data/lean4-ffi-constructor-layout), meant for AI agents, explains the memory layout and APIs to create Lean objects to return. 

### C Layer

Now we’re ready for the C layer which will bridge Crossterm’s Rust and the game’s Lean. 

As an example, `lean_terminal_try_next_event` in `src/ch2/c/terminal.c`.

```haskell
LEAN_EXPORT lean_obj_res lean_terminal_try_next_event(lean_obj_arg world) {
  (void)world;

  CtEvent event = ct_read_event();
  lean_obj_res lean_event;

  switch (event.event_type) {
  case TERMINAL_EVENT_NONE:
    lean_event = mk_event_none();
    break;
  case TERMINAL_EVENT_KEY:
    lean_event = mk_event_key(event.data.key.code, event.data.key.modifiers);
    break;
  case TERMINAL_EVENT_RESIZE:
    lean_event =
        mk_event_resize(event.data.resize.width, event.data.resize.height);
    break;
  default:
    return io_result_except_error(
        "lean_terminal_try_next_event: unknown event type.");
  }

  return io_result_except_ok(lean_event);
}
```

`lean_terminal_try_next_event` reads an event from Crossterm and calls the appropriate Lean function to construct a `TerminalEvent` from C data. It then uses `io_result_except_ok` to wrap the event in an `IO (Except String TerminalEvent)`  result.

Calling a Lean function to construct a Lean object and then returning that same object back to Lean is admittedly circular. The alternative is to construct the Lean objects in C, which, as noted above, requires an understanding of details best left to Lean itself.

Constructing via Lean also has the advantage of keeping the representation of `TerminalEvent` squarely within Lean, instead of strewn across two libraries.

### Lean Declarations

And finally the Lean declarations for the C functions.

```haskell
-- C API for terminal
@[extern "lean_terminal_enter"]
opaque terminalEnter : IO (Except String Unit)

@[extern "lean_terminal_restore"]
opaque terminalRestore : IO Unit

@[extern "lean_terminal_try_next_event"]
opaque terminalTryNextEvent : IO (Except String TerminalEvent)

@[extern "lean_terminal_next_event"]
opaque terminalNextEvent : IO (Except String TerminalEvent)
```

The C functions are exposed to Lean using `opaque` declarations with the `@[extern]` attribute. Lean uses these to type-check calls, while the implementations are provided by our C code.

## Next Time

Now that we have the basics of a terminal interface, we can actually do something on the screen. It’s not much, but it’s a start. We will need to add cursor support, support for window resizing, flesh out the `modifiers` member of `KeyEvent`, and eventually add things like mouse support.

If you have looked at the source code in `ch2`, you have undoubtedly noticed that there is more plumbing than just terminal use.  That’s the subject of the next article.

:::callout{icon="🤖"}

This article and code were authored by me, with proofreading and editorial suggestions by AI.

:::
