# SQUAD

AI deepagents orchestration project for coding purposes.
Point of the project is to apply the best coding practices and reduce the cost by delegating to cheaper models and using less context.

## The loop

These rules are like a law in the system. They are the best programming practices:

- **Test driven development**, assume that the user cares only about the tests and will read tests primarily. Test everything that can be tested.
- **Focus before features**, or YAGNI, each task should be done with a focus to the task, each function should perform only the one job. Functions should be short, around 20 lines.
- **Self explanatory names, consistent style, readability**, for classes, interfaces, functions and variables.
- **No premature optimisation** - optimisation only if the task requires it or we are dealing with a system that is user-facing and with simple optimising we can gain on resource reduction thus cost reduction.
- **Prefer readability and composition over optimisation**
- **Prefer standard library and native code**
- **Declarative programming is preferred**, where applicable.
- **Immutability by default**

### Initial phase

Agent: supervisor

A task is given

Task can be performed over a repo GIT or if there is no repo a new project directory is created and the git repo is initialised.

Task can be a prompt, GitHub issue or a Linear issue. In order not to waste tokens we need a notation that can be parsed telling us whether it is an issue and what tool to reach.
`.env` will need both GitHub API and Linear API keys.

GitHub integration can use `gh` terminal commands, but we prefer API to lean onto the tool and reduce the usage of tokens.

Here is where the loop breaks into two possible loops, based on if the repo exists and we are doing work on existing code or we are creating a new project.

Prompt is then passed to a compressor agent. Compressor agent role is to review the textual prompt/issue. Improve the prompt by fixing typos, making sure it’s to the point and perform compression. (Maybe we need a better name, like scribe?)
Compressor should also provide one sentence summary if it’s a long prompt.

After the prompt is compressed the supervisor createas a git branch, names it based on the issue title or number, or one sentence summary prefixed by `squad/`, starts the discovery phase.

### Discovery phase

Agent: scount

Basic data collection about the project: Languages used (we should use a GitHub Linguist like tool to save on tokens), testing and linting tools, Readme (passed through compressor/scribe agent - to make it to the point and reduce token count)

We can store this data in `.squad` directory, but we should make sure it’s up to date before and after every loop is complete. This should be a job for scout.

Scout should then investigate the prompt and scout the codebase for the files that need updating, making a list.

If it is the new project, supervisor already initialised the repo. Scout performs web search.

#### Web search (scouting loop)

We need a web search tool, that will extract the text and links form the web page. We need only basic html like lists, blockqotes, links, anything that would make reading straightforward. We should have a tool to convert a html page contents to markdown notation. The scout does a google search, gets the results, decides if it wants to explore further. It makes a stack of links to read through.

Stack is fetched one by one, compressed by the compressor. and handed back to the scout. Scout then has to decide if the data fetched is useful or follow additional links per each fetch looping through it again.

If we are starting a new project we want to answer the following questions:

- What are the competitors and what could we do better?
- Is there a value in starting a project like this?
- Does the benefit match or exceeds the effort.

Scout then compiles a report combining all the data. Report is then sent to the compressor. Compressor tries to shrink it but keeping all the data related to the prompt.

Report is then stored as an `.md` file and logged in the filesystem. `.squad` directory should be used as a database ob jobs. We need a tool to log the prompt(issue) and assign a directory name to it. This is where the each job documents will be stored. If it’s a GitHub or a Linear issue we need to post the report as a comment as well. **Reports need to be in markdown notation.** Report should contain the language of the project, the most prominent language, and other minor languages. Testing and lint pipeline.

#### Note about the code style

Code style note should be a separate file. Based on the discovery we should manage it. It supplements the context. It contains the language, environment details, testing and linting pipelines types and execution info.

Report is then passed to the supervisor that initiates the coder.

### Coding phase

Agent: coder

Coder should be able to perform the tasks of coding with the tools to execute terminal commands related to the job it is performing.

Initial research should be regarded as a context. Code style note as well.

Task (initial compressed prompt or an issue) should be broken into granular steps.

Each step is a prompt (subprompt). **Eliminate contradiction**.

We need a tool that will stack these subtasks so the agent can access them one by one. Each subtask is a new context filled with only info from the initial report that aligns with the subtask. We can delegate the decision of what aligns to the compressor.

It should also be able to access other projects on the users machine and review the code if it’s useful. Try to find the functions that already solve the tasks, depending on the LICENSE.

Coder can issue another web search loop from the scout through the supervisor based on each step.

We want to know:

- If the functionality exists in the standard library?
- If the functionality exists as a quality maintained package?
- If we can do better - shorter localised code that follows **focus before features**, meaning if we can benefit from the localised simpler solution.
- Is there documentation of an existing solution? Read the code if there is no documentation or the documented solution doesn’t work.

The questions above are up to scout to answer and generate a subreport for each subtask. Passing it back to coder through the supervisor.

Coder does the code based on all subtasks. Upon completion of each subtask coder pings the supervisor to ping the reviewer.

### Reviewing phase

Agent: reviewer

Reviews the pending, not committed, code. Has access to the granular tasks of the coder and their initial context. Has access to the research docs and code notes.

Generates findings on what should be improved and passes them to the coder. Coder makes the update, reviewer compares it to the findings and signs it off.

Supervisor commits the code - commit message is the subtask prompt. Tells coder to resume, and so on until all of the subtasks are signed off.

All communication can be compressed, but maybe shouldn’t be between the coder and reviewer.

We should worry here not to make to many review loops. We need a system to limit the loops.

### Finishing phase

When all of the subtasks are done, coder reports to the supervisor.

Supervisor issues a scout to write the PR notes on what has been done and why, not compressed, it’s user facing.

PR is created. Loop is complete.

## Notes

- All the conversation must be logged in a big markdown file. Each role noted before the context.
- User should be updated through the CLI on what’s going on as well.
- Maybe worktree support is not needed? We should make it optional and not remove it. I’m thinking it’s we are rarely to use simultaneously run squad on the same codebase in parallel, but there are cases when we are touching different parts of the code.
