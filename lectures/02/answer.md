# Lecture 02 Answers

## Exercises

- Model and settings used (from `config` in `result.json`): `Qwen/Qwen3.5-0.8B`, 20 epochs, lr=0.0002, lora_r=16, lora_alpha=32
- Did you run training yourself (`executed_training_myself`): Yes
- Before training: `format_rate` = 0.95 / `content_rate` = 0.38
- After training: `format_rate` = 1.00 / `content_rate` = 0.86
- Questions that regressed: None
- Failures remaining after training and their types (assertion without evidence / evasion through a confirmation request despite evidence being present / broken format): Primarily unsupported assertions for out-of-FAQ questions (asserting fictional answers instead of recognizing missing evidence).
- Results of knowledge questions (section 6; classification before → after training) and observations: Before training outputs were mostly 'asserted'. After training, the model still confidently 'asserted' answers to out-of-FAQ knowledge questions. It learned the format but not the boundary of its knowledge.
- What changed and what stayed the same with training: Format compliance perfectly improved to 100%. However, the tendency to hallucinate unsupported facts instead of requesting confirmation remained the same.

## Homework

- Level attempted: Advanced (Custom Glossary Fine-Tuning)
- Settings or data changed: Swapped the FAQ for a `glossary.json` dataset (116 examples), trained for 5 epochs, and evaluated on custom glossary vs out-of-glossary queries.
- Results (comparison tables or numbers): The model perfectly recalled exact glossary definitions and adapted to rephrased queries, but it confidently hallucinated definitions for completely unrelated terms (like grading curves and office hours).
- Discussion of when fine-tuning is and is not suitable: Fine-tuning is excellent for teaching a model specific formats, tones, and structural behaviors (like JSON outputs). It is NOT suitable for injecting dynamic factual knowledge, as the model cannot easily distinguish between known facts and guesses, leading to confident hallucinations. A search-based system (RAG) is far more appropriate for factual retrieval since it relies only on retrieved text, guarantees zero hallucinations for missing facts, and allows instant updates without retraining.

### Discussion: Fine-Tuning vs. Glossary Search (RAG)

*(Write your discussion here based on the results)*

**Pros of Fine-Tuning:**
Perfect Recall of Trained Concepts: The model flawlessly memorized the exact glossary definitions and was even able to apply them to rephrased questions (e.g., answering correctly when asked to explain "AI engineering" in other words).
Format Consistency: The model learned the exact style and tone of the training data.

**Cons of Fine-Tuning:**
* Confident Hallucinations: When asked about out-of-glossary topics (like the grading curve or office hours), instead of admitting it didn't know or requesting confirmation, the fine-tuned model confidently invented definitions that sounded like glossary entries.
* Hard to Update: If a definition changes, you have to recreate the dataset and run the training process all over again.
* Knowledge Blending: The model struggles to separate its pre-existing general knowledge from the highly specific fine-tuned knowledge, leading it to force a fit where none exists.

**Pros of a Search System (Retrieval-Augmented Generation / RAG):**
* Reliable "I Don't Know": If a student searches for "grading curve" and it's not in the glossary, the search returns nothing, allowing the system to accurately say "I don't know" or "Confirmation is needed."
* Zero Hallucination on Missing Facts: Because the model relies only on the retrieved text in its prompt, it won't invent fake definitions.
* Instant Updates: You can simply update the glossary.json file, and the system instantly uses the new information without any retraining.
