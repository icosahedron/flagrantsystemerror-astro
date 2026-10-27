---
title: "Lean at Large"
pubDate: 2026-10-31
updatedDate: 2026-11-02
description: "The programming language Lean is becoming better known."
public: false
notionLastEdited: "2026-11-02T08:35:37.042000+00:00"
---
The programming language Lean is becoming better known. 

I admit that it might be *frequency illusion* or it might be it’s always been there and *I* am starting to notice it. But I don’t think so. I think it’s the advent of AI code generation that makes formal verification practical.

As the AI models keep finding math proofs, they demonstrate the validity of the proofs using Lean. This has drawn the attention of software developers, who surmise that if Lean can do this for math, it should be possible to do for normal applications[^comment-1].

## Additional Articles

Below are articles that mention formal verification for software and Lean in particular.

[Why am I betting on Lean 4 for agentic coding? | Theoric](https://theoric.com/blog/why-lean-4-for-agentic-coding/)

[LeanDB: A strongly typed SQL Frontend | Theoric](https://theoric.com/blog/leandb_a_strongly_typed_sql_frontend/)

[A Type System Is a Search Oracle](https://hiraditya.github.io/posts/a-type-system-is-a-search-oracle/?utm_source=tldrnewsletter)

[Like Terraform, but in Lean 4](https://ngrislain.github.io/blog/2026-9-6-like-terraform-but-in-lean-4/) - “Terraform in Lean”

[I built the RealWorld app in Lean 4](https://leangineer.com/blog/realworld-in-lean/) - a “real” web application written in Lean. It could be useful as a reference in the future.

[Why Lean is faster than Rust — kim@lean](https://kim-em.github.io/blog/2026-7-24-why-lean-is-faster-than-rust/) - how finely tuned Lean can be performant using the `deflate` algorithm as an example.

[LLMs are making formal software verification feasible at a much larger scale](https://www.anthropic.com/research/formal-verification) - even Anthropic is extolling the virtues of formal verification, though this doesn’t mention Lean specifically.

## Are we headed towards formal software?

Given the ongoing cybersecurity attacks discovered by AI[^comment-2], it seems to me that verified software is the best front line against such attacks, *especially for system software*. Using verified kernels with verified services provided to verified applications should prevent most attacks.

### Is Lean the only option?

Is Lean the only programming language that we can use? Is functional programming the only paradigm where we can use proofs?

No. But functional programming languages do make it easier.

However, there are a few projects that demonstrate that you can use Lean like dependent types to prove programs in other languages.

- [Ansatz](https://github.com/replikativ/ansatz) converts the Lean kernel to Java/Clojure and allows proofs to be written in Clojure directly.

- [Aneas](https://github.com/AeneasVerif/aeneas) translates Rust into Lean (and other languages) to prove the program.

There will undoubtedly more work towards this, provoked by the ongoing cybersecurity holes being found in current software.





[^comment-1]: This presumption has academic validity via the Curry-Howard correspondence.
[^comment-2]: PHP2Shell is the primary vulnerability in the news as of 10/2026, but there have been several so far, and likely to continue to be.
