# Policy for AI-Generated Code

## Introduction and Purpose

This policy outlines the guidelines for using Artificial Intelligence (AI) generated code within this repository. As AI tools become increasingly common, we aim to ensure transparency, maintain code quality, and stay consistent with Red Hat's internal AI policies. This document applies only to this repository and complements, but does not replace, Red Hat's official AI policies and guidelines.

## What is AI-Generated Code

Any code, snippet, configuration, documentation, or other programmatic asset produced, suggested, or significantly modified by an AI model, tool, or service (e.g., GitHub Copilot, ChatGPT, etc.). Code that is directly used or heavily adapted from AI output qualifies as AI-generated.

## Transparency and Disclosure

All contributors must disclose the use of AI tools when submitting AI-generated code.

**Explicit Attribution**: When a Pull Request (PR) or commit includes nontrivial or substantial AI-generated content (e.g., functions, methods, classes, or multi-file changes), indicate this in the commit message and PR description.

Example Commit Message/PR Description:

```
header          <- Limited to 72 characters. No period.

                 <- Blank line

message         <- Any number of lines, limited to 72 characters per line.

                 <- Blank line

Assisted-by:    <- Name of AI model/tool used
   OR
Generated-by:   <- Name of AI model/tool used
```

**Originality**: If AI was used only for brainstorming, refactoring, or inspiration, and the final code is substantially original and reviewed by the contributor, a general disclosure in the PR description is sufficient.

## Licensing and Copyright

Contributors are responsible for ensuring AI-generated code complies with this project's license and Red Hat's copyright and AI guidelines. Do not assume AI-generated code is free from copyright obligations. Treat it with the same diligence as third-party code. If there's a risk of training data leakage or unclear licensing, investigate or rewrite the code before submission.

## Code Quality, Review, and Testing

AI-generated code must meet the same quality, testing, and review standards as human-written code.

* **Human Review Required**: All AI-generated code must be reviewed and understood by the contributor and reviewers.
* **Understanding is Key**: Do not submit code you cannot explain, modify, or debug yourself.
* **Iterative Refinement**: AI tools are assistants, not replacements for human judgment.

## Enforcement and Dispute Resolution

Non-compliance with this policy may result in PR changes or rejection. Questions or concerns about AI-generated contributions will be discussed and resolved by the maintainers.

## Disclaimer

This policy is a living document and will be updated as AI technology evolves and best practices emerge. Contributors are encouraged to provide feedback and suggestions to improve this policy over time.

