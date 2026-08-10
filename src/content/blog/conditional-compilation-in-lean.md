---
title: "Conditional Compilation in Lean"
pubDate: 2026-08-13
updatedDate: 2026-08-17
description: "Conditional compilation is a handy tool to have for programming. It can select platform-specific code, development instrumentation, alternate implementations…"
public: false
notionLastEdited: "2026-08-17T05:39:26.948000+00:00"
---
Conditional compilation is a handy tool to have for programming. It can select platform-specific code, development instrumentation, alternate implementations, or—as in my case—different parts of a tutorial project.

Lean doesn’t have an `#ifdef`-style preprocessor, but it does have build configuration options that a Lean build script can use to control compilation. For the “roguelike in Lean” tutorial I’m developing, I’ve found that I can use this feature

- to decide which file(s) to compile

- to decide which definition or statement to use within a file (similar to #ifdef)

Using either of these options requires `-K` with `lake`. For example, `lake -K tracelevel=1 build` would set `tracelevel` to 1. 

:::callout{icon="💡"}

It is often necessary to include `-R` in the command line. `lake` has some sort of configuration cache, and changing the `-K` options used sometimes doesn’t seem to change the build unless `-R` is on the command line too.

:::

## Selecting Files at Compile Time

This requires using the `lakefile.lean` build script instead of the default `lakefile.toml`.

From above, we know that we have to somehow learn whether a certain option was passed via the `-K` option. In this example, we are reading the configuration option as a `Nat`.

```haskell
import Lake

open System Lake DSL

def tracelevel : Nat :=
  ((get_config? tracelevel).bind String.toNat?).getD 0

package «my_app» where
  srcDir := "src"
```

You can then use this for a variety of purposes within the `lakefile.lean` file. I have found it handy to use to separately compile different files. The type of the filename(s) must be `Lean.Name`.

```haskell
def mainFile : Lean.Name :=
  s!"trace{tracelevel}.Main".toName

...

@[default_target]
lean_exe my_app where
  root := mainFile
```

The periods in the filename represent subdirectories. Coupled with the `srcDir` assignment in the package, the full path to `mainFile` would be `src/trace<tracelevel>/Main.lean`.

## Inline Conditional Compilation

It is also possible to selectively compile certain code within a file. Again, the `-K` option is used, but the implementation is a bit different.

Here we dip into Lean’s metaprogramming capabilities. Lean offers two kinds of code generation: macros and elaborators. Macros are syntax → syntax transformations. Elaborators are Lean’s counterpart to Scheme’s `syntax-case` or Rust’s procedural macros. They let Lean code run at compile time and decide what gets compiled.

To demonstrate conditional compilation within a file, we’ll use an elaborator called `if_section`. This example shows how this can be used to decide which `main` function to compile.

```haskell
import build.Config

...

if_section = 1
def main : IO Unit :=
  IO.println s!"Hello from section 1"

if_section = 2
def main : IO Unit :=
  IO.println s!"Hello from section 2"
```

The build command `lake -R -K tutorial.section=2 exe my_app` maps to `if_section = 2` during compile time. Running this should print “Hello from section 2”.

The following code shows how this mapping is done.

```haskell
import Lean

open Lean Elab Command

register_option tutorial.section : Nat := {
  defValue := 0
  descr := "Section of the tutorial to compile"
}

syntax "if_section" "=" num command : command

elab_rules : command
  | `(if_section = $expected:num $cmd:command) => do
      let sect :=
        tutorial.section.get (← getOptions)

      if sect = expected.getNat then
        elabCommand cmd
```

This code can either be directly included in the file where the elaboration is used, or saved into a separate file and imported where needed (e.g. `import build.Config` in the conditional compilation example above).

`syntax` declares what Lean matches. In this case, two string literals and two variables, `num` as a singular term, while `command` represents the code that follows it.

`elab_rules` expands it by evaluating the syntax terms into variables, and then evaluating code at compile time. In our case here, it sets the variable `sect` to the value of the config option `tutorial.section`, and then compares that to the number bound in `expected`. If the `if` statement evaluates to true, `elabCommand cmd` inserts the code we included after `if_section`.

The `-K` option is used as in `lake -R -K tutorial.section=2 exe my_app` to define which section to use. But we must use some glue code in the `lakefile.lean` to pass the `-K` option to Lean’s compiler.

```haskell
def sect : Nat :=
  ((get_config? tutorial.section).bind String.toNat?).getD 0

...

package «my_app» where
  srcDir := "src"
  leanOptions := #[
    ⟨`weak.tutorial.section, .ofNat sect⟩
  ]
```

The Lean compiler uses `-D` to define compiler options, but `lake` uses `-K` to set configuration options. The code above effectively maps `-K` to `-D` by retrieving the value from the `lake` configuration and passing it through the `leanOptions` setting, the equivalent of passing `-D` to the Lean compiler. (`weak` is used to get around some circular dependencies that I won’t elaborate on here.)

## Conclusion

Lean’s metaprogramming facilities have earned it high praise as the “[perfectable language](https://alok.github.io/lean-pages/perfectable-lean/)”. Lisp is the only other language I’ve heard praised similarly.

This is only a small taste of Lean’s metaprogramming. There’s an [entire book](https://leanprover-community.github.io/lean4-metaprogramming-book/) related to it, but this sample is pretty tantalizing.

Given how much I still have to learn about Lean, I don’t think I’ll be touching on metaprogramming until much later in this project, if at all, but it’s good to know it’s there.
