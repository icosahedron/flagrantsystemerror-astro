---
title: "Lean Roguelike (Part 1)"
pubDate: 2026-06-06
updatedDate: 2026-08-10
description: "To better learn the applicability of formal methods in general for application development, I’m attempting to write small roguelike using Lean."
public: false
notionLastEdited: "2026-08-10T06:42:45.803000+00:00"
heroImage: "/images/covers/cc92f9c7c83c.png"
heroImagePosition: 0.5
icon: "🕹️"
---
To better learn the applicability of formal methods in general for application development, I’m attempting to write small roguelike using Lean.

Games and business applications might not be obviously related, but they’re both code, and if you can “prove” your game, you can prove your application.

This series assumes a Unix operating system, either Linux or macOS. Lean itself works on Windows, but there is some platform specific code.

## What is Lean?

I won’t explain too much about Lean other than to say it is a functional programming language that doubles as a theorem prover, or it’s an automated theorem prover that doubles as a functional language.

If you’re familiar with Haskell, the syntax will be somewhat familiar.

If you’ve heard of Lean, you’ve likely heard about it via the success of LLMs in solving before unsolved math conjectures. These LLMs generate Lean code to find the proofs.

And if LLMs can do it, why can’t we?

Some links to better explain Lean

- [The Lean Homepage](https://lean-lang.org)

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)

- [Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/NNG4)
  - This doesn’t teach program verification, but does help familiarize with proofs and tactics

- [Lean for Scientists and Engineers Video Playlist](https://www.youtube.com/watch?v=s9Dyiu4S4vA&list=PLX21uJ4UfpF43NExUcPcAEgnzV58x_26l)

## Why Formal Methods?

Formal methods are not new. The [history](https://kindatechnical.com/formal-methods/lesson-2-history-and-evolution-of-formal-methods.html) of using formal methods to prove either specifications or code has been around for 50+ years, and some would say that the formalization of computation with the Turing Machine and Lambda Calculus in the 1930’s were also formal methods.

With advances in computation and programming language theory, we now have the capacity to prove theorems interactively.

But the human effort required to build these proofs is still very high. Therefore only very sensitive software, such as kernels, cryptography, or high risk to humans (e.g. medical machinery) software.

### Now is the Time for Formal Methods

The combination of LLMs and Formal methods is potentially a powerful one. And makes it easier than ever to verify even non-critical software.

I’m not the only one to imagine such a possibility:

- [Prediction: AI will make formal verification go mainstream](https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html)

- [Formal Methods at Jane Street](https://blog.janestreet.com/formal-methods-at-jane-street-index/)

- [Vibe Validation with Lean, ChatGPT-5, & Claude 4.5 (Part 1)](https://medium.com/@carlmkadie/vibe-validation-with-lean-chatgpt-5-claude-4-5-part-1-c57b430b3d7a)
  - This last one is behind a paywall that you might not be able to access.

## Roguelike in Lean

What would a roguelike in Lean look like?

That’s a good question. I have not yet developed it. Lean doesn’t have a lot of libraries, so some effort will be necessary to just make the game development possible.

For example, as of August 2026, there is no terminal library for Lean, outside of just standard POSIX IO. Nothing like `ncurses` or more advanced.

Lean *does* have a robust FFI that interfaces with C libraries, so adding `ncurses` would be possible, but I want to keep as much as in Lean as possible, so unless absolutely necessary, I won’t be interfacing with any C libraries other than the standard library.

Who knows, this may turn out to be an effort that results in me learning that Lean isn’t fit for application development. I doubt that, or I wouldn’t be undertaking this project.

### A Note on AI

This will *not* be written by AI. **No AI generated code will be used**. 

AI *will* be used in a teaching capacity, much like Google or Stack Overflow. Pure questions and answers, but no huge copypasta code chunks.
