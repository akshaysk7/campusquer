# campusquer
## Abstract

RAG SYSTEM WHICH ANSWERS QUESTIONS REGARDING THE CAMPUS WHICH ARE CITED FROM OFFICIAL CIRCULARS AND INFORMATION PROVIDED BY THE COLLEGE ITSELF. ONLY REAL AND OFFICIAL DATA. NO GUESSING/UNSURE ANSWERS. UNANSWERED QUESTIONS ARE DRAFTED INTO A FINAL REPORT WHICH CAN BE PRESENTED TO THE COLLEGE MANAGEMENT/DISCUSSION FORUMS FOR CONCLUSIVE ANSWERS


## The problem

Every student here has asked something already answered in a circular
posted six months ago — attendance rules, exam eligibility, revaluation
procedure. The information exists, it's just scattered across PDFs and
WhatsApp forwards. So students ask seniors, get wrong answers, and the
office fields the same twenty questions every week.

## What it does

Ask a question in plain English, get the answer with the source circular
cited. Ask ChatGPT about attendance thresholds and it'll confidently give
you the common norm — which may be wrong for this college. This only
answers from official documents.

## The part that matters

When the documents don't cover a question, it says so instead of
inventing an answer. And we log every one of those failures — which
turns the system into a documentation-gap report showing which questions
students keep asking that nobody has documented.

That reframe came from a criticism during our pitch, not from the
original idea.

## Approach

Document ingestion and chunking → embeddings → vector search for
retrieval → LLM generating answers grounded strictly in retrieved
sources, with metadata for citation.

## Status

In progress — semester minor project, team of three.

`Python` `embeddings` `vector search` `RAG`
