---
title: "Lean at Large"
pubDate: 2026-10-31
updatedDate: 2026-11-06
description: "The programming language Lean is becoming better known."
public: true
notionLastEdited: "2026-11-06T00:07:21.442000+00:00"
heroImage: "/images/covers/eac5556e2eb4.png"
heroImagePosition: 0.5
icon: "🚓"
---
The programming language Lean is becoming better known. 

I admit that it might be *frequency illusion*, but I believe it’s due to the advent of AI code generation that makes formal verification practical.

As AI models keep finding math proofs, they increasingly demonstrate the validity of the proofs using Lean. This has drawn the attention of software developers, who surmise that if Lean can do this for math, it should be possible to do the same for normal applications[^comment-1].

## Additional Articles

Below are articles that mention formal verification for software and Lean in particular.

[Why am I betting on Lean 4 for agentic coding? | Theoric](https://theoric.com/blog/why-lean-4-for-agentic-coding/) - “Because Lean 4 can potentially solve the unreliability of AI coding agents.”

[LeanDB: A strongly typed SQL Frontend | Theoric](https://theoric.com/blog/leandb_a_strongly_typed_sql_frontend/) - “LeanDB is an experiment in applying part of this idea to databases”.

[A Type System Is a Search Oracle](https://hiraditya.github.io/posts/a-type-system-is-a-search-oracle/?utm_source=tldrnewsletter) - “The machine checker is the only cheap way to put constraints back.”

[Like Terraform, but in Lean 4](https://ngrislain.github.io/blog/2026-9-6-like-terraform-but-in-lean-4/) - “How many of the mistakes you normally discover halfway through an `apply` can be moved into the compiler?”

[I built the RealWorld app in Lean 4](https://leangineer.com/blog/realworld-in-lean/) - a “real” web application written in Lean. It could be useful as a reference in the future.

[Why Lean is faster than Rust — kim@lean](https://kim-em.github.io/blog/2026-7-24-why-lean-is-faster-than-rust/) - how finely tuned Lean can outperform Rust, using the `deflate` algorithm as an example.

[LLMs are making formal software verification feasible at a much larger scale](https://www.anthropic.com/research/formal-verification) - even Anthropic is extolling the virtues of formal verification, though this doesn’t mention Lean specifically.

[Progress on provable inference for large language models](https://www.anthropic.com/research/provable-inference) - using cryptographic proofs to show that you’re talking to the model you think you’re talking to, with Lean used to prove the protocol’s security guarantees.

## Are we headed towards formal software?

Given the ongoing security vulnerabilities that are discovered by or exploited with the help of AI[^comment-2], it seems to me that verified software is the best front line against such attacks, *especially for system software*. A verified kernel (such as seL4) running verified services for verified applications would eliminate whole classes of attacks.

### Is Lean the only option?

Is Lean the only programming language that we can use? No. Dafny, F*, Rocq can all be used.

Is functional programming the only paradigm where we can use proofs? No. But functional programming languages do make it easier.

There are a few projects that demonstrate that you can use Lean-style dependent types to prove programs in other languages.

- [Ansatz](https://github.com/replikativ/ansatz) reimplemented the Lean kernel in Java,  so you can write proofs in Clojure. No translation to Lean necessary.

- [Aeneas](https://github.com/AeneasVerif/aeneas) translates safe Rust into Lean (and other proof assistants) to prove properties about the program.

- [Project Everest](https://project-everest.github.io) has created verified implementations of several components of the web stack in F* (which compile to C).

There will undoubtedly be more work towards this, provoked by the ongoing cybersecurity holes being found in current software.

[^comment-1]: This presumption has theoretical grounding via the Curry-Howard correspondence.
[^comment-2]: PHP2Shell is the primary vulnerability in the news as of 10/2026, but there have been several so far, and there are likely to be more.
