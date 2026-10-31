# Design doc: permission-aware Enron mail assistant

## 1. Problem

Companies now put AI assistants over employees' mail and documents, for example Microsoft 365 Copilot, Gemini in Google Workspace and Glean. The assistant searches the company's data, then answers. Two failures are documented:

1. Oversharing. Search over a shared index can show a user mail they should not see. Access has to be enforced inside the search, not checked afterwards.
2. Mail as an attack. EchoLeak (CVE-2025-32711, June 2025) was a prompt injection in Microsoft 365 Copilot that needed no click. An attacker's email carried hidden instructions. When the victim later asked Copilot about internal data, Copilot read that email and leaked data through an image link that loaded by itself (source: arXiv 2509.10540).

The problem: build an assistant that answers a user's questions about their own mail, accurately, with citations, without ever showing another user's mail, and without being hijacked by what an email says. Each of those properties must be shown with numbers.

## 2. Requirements
Empty until decided.

## 3. Data
Empty until decided.

## 4. Access rule
Empty until decided.

## 5. Evaluation
Empty until decided.

## 6. Sizes and costs
Empty until decided.

## 7. Architecture
Empty until decided.

## 8. Security
Empty until decided.

## 9. Results
Empty until decided.
