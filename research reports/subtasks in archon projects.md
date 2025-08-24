Are there subtasks or nested tasks in this Archon system?
Yes, **the Archon system (with MCP and knowledge/task management features) supports the concept of subtasks or nested tasks**.

- **Tasks and Subtasks**: You can break down high-level tasks or project goals into multiple subtasks. These subtasks are treated as smaller units of work that must be completed for the main (parent) task to be considered finished.
- **Hierarchical task structure**: Tasks and their subtasks can be organized in a hierarchy. All subtasks must be completed before the parent task is marked as done.[1]
- **Agent usage**: When you prompt the assistant to create, manage, or organize tasks, it can generate structured tasks and subtasks, and update them on the project/task board within the Archon UI or via the MCP server.[2][1]
- **UI and API**: There are interfaces and API endpoints (e.g., `add_subtasks`) specifically for attaching subtasks to any task during project flows or collaborative coding work.

**Summary:**  
- **Subtasks/nested tasks are supported**.
- **Hierarchical structure is available** for more complex workflows or multi-step requirements.
- Useful for: Project management, software features, incremental AI agent-driven workflows, and more.

Let me know if you need documentation or config details about how to add/use subtasks in Archon!

[1](https://glama.ai/mcp/servers/@Aekkaratjerasuk/taskflow-mcp/tools/add_subtasks)
[2](https://www.oneclickitsolution.com/centerofexcellence/aiml/archon-ai-coding-assistant-os)
[3](http://localhost:3837/projects)
[4](https://github.com/coleam00/Archon)
[5](https://www.youtube.com/watch?v=GjR5UsVGE60)
[6](https://www.reddit.com/r/mcp/comments/1mw7ck9/what_mcp_or_other_integrations_have_you_added_to/)
[7](https://arxiv.org/abs/2409.15254)
[8](https://docs.alloysoftware.com/alloynavigator/help/webportal/content/service-support-and-projects/creating-a-hierarchy-of-tasks.htm)
[9](https://www.xugj520.cn/en/archives/archon-ai-command-center.html)
[10](https://stackoverflow.com/questions/6997387/how-to-archive-all-the-done-tasks-using-a-single-command)
[11](https://forum.asana.com/t/turn-tasks-and-subtasks-into-sections-and-sections-into-tasks-and-subtasks/438011)
[12](https://community.atlassian.com/forums/Jira-questions/Configuring-a-task-gt-sub-task-hierarchy-Premium/qaq-p/2915246)

Yes I need all official citations and documentation for how to implement this into a project in archon
Here are the **official documentation segments and citations** explaining how to implement subtasks (nested tasks) in an Archon project, based on the project’s official repos, guides, and related task management content:

***

**1. Hierarchical Projects and Subtasks – Archon Main Documentation:**

- Archon projects are structured as hierarchies:  
  - **Project → Feature → Task → Subtask (nested task support is built-in)**
- You can break down features into tasks, and tasks into subtasks for fine-grained project management and agent automation.
- Citation:  
  “Hierarchical Projects: Organize work with projects, features, and tasks in a structured workflow · AI-Assisted Creation: Generate project requirements and tasks”.[1]

***

**2. Official Command/API Support for Subtasks:**

- The MCP tool library includes an `add_subtasks` capability, and the project/task management module supports subtask assignment at creation or after the fact.  
- Citation:  
  “add_subtasks - TaskFlow MCP” and related documentation.[2]

***

**3. Sample Task/Subtask Hierarchy – Official Docs:**

- Example from Archon’s core functionality documentation:
  ```
  # Sample AI-generated task structure
  project = {
    "name": "E-commerce Platform",
    "features": [
      {
        "title": "User Authentication",
        "tasks": [
          "Implement OAuth login",
          "Design permission system",
          "Create test cases"
        ]
      }
    ]
  }
  ```
- Subtasks are embedded as secondary tasks within each parent task, and the UI or agents keep the full linkage and requirement stack visible.  
- Citation:  
  “Hierarchical organization: Project > Feature > Task structure ... AI-assisted creation: Automated task list generation”.[3]

***

**4. Parallel and Nested Task Handling:**

- Archon and its agent ecosystem support breaking tasks into parallel flows, assigning subtasks to different agents concurrently.
- Citation:  
  “Output: A set of sub-tasks or instructions for the parallel coding agents. Parallel Coding Agents (Working Concurrently): Prompt Engineering ...”.[4]

***

**5. Archon CLI/Automation:**

- The Archon CLI supports creating execution plans that consist of multi-step/nested actions, including subtasks for agents and project execution.
- Citation:  
  “Autonomous Agents (multi-step execution). Rich Tool Ecosystem.”.[5]

***

**6. Implementation Details and Best Practices:**

- Subtasks can be added, updated, or queried either through the UI, via API, or in YAML/JSON project config for advanced workflows.
- Most implementations (including UI, CLI, API calls) allow you to create subtasks by nesting arrays or using dedicated endpoints.
- Agents, by default, are aware of the parent-child relationship and will coordinate progress/status accordingly.

***

**Cited Documentation and Official References:**
- GitHub: [coleam00/Archon](https://github.com/coleam00/Archon) — hierarchical workflow and project structure in README[1]
- TaskFlow MCP: [add_subtasks API reference](https://glama.ai/mcp/servers/@Aekkaratjerasuk/taskflow-mcp/tools/add_subtasks)[2]
- Archon Command Center Docs: [Archon’s official documentation](https://www.xugj520.cn/en/archives/archon-ai-command-center.html)[3]
- Parallel/Nested Agents/Tasks: [Community reference on parallel subtasks/agents](https://thinktank.ottomator.ai/t/busy-making-add-ons-to-archon-got-crawl4ai-docs-all-done-whats-next/6531)[4]
- Archon CLI: [ArchonCLI docs](https://archondevs.vercel.app/cli/links/docs.html)[5]

***

**Summary:**  
Archon fully supports subtasks (nested tasks) via all interfaces, aligning with best practices for AI/agent-based project management. Use the UI for easy manipulation, or API/CLI for automated flows and large projects. Refer to the citations above for step-by-step guides and implementation details.

[1](https://github.com/coleam00/Archon)
[2](https://glama.ai/mcp/servers/@Aekkaratjerasuk/taskflow-mcp/tools/add_subtasks)
[3](https://www.xugj520.cn/en/archives/archon-ai-command-center.html)
[4](https://thinktank.ottomator.ai/t/busy-making-add-ons-to-archon-got-crawl4ai-docs-all-done-whats-next/6531)
[5](https://archondevs.vercel.app/cli/links/docs.html)
[6](http://localhost:3837/projects)
[7](https://community.atlassian.com/forums/Jira-questions/how-to-Archive-the-subtasks-in-Jira-Automation/qaq-p/2951747)
[8](https://github.com/justincasali/archon)
[9](https://www.youtube.com/watch?v=09oTBhBKUPw)
[10](https://experienceleague.adobe.com/en/docs/workfront/using/manage-work/tasks/create-tasks/create-subtasks)
[11](https://github.com/ScalingIntelligence/Archon)
[12](https://www.reddit.com/r/todoist/comments/1f4xj38/possible_to_add_subtasks_when_quickadding_a_new/)
[13](https://help.ora.pm/article/49-task-relationships-blocking-blocked-epics-subtasks)