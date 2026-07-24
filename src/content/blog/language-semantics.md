---
title: "Category Theory: Programming Language Semantics"
pubDate: 2024-11-29
description: "While watching video 2.1 of the Category Theory series, Bartosz briefly mentions semantics of programming languages. But what are these semantics?"
---
While watching video 2.1 of the Category Theory series, Bartosz briefly mentions semantics of programming languages. But what are these semantics?

> …every time you design a language you have to provide semantics for the language, right? What does it mean, certain things in language? A lot of languages are defined using operational semantics. I mean the ones that have semantics, right? <chuckle from the class>. There are very few of them, none of the major ones. But they sort of like, have part of their semantics, right? 
> 
> There are two ways to define semantics. One is by telling how this thing executes, right, so it’s called operational semantics, because you’re defining operations of the language. You know how one expression or statement can be turned into another simpler one and so on.
> 
> And the other is called denotational semantics, where you actually map into some other area that you understand. And in particular, the most interesting of mappings is into mathematics, right? So you say “this statement in the language or this construct in the language corresponds to some mathematical thing.”

Curiosity piqued, a side quest opened in my adventure journal. What exactly are operational and denotational semantics, and how are they defined? And what languages have them defined?

Besides operational and denotational, there is a third that I see referenced quite a bit, *axiomatic semantics*.

The quick summary of each type is 

- Operational Semantics - what the program does

- Denotational Semantics - what the program means

- Axiomatic Semantics - what properties the program has

Since the first two are the only ones mentioned in the video, I only researched them for this article.

## Operational Semantics

Operational semantics define how a language operates. Given an *idealized* machine, the operational semantics describe how this programming language operates on that machine. 

What is an idealized machine? The machine in your imagination. In other words, operational semantics are what you describe. 

There are two primary ways that these can be expressed.

### Natural Language

The first is in precise natural language.  Operational semantics can be a written description of how a language operates, and sometimes more importantly, how it doesn’t operate.

This is not so different from feature specifications that you may have written.

A good example is the Java Language Specification of iteration in a [for loop](https://docs.oracle.com/javase/specs/jls/se8/html/jls-14.html#jls-14.14):

> **14.14.1.2. Iteration of **`for`** Statement**

> Next, a `for` iteration step is performed, as follows:

> If the *Expression* is present, it is evaluated. If the result is of type `Boolean`, it is subject to unboxing conversion ([§5.1.8](https://docs.oracle.com/javase/specs/jls/se8/html/jls-5.html#jls-5.1.8)).

> If the *Expression* is not present, or it is present and the value resulting from its evaluation (including any possible unboxing) is `true`, then the contained *Statement* is executed. Then there is a choice:

> If the *Expression* is present and the value resulting from its evaluation (including any possible unboxing) is `false`, no further action is taken and the `for` statement completes normally.

> If the *Expression* is not present, then the only way a `for` statement can complete normally is by use of a `break` statement.

### Problems with Natural Language Operational Semantics

It may seem like a good idea to use natural language, because anything can be described with it. However, it is very difficult to describe things unambiguously. Knowledge transfer via natural language is inherently imprecise.

Not only is this a limitation of the medium, but someone writing such a description will inevitably fall victim to their own perceptions. The subject is well known to them, and likely important details will be left out.

As well, natural language is tiring to write. The longer a document becomes, the more difficult it becomes to maintain consistency.

Of course, it can be done, but the labor involved is not small. It requires many iterations and revisions to get it right.

### Transition Systems

Instead of witting natural language descriptions, what if we used formal logic to describe operations as transitions between states?

[Gordon Plotkin](https://homepages.inf.ed.ac.uk/gdp/publications/sos_jlap.pdf) realized that natural language and other attempts at expression of operational semantics were lacking. He thought that describing programs as state machines and their transitions would be more succinct and precise.

These state machines and rules are given in standard form of formal logic.

An example for sequential statements operating on states:

$$
(S_0, s) \rarr s^{\prime} \over (S_0; S_1, s) \rarr (S_1, s^{\prime})
$$

This says that 

- if program statement $S_0$ executes under state $s$ and then terminates, the state at termination is $s^{\prime}$,

- then if a program with statements $S_0$ and $S_1$ remaining, when $S_0$ executes, the state after is $S_1$ remains to be executed, under the new state $s^{\prime}$.

Plotkin’s paper summarizes the intent of the notation:

> The announced “symbol-pushing” nature of our method suggests what is the truth; it is an operational method of specifying semantics based on syntactic transformations of programs and simple operations on discrete data. The idea is that in general one should be interested in computer systems whether hardware or software and for semantics one thinks of systems whose configurations are a mixture of syntactical objects – the programs and data – such as stores or environments. Thus in these notes we have
> SYSTEM = PROGRAM + DATA

:::callout{icon="ℹ️"}
This [presentation](https://www.youtube.com/watch?v=takJBOaHnJs) from the Luca Aceto of Reykjavik University provided much of the understanding of operating semantics for this article. And it’s entertaining.
:::

## Denotational Semantics

Denotational semantics are where the semantics of the program are equated or defined in relation to mathematics.

Most languages are described by operational semantics, but two languages in particular, [Standard ML](https://smlfamily.github.io/sml90-defn.pdf) and Haskell, are defined by denotational semantics. Given that these are functional languages, this is perhaps not surprising.

Denotational semantics describes the transformation from syntactic domain to the semantic domain. Each syntax phrase is *denoted* into a semantic evaluation.

As an example, this is a denotational transformation of a digits of a non-negative integer from its syntax form into its semantic form.

**Grammar**

**Semantic Types and Functions** 

The grammar is a typical BNF format for an integer.

The semantic functions take a syntax element parameter and describe its transformation to a semantic element. In this case, these functions parse a string to an integer. (There is no error handling, though that could be added for completeness if desired.)

:::callout{icon="ℹ️"}
This example was adapted from Chapter 9 of the book [Formal Syntax and Semantics of Programming Languages: A Laboratory Based Approach](https://homepage.divms.uiowa.edu/~slonnegr/) by Ken Slonneger
:::

As another example, the document for Standard ML describes the notation:

> Each rule of the semantics allows inferences among sentences of the form
> $A ⊢ phrase ⇒ A^{\prime}$
> where A is usually an environment or a context, phrase is a phrase of the Core, and A' is a semantic object – usually a type or an environment. It may be pronounced “phrase elaborates to A' in (context or environment) A”.

Here is a sample language construct in the premise/conclusion format for Standard ML.

$$
C \space ⊢ \space dec \space ⇒ \space E \space C \space ⊕ \space E \space ⊢ \space exp \space ⇒ \space τ \over C \space ⊢ \space \mathtt{let} \space dec \space \mathtt{in} \space exp \space \mathtt{end} \space ⇒ \space τ
$$

As far as I can tell, this premise is that a stand-alone type declaration in context $C$ results in a new type entry in the environment $E$, therefore the expression “let <declaration> in <expression> end” results in the same type. I am not positive on that, as I don’t know ML and haven’t read the report entirely.

## Conclusion

Neither of these formal semantics is perfect, but using symbolic logic, they can more precisely describe a language.

How category theory relates to semantics is not yet clear to me, but I suspect that category theory will provide constructs to denotationally describe programming languages. Further exploration will hopefully reveal the utility of these semantics.
