# Agent Studio

The Studio is the visual and orchestration layer for the controller.

Core rule: **one active site at a time**. A site must finish its workflow and pass verification before the queue advances.

Characters are UI representations of agents. The actual work remains controlled by GitHub Actions and authorized repository configuration.

Never place GitHub tokens or other secrets in public Pages files.
