For coding projects, here are the current best practices:

**Files to Keep in the Root Directory**
- Top-level configuration files (e.g., `README.md`, `.gitignore`, `LICENSE`, `package.json`, `requirements.txt`, `pyproject.toml`, etc.)
- Project documentation or main install/usage instructions (`README.md`, `INSTALL`, `WHATSNEW`)
- Project metadata or manifest files (e.g., `Cargo.toml`, `composer.json`, etc.)
- Tooling configs (`.eslintrc`, `.prettierrc`, `Makefile`, etc.)
- Legacy: for some frameworks, the main entry point (`index.js`, `main.py`), although even this is increasingly placed inside a dedicated directory (like `/src`)
  
**Files NOT To Keep in the Root Directory**
- Source code files (e.g., `.py`, `.js`, `.ts`, `.cpp`, etc. that are not configuration or project entry points)
- Compiled files, build outputs, or artifacts (`.o`, `.class`, binaries, or `.exe` files) — these should go under `/bin`, `/dist`, or `/obj`
- Tests and test data (`/tests`, `/spec`, etc.)
- Documentation files should be in `/docs`
- Miscellaneous configs and templates that pertain to features or modules, not the whole project, should go in `/config` or equivalent subfolders

Putting everything in the root is considered an anti-pattern in modern project organization. At a minimum, you should have a `/src` (source code), `/tests`, `/docs`, `/config`, and output folders appropriate for your build system.[1][2]

**Enforcing Project Rules in Cursor IDE or VS Code:**

- **Cursor IDE**:  
  - Supports rule files to enforce directory structure for AI agents and LLMs.
  - Use `.cursor/rules/` directory to place rule files, each in **.mdc** format.
  - You can create rules that specify where certain files must go using path globs, descriptions, and enforcement properties.
  - Nested `.cursor/rules/` in subfolders let you scope rules to certain directories.
  - To force AI agents to always follow these rules:
    - Create individual `.mdc` rule files for each best practice or directory standard.
    - Use the Cursor Rule Formatting Agent to help generate and maintain them.[3][4][5]
    - Outdated: the single `.cursorrules` file in the root directory; now, use multiple files in `.cursor/rules/`.

**Summary Table**

| In Root Directory              | Not in Root Directory                | How to Enforce (Cursor)      | How to Enforce (VS Code)          |
|-------------------------------|--------------------------------------|------------------------------|------------------------------------|
| README.md, .gitignore         | Source code files (`/src`)           | `.cursor/rules/*.mdc`        | ESLint, custom scripts             |
| package.json, Makefile        | Build outputs (`/bin`, `/dist`)      | Scope to directory/subfolder | Pre-commit hooks, linter plugins   |
| Top-level config files        | Documentation (`/docs`)              | Rule types: Always, Auto     | Husky scripts, CI enforcement      |
| Entry point (legacy only)     | Tests (`/tests`)                     | Nested `.cursor/rules/`      | VS Code Tasks, custom checks       |

If you want **strict structure enforcement** for AI/LLMs, Cursor’s `.cursor/rules/` system is the current best-in-class standard; for VS Code, use a combination of linter rules and automation scripts to guide or block misplacement.

create tasks in archon backlog for all step-by-step code for rule/linter creation that is not yet automated if any issue, problems or errors are found in the current implementation of the rules.

[1](https://www.embeddedrelated.com/showarticle/628.php)
[2](https://stackoverflow.com/questions/311257/is-it-ok-to-have-code-in-the-root-of-a-project)
[3](https://chatprd.ai/resources/PRD-for-Cursor)
[4](https://docs.cursor.com/context/rules)
[5](https://forum.cursor.com/t/how-to-force-your-cursor-ai-agent-to-always-follow-your-rules-using-auto-rule-generation-techniques/80199)
[6](http://localhost:3837/projects)
[7](https://www.reddit.com/r/learnprogramming/comments/1e5qs8w/do_i_save_my_code_to_my_root_folder_or_does_it/)
[8](https://stackoverflow.com/questions/902541/what-is-the-best-default-location-for-projects-in-visual-studio)
[9](https://martinctc.github.io/blog/rstudio-projects-and-working-directories-a-beginner's-guide/)
[10](https://www.youtube.com/watch?v=CAeWjoP525M)
[11](https://www.youtube.com/watch?v=G6Y33pwGcVc)
[12](https://discuss.codecademy.com/t/help-with-project-directory/589872)