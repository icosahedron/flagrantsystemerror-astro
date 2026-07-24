---
title: "Category Theory: What Is A Category?"
pubDate: 2024-11-29
description: "From a functional programming perspective, category theory is a branch of mathematics that serves a purpose similar to what patterns do in object-oriented pr…"
---
From a functional programming perspective, category theory is a branch of mathematics that serves a purpose similar to what patterns do in object-oriented programming. That is, categories provide a set of patterns or ideas that provide implementation recipes. This is an opinionated definition that will hopefully bear out in future articles.

## Categories and Functional Programming

Functional programming is becoming more popular, and with it has come a new vocabulary. Words like monad, endofunctor, and monoid cause software engineers to scratch their heads in confusion.  For most of us these words are new and unique, without analogs to the real world. They are mathematical terms that aren’t used much outside that domain.

At first examination, it seems to me that using these mathematical terms are the approximation of patterns that object-oriented languages use (e.g., The Gang of Four Patterns). They describe constructs used frequently in functional programming the same way that Observer and Visitor might be used C++ or C#. (We’ll see if that definition holds up as I progress.)

## Category Theory for Programmers

There are many resources available to learn category theory, but one such resource is aimed at programmers.  [*Category Theory for Programmers*](https://bartoszmilewski.com/2014/10/28/category-theory-for-programmers-the-preface/) is an online book by Bartosz Milewski.  It can be freely read, though there is a dead tree version if that is your preference.

I have started the book a few times, but that format didn’t speak to me for some reason. Through the book and website though I discovered the [video series](https://www.youtube.com/playlist?list=PLbgaMIhjbmEnaH_LTkxLI7FMa2HsnawM_).  I find it much more approachable and so far has been my primary way to learn category theory.

These posts are mostly summarized from the video series, supplemented with some additional material that I found helpful.

### Math Required?

I am not a mathematician by trade or even experience, but you could say that I’m an enthusiast. Category Theory doesn’t require, at least so far in my studies, much math beyond high school level.  Logic is helpful too.  When appropriate, the logic will be explained, which mostly entails describing how the symbols map to English.

Category theory, and this video series in particular, displays what is so neat about math.  

As Keith Devlin explains in his *Mathematical Thinking* book, math learned in higher education is different from the math in elementary education. It primarily differs by moving from *calculation* to *conceptual*.  That is, rather than using math as a tool, we begin to use it for understanding.

### Functions as Concepts

A good example is the evolution of the *function.* A function as a calculation tool is an equation:

$f(x) = x^2 + 3x - 5$

But as a conceptual topic, a function can be almost anything. As an example, a function can be described in plain language:

$f(x) = \begin{cases} 1 &\text{if } x &\text{is rational} \\ 0 &\text{if } x &\text{is irrational} \end{cases}$ 

The former is used to compute values.  The latter is a concept for mapping numbers to booleans.  As Mr. Devlin says, “Try graphing that monster [function]!”.

:::callout{icon="ℹ️"}
Keith Devlin’s book on [Mathematical Thinking](https://www.goodreads.com/book/show/16010552-introduction-to-mathematical-thinking) is a pretty good introduction to making this transition, though I am still working my way through it.
:::

## What is a Category?

Starting at the very beginning, what *is* a category?

First, what it is not.  A category is not just a set (as in set theory). A set can be a category, and its elements are the objects in the category, but categories are not necessarily sets. Though sets-as-categories is often a convenient way to explain them.

Categories are defined by two things:

- Composition 

- Identity

But composition of what? And identity of what?

### Objects in a Category

A category is a group of *objects* or *things, *or as described in the videos, a *bunch*.  A category is not a group in the mathematical sense. 

What is an *object*? It’s not really defined.  We know it’s there, but category theory does not attempt to define it beyond “it’s what is in the category”.  

An object has no properties or attributes that are important within category theory.

### Functions in a Category

In category theory, a function (also known as a morphism) is a transformation between two objects in the categories. So if a category is a *bunch of objects*, a function takes *something* that is in that bunch and transforms it into something else that is in another category (or technically, it can be in the same category).



:::figure{src="/images/posts/ff04536ecd3b.png" alt="Figure 1, functions f and g map objects between categories A and B."}
**Figure 1,** functions f and g map objects between categories A and B.
:::
When diagramming, functions are represented as directed arrows, as in Figure 1.  It is important that they show as directed.  Functions are one way.  You give it an argument, it returns a result.  If you give the result back to the function, you don’t get the original argument, you get another result.

In the diagram above, we see that $f(x)$ and $g(x)$ must be different functions because for the same object in A, they return different objects in B.

While some functions have an inverse, the inverse function is a function in its own right and would be represented with a separate arrow back to the original object.

Functions have a domain, a codomain, and an image. In the parlance of sets, the domain is the set that has valid elements for parameters to the function. The codomain is the set that has valid values returned by a function as elements.  And an image is the actual elements in the codomain that a function will return.

Wikipedia’s example of a domain, codomain, and image using sets:

> For a function $f: ℝ \to ℝ$, defined by $f : x ↦ x^2$, or equivalently $f(x) = x^2$, 
> the codomain of $f$ is ℝ, but $f$ does not map to any negative number. Thus the image of $f$ is the set $R_0^{+}$, i.e., the interval $[0,\infin)$.

:::callout{icon="📡"}
This [answer](https://math.stackexchange.com/questions/97390/function-theory-codomain-and-image-difference-between-them) on Math Stack Exchange does a good job of explaining the differences between codomain and image. Codomains are specified for a function, and can not generally be inferred from the function alone.
:::

Not every object in a category needs to have a morphism between every other object in another category. Functions can be selective, or even infinite. There could be infinite number of functions between two objects.

:::callout{icon="📡"}
Interesting side fact: Two functions between the same objects are **not** considered isomorphic.  They are different functions. (Citation needed.)
:::

## Identity

Knowing what a function is, we refer back to our definition of a category, and tackle the identity.

Each object in a category has an identity function. This function simply maps any object in the category back to itself.

:::figure{src="/images/posts/360d805f2600.png" alt="Figure 2 Identity functions for objects in the category represented as arrows that map back to the original object."}
**Figure 2** Identity functions for objects in the category represented as arrows that map back to the original object.
:::
In the category above, each object has an $id$ function, which returns the object itself, essentially $id(x) = x$.  In code the equivalent is 

```python
def id(x):
	return x
```

In a category, each object *must* have an identity function. Otherwise, it is not a category.

An example of an identity function would be adding 0 or multiplying by 1 if your objects were numbers.

## Composition

Besides identity, categories must have composition.  Composition is the concept of two functions *composed* by using the result of the first function as the input to a second function, etc.  It is commonly expressed as $g(f(x))$ or $g \circ f$, both of which read “g after f”.

In code this would look similar to:

```python
def compose(f, g, x):
	return g(f(x))

def inc(x):
	return x + 1

compose(inc, inc, 1) # evaluates to 3
```

Where there is any function between two objects in category A and category B, and a function between the same object in category B and another object in category C, there *must* be a function which maps the object in category A to the object in category C, as shown in Figure 3. This function is always named “second function after first function”.

:::figure{src="/images/posts/703c013b8571.png" alt="Figure 3 If a function exists from an object in A to an object in B and one from that object in B to an object in C, then a function must exist from the object in A to the object in C."}
**Figure 3** If a function exists from an object in A to an object in B and one from that object in B to an object in C, then a function must exist from the object in A to the object in C.
:::
### Composition and Associativity

What about composing more than 2 functions?  What about a category D with a function $h$ from the object in C?  That would look like $h \circ g \circ f$, as you would expect.

Composition is associative, like addition or subtraction, meaning it doesn’t mean how the operations are grouped.  $(h \circ g) \circ f$ is the same as $h \circ (g \circ f)$ which is the same as the above without parentheses.

### Identity and Composition

When an identity function is composed with any other function, it simply maps to that function, as such $id \circ f = f$.  As one would expect, $id$ can be composed infinite amount of times and it will always return its argument.

## Category Theory and Information Hiding

In programming, we strive for information hiding. We hide implementation details about an object (or module or structure) behind interfaces of functions or operations for a variety of reasons.

In categories, objects are also hidden. We know they’re there, but we don’t know anything about them, *except the functions which can operate on them.*

We abstract away the details of the objects themselves, and only look at the functions that can interact between objects.  

Already we see that categories in mathematics can help model one aspect of programming.
