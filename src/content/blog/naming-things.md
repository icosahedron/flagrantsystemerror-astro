---
title: "Review of Naming Things by Tom Benner"
pubDate: 2024-11-27
updatedDate: 2024-11-29
description: "Billed as the solution to the hardest problem in Computer Science, it doesn’t quite deliver on that promise."
public: true
notionLastEdited: "2024-11-29T19:48:43.069000+00:00"
heroImage: "/images/covers/c43a0e443cb2.jpg"
heroImagePosition: 0.2
---
Billed as the solution to the hardest problem in Computer Science, it doesn’t quite deliver on that promise.

The book is brief and a quick read. It would be easy to dismiss it on these grounds, but the advice is solid, if well-worn.

Nothing in the book will surprise a senior engineer, but like many principles, repetition reinforces good practice.

The book is well organized, divided into two sections, Principles and Application. Perhaps the most impressive section is “Tradeoffs”, which balances the principles against each other.

### Principles

This is the direct copy from the book:

- Understandability - A name should describe the context it represents.

- Conciseness - A name should only use the words necessary to communicate the concept it represents.

- Consistency - Names should be used and formatted uniformly.

- Distinguishability - A name should be visually and phonetically distinguishable from other names.

The remaining chapters in this section take each principle and elaborate on its use, providing both good and bad examples.

### Application

How should these principles be applied, or to be more concrete, in which order should the principles be applied?

- Consistency is the most important. Inconsistency can violate 
  - understandability because when names are inconsistent each is a separate concept without a direct mapping.
  - conciseness because if two names represent the same concept, one of them isn’t the most concise.
  - distinguishability because a single name can represent more than one concept, or a single name can represent one or more concepts.

- Distinguishability is next most important because
  - understandability from a common name make actually represent multiple concepts, that need to be distinguished separately (e.g. email may be multiple things, whereas email_address is more distinguished)
  - conciseness can likewise cause the same term to represent multiple concepts.

- Understandability is more important than conciseness because
  - naming something that isn’t understood but short is pointless.

- Conciseness is preferred to limit the space, both code and head, of a concept.

The remaining chapters in this section detail examples of these applications of the principles from the previous section.

### Conclusion

What is a good name? The answer is “it depends.” Like [The Pirate’s Code](https://pirates.fandom.com/wiki/The_Pirates'_Guidelines), the points in this book are more guidelines, and there are always exceptions to the principles and applications.

Still, the book is worth the short read if it causes you to question if the name you chose is the right one.
