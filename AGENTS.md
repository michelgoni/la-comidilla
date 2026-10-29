# Working rules for this repository

This file is the contract between Michel (the owner) and any assistant or coding agent working here. Read it before touching anything.

## Who decides what

- **Michel decides.** Model, business rules, output format, what gets measured and what does not.
- **The assistant proposes.** It never implements a decision that is not written here or approved by Michel in conversation and recorded in `docs/decisions/`.
- If the assistant spots a missing decision, it **stops and asks**. It does not fill the gap on its own.

## The mandatory cycle

1. **Proposal.** The assistant writes what it plans to do, what it assumes and what it touches, in `docs/proposals/`.
2. **Review.** Michel reads it, argues and corrects. This step cannot be skipped. If a decision is not understood, the reason gets asked.
3. **Decision.** It is recorded in `docs/decisions/` with the date and the reasoning. What is not in a file does not exist.
4. **Implementation.** Only then does code get written in `src/`.
5. **Measurement.** It is checked against the exam in `labelled/` and the result is recorded.

## Language rules

- **Code, comments, folder names and file names are always in English.** No exceptions.
- **Project documentation is written in Spanish**, plain language, no acronyms and no opaque labels. That covers `docs/`, the README and the vault notes. If Michel asks for a document in English, that document is the exception and it is said so in its first line.

## Code rules

- Every function carries one line saying what it does and why it exists.
- No new dependency without a written decision.
- One program does one thing. If it does two, it is two programs.
- Secrets never live inside this folder. The environment file is `~/.hermes/secrets/comidilla.env` and it stays empty until a model call path is chosen.

## What is not done without permission

- Changing the model prompt.
- Changing the model.
- Editing the hand-labelled sheet.
- Running a new measurement. Every call costs money and time.
- Adding folders or files outside the structure below.
- Touching the source corpus. It is read only.

## Where everything lives

| Folder | What it holds |
| --- | --- |
| `docs/specs/` | What the system must do. Requirements and acceptance criteria. |
| `docs/proposals/` | Assistant proposals before implementation. |
| `docs/decisions/` | Decisions taken, with date and reasoning. |
| `src/` | The code. Empty for now. |
| `tests/` | Test code. Empty for now. |
| `prompts/` | Prompt versions. Each one numbered. |
| `labelled/` | The exam: hand-labelled reviews and every model result. |
| `data/` | Working data and old run outputs (`full_corpus.json`, `registry.json`, `selected.json`, `run_corpus.log`). |

The root only holds this file and `README.md`. Prompts live in `prompts/`, data in `data/`, the exam and model results in `labelled/`, code in `src/`.

## Domain rules that cannot be broken

These come from the labelling rubric. An agent that changes them changes the whole project.

- **Five aspects only:** food, service, price, atmosphere, wait. In Spanish: comida, servicio, precio, ambiente, espera. The words used in the data are Spanish, because the reviews are Spanish.
- **Three polarities only:** positive, negative, mixed. Mixed means the same aspect gets both a good and a bad face in the same review. A bad meal with good service is not mixed: it is two separate judgements.
- **The snippet is literal.** It is copied from the review character by character. If it is not found in the text, it is an invention and the result is wrong.
- **Precision over recall.** It is better to stay silent than to invent an aspect that is not there. The exam punishes invention more than omission.
- **Naming is not judging.** "The place has a terrace" is not an atmosphere judgement. "The terrace is lovely" is.
- **No judgement, no row.** A review can end with zero rows and that is correct.

## Source data

- Corpus: `/home/ubuntu/gastronomy/gilda-report/corpus_reviews.json`. Shape is `[place, stars, text]`. 1,522 reviews with text, 1,516 in Spanish. Read only.
- The exam: `labelled/reviews_to_label.json`, hand-labelled by Michel. Read only unless Michel asks for a correction.
- Model results: `labelled/result*.jsonl`, one line per review. These are outputs, not truth.
