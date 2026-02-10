# Agentic Research & Action Assistant

The Agentic Research & Action Assistant is an agentic system for document‑grounded analysis and research. It coordinates multiple specialized agents over a shared state to retrieve evidence from local documents, synthesize findings, and (when appropriate) produce structured outputs for human review.

This repository currently represents an initial scaffold and early‑stage project. The focus is on establishing a clear, extensible architecture rather than delivering a fully featured application.

---

## Core Components

- **Planner Agent**  
  Interprets the user’s goal, determines the desired output mode (e.g., analysis vs. email), and outlines the high‑level workflow for subsequent agents.

- **Researcher Agent**  
  Executes hybrid document retrieval (vector search plus keyword-based retrieval) over a local corpus, returning grounded evidence in the form of text chunks and associated citations.

- **Writer Agent**  
  Consumes the retrieved evidence and produces structured, human‑readable outputs while remaining strictly constrained to the provided documents.

- **Verifier Agent**  
  Checks that all claims in the final output are supported by the retrieved evidence, removing or flagging unsupported statements to maintain correctness.

- **Hybrid Document Retrieval**  
  Combines vector similarity search with keyword-based ranking to balance recall and precision, with support for contextual expansion via neighboring chunks.

- **Orchestration Layer**  
  Uses a graph‑based orchestration framework to connect the agents into a coherent pipeline (Planner → Researcher → Writer → Verifier) and manage the shared state.

- **Streamlit UI**  
  Provides a simple web interface for submitting tasks, triggering the pipeline, and inspecting outputs, evidence, and agent traces.

---

## Usage (Placeholder)

This project is not yet ready for general use. A typical interaction will eventually follow this pattern:

1. Review the sample documents provided in the repository, which serve as a non-confidential evidence base.
2. Start the application’s user interface.
3. Submit a research or analysis task.
4. Review the generated output, along with its supporting evidence and agent trace.

More detailed guidance on configuration, execution, and extension will be added as the project matures.