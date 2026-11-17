# Semantic Patterns for Factoid Extraction

## Overview
This document outlines common semantic patterns used in natural language to encode information, facts, and relationships. These patterns serve as the foundation for the **SemanticGoblin**, which will identify and extract structured knowledge from text.

## 1. Definitional Patterns
These patterns establish the identity, category, or nature of an entity.

- **Pattern:** `X is a/an Y`
  - *Example:* "A bat is a mammal."
  - *Encoded Fact:* `bat IS_A mammal`
- **Pattern:** `X is known as Y`
  - *Example:* "The red fox is known as Vulpes vulpes."
  - *Encoded Fact:* `red fox ALIAS Vulpes vulpes`
- **Pattern:** `X refers to Y`
  - *Example:* "The term 'quantum' refers to a discrete quantity."
  - *Encoded Fact:* `quantum DEFINITION discrete quantity`

## 2. Relational Patterns
These patterns describe connections, ownership, or composition between entities.

- **Pattern:** `The X of Y`
  - *Example:* "The capital of France is Paris."
  - *Encoded Fact:* `France HAS_CAPITAL Paris`
- **Pattern:** `X has Y`
  - *Example:* "The car has four wheels."
  - *Encoded Fact:* `car PART_OF four wheels`
- **Pattern:** `X belongs to Y`
  - *Example:* "This book belongs to the library."
  - *Encoded Fact:* `book OWNED_BY library`

## 3. Causal and Temporal Patterns
These patterns describe cause-and-effect relationships or sequences in time.

- **Pattern:** `Because X, Y`
  - *Example:* "Because it rained, the match was canceled."
  - *Encoded Fact:* `rain CAUSED match_cancellation`
- **Pattern:** `X leads to Y`
  - *Example:* "Poor diet leads to health issues."
  - *Encoded Fact:* `poor_diet CAUSES health_issues`
- **Pattern:** `After X, Y`
  - *Example:* "After the war, peace was declared."
  - *Encoded Fact:* `war PRECEDED peace_declaration`

## 4. Attribute and Property Patterns
These patterns describe characteristics, qualities, or states of an entity.

- **Pattern:** `X is Y` (where Y is an adjective)
  - *Example:* "The sky is blue."
  - *Encoded Fact:* `sky HAS_PROPERTY blue`
- **Pattern:** `X has Y` (where Y is a property)
  - *Example:* "The diamond has high hardness."
  - *Encoded Fact:* `diamond HAS_PROPERTY high_hardness`

## 5. Action and Event Patterns
These patterns describe actions performed by entities or events occurring.

- **Pattern:** `X does Y to Z`
  - *Example:* "The chef cooked the meal."
  - *Encoded Fact:* `chef ACTION cooked meal`
- **Pattern:** `X happens to Y`
  - *Example:* "An accident happened to the vehicle."
  - *Encoded Fact:* `vehicle EXPERIENCED accident`

## 6. Comparative and Superlative Patterns
These patterns describe relative qualities or rankings.

- **Pattern:** `X is more Y than Z`
  - *Example:* "The elephant is larger than the mouse."
  - *Encoded Fact:* `elephant SIZE > mouse SIZE`
- **Pattern:** `X is the most Y`
  - *Example:* "The cheetah is the fastest land animal."
  - *Encoded Fact:* `cheetah RANKED fastest land_animal`

## 7. Conditional Patterns
These patterns describe hypothetical scenarios or dependencies.

- **Pattern:** `If X, then Y`
  - *Example:* "If it rains, the ground gets wet."
  - *Encoded Fact:* `rain IMPLIES ground_wet`
- **Pattern:** `X unless Y`
  - *Example:* "We will go unless it rains."
  - *Encoded Fact:* `go_conditioned_on NOT_rain`

## Implementation Notes for SemanticGoblin
- **Uncertainty Handling:** The goblin should distinguish between observed statements and generally accepted facts.
- **Conflicting Relationships:** The system should be capable of expressing uncertainty and conflicting relationships (e.g., "A bat IS_A mammal" vs. "A bat IS_NOT_A bird").
- **Context Awareness:** Patterns should be extracted within their specific context to avoid misinterpretation.
