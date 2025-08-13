# Cedar CLI Context for AI Agents

## What is Cedar CLI?

The Cedar CLI (`cedar-os-cli`) is a command-line tool that creates and manages Cedar-OS projects. 

## Key Command: `npx cedar-os-cli plant-seed`

**CRITICAL: This command creates a COMPLETE project, not just installs packages!**

### What `plant-seed` Does:

1. **In an empty folder**: Creates a full project from scratch
   - Offers template selection (Mastra template recommended)
   - Creates project structure
   - Sets up demo frontend (Next.js/React) with Cedar pre-integrated
   - Initializes Mastra backend with Cedar-OS
   - Installs all Cedar packages and dependencies
   - Provides working example components

2. **In an existing project**: Adds Cedar to the project
   - Detects existing framework
   - Integrates Cedar components
   - Installs all Cedar packages

## Important Rules for AI Agents:

### DO NOT:
- Create a Next.js project first (plant-seed creates it)
- Run `npm install cedar-os` or any Cedar packages directly
- Use `create-next-app` before running plant-seed
- Assume the user needs to set up a project manually

### ALWAYS:
- Call `checkInstall` tool first when starting Cedar work
- Use `npx cedar-os-cli plant-seed` for initial setup
- Let plant-seed create the entire project structure
- Trust that plant-seed provides a complete, working application

## Project Structure After plant-seed:

```
my-cedar-project/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main page with Cedar components
│   └── api/               # API routes integrated with Mastra
├── components/            # Cedar components pre-configured
├── lib/                   # Cedar utilities and configuration
├── mastra/               # Mastra backend with Cedar-OS
│   ├── agents/           # AI agents configuration
│   └── workflows/        # Workflow definitions
├── package.json          # All Cedar dependencies included
└── cedar.config.js       # Cedar configuration
```

## Common Misconceptions to Avoid:

1. **Misconception**: "I need to create a Next.js project first"
   **Reality**: plant-seed creates the entire project

2. **Misconception**: "I need to install Cedar packages with npm"
   **Reality**: plant-seed installs all Cedar packages

3. **Misconception**: "Cedar CLI just installs packages"
   **Reality**: Cedar CLI creates a complete, working application

## Correct Flow:

1. User wants to set up Cedar in empty folder
2. AI calls `checkInstall` with context='starting Cedar integration'
3. AI receives instruction to run `npx cedar-os-cli plant-seed`
4. User runs the command
5. User gets a complete project with frontend + backend
6. No additional setup needed - project is ready to run

## Template Options:

When running plant-seed, users can choose from:
- **Mastra Template** (RECOMMENDED): Full-stack with Mastra backend
- **Next.js Template**: Frontend-focused with Next.js
- **React Template**: Basic React setup
- **Custom**: Manual configuration

The Mastra template is recommended as it provides the most complete setup with the least configuration needed.