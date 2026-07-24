---
title: "Probability: Fundamentals"
pubDate: 2025-12-10
updatedDate: 2026-07-23
description: "Probability deals with likelihoods of events occurring or a member of a population matching some criteria. For example, given a fair coin, 50% of the time it…"
heroImage: "/images/covers/cf33f8697d93.jpg"
heroImagePosition: 0.3394
---
## Probability: Fundamentals

Probability deals with likelihoods of events occurring or a member of a population matching some criteria. For example, given a fair coin, 50% of the time it should land on heads and 50% of the time it should land on tails each time it is tossed. Or, out of 100 people, if 50 like peanut butter sandwiches with grape jelly and the other 50 people like tuna sandwiches, what are the chances that one of the 100 people likes peanut butter sandwiches.

These are hardly tough questions, but when assessing risk in insurance or finances, probability is the math that is used to determine the risk involved.

## Sets

The groups of people that we measure above are mathematical objects called *sets*. A set is simply a collection of objects that have a similarity. In our first example, the coin toss, there are two sets, each with one member for each possible outcome, heads or tails. In our second example, the sandwich samples, there are again two sets, one that has the 50 people that like peanut butter and the other set has 50 people that like tuna.

### Notation

The notation for sets is pretty arbitrary. Each set is typically represented by a capital letter, or perhaps two letters. For our coin toss, heads would be *H* and tails *T*. But these are arbitrary. They could easily be *A* or *B, *though frequently the letters better represent the names of the sets.

If we want to say that a particular element is a member of a set, we use the symbol $\in$, like $x$ being in set $T$ as

$$
x \in T
$$

or John liking peanut butter sandwiches as

$$
John \in P
$$

To represent the probability of an event or membership in a set, we simply wrap the name of the set as P(name of set). So our sandwich set probabilities would be *P(P)* and *P(T), *for Peanut butter and Tuna respectively. Again, these letters are arbitrary, but the function P is standard way to express the probability.

### Empty Set

One special set is called the empty set, and its symbol is $\empty$. This is a set with no members. Usually sets like this aren’t represented with letters, as that rarely makes sense. But operations on sets, which we discuss below, can result in the empty set.

### Membership

A set is made of members, or *elements*. These elements are each unique. In numbers, this means that you don’t have the same number twice belonging to a set. For sandwich loving people, each person is only represented once.

For example with numbers, the set of integers between 1 and 5 can be expressed as {1, 2, 3, 4, 5}, with each element listed explicitly, or as { x | 0 < x ≤ 5}, which shows the conditions that match.

For example with sandwich loving people, we might say {Alice, Bob, Carmen, Doug}, but there really isn’t a way to otherwise specify.

## Subsets

Elements of sets only have distinct elements or members. In our sandwich set above, we use the criteria of types of sandwich to determine which set a person belongs to. 

But what if we had a shop that sold both peanut butter and tuna sandwiches? We could list the customers of that shop in a single set, simply people who like sandwiches from this shop. Let’s call it *S*. 

But isn’t it possible that someone who eats at our shop also likes both peanut butter and tuna sandwiches? Which set should we place them in then? Well, a single person can belong to both sets. And, since they buy sandwiches at our shop, they also belong to the larger set *S*. (What does it mean for a set to be larger or smaller than another set? That will be discussed in a later article.)

So, we have 3 sets, the set P of people who like peanut butter, T of people who like tuna, and S, of people who like sandwiches. As you can probably tell, people in T and people in P are also in S.

When a set is comprised of elements that are also in another set, such people who like tuna (T) also being people who like sandwiches (S), we say that T is a subset of S. 

This is hopefully apparent, since the people who like T also shop at the sandwich shop, so are therefore in S. For math reasons, if two sets are equal (have the exact same elements)then they are also subsets of each other.

## Union of Sets

So we have 3 sets for the sandwich shop:

- People who like our tuna sandwiches, T

- People who like our peanut butter sandwiches, P

- People who like one or both of our sandwiches, S

How do we express that S is the combination of P and T? This is the union operator.

$$
S = P \cup T
$$

This means that a new set is created by combining the elements of P with the elements of T.

Let’s say that T = {Alice, Bob, Carmen} and P = {Alice, Doug, and Emily}, so the union S would be {Alice, Bob, Carmen, Doug, Emily}. Notice that even though Alice is part of both P and T, she is only listed once in S. There are no duplicate elements in a set.

## Intersection of Sets

Again, we have the set of each sandwich type, T, and P. How do we show if there is any overlap between people who like peanut butter and tuna sandwiches. This is the intersection operator does, $\cap$. Let’s say that B is the set of people who like both tuna and peanut butter:

$$
B = P \cap T
$$

In our example above in Unions, the intersection of T and P would be *{ Alice }*, since she is the only one listed in both sets.

## Probability of Sets

All probability measurements are from 0 to 1, 0 being that there is no probability, 1 being a certain probability, and the ranges in between being the chance of the event.
