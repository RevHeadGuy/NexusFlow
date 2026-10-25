export const PROJECT_TEMPLATES = [
  {
    key: "saas_mvp",
    name: "SaaS MVP",
    description: "Scope a focused first version of a software product.",
    projectName: "SaaS Product MVP",
    idea: "Build a focused SaaS product that helps small teams manage a recurring workflow currently handled across spreadsheets and chat. The first release should support a small set of core users, a clear onboarding path, and one measurable outcome. Define the essential user roles, data that must be retained, and the integrations required for launch. Keep the MVP narrow enough to validate with a handful of design partners before expanding the feature set.",
  },
  {
    key: "internal_tool",
    name: "Internal Tool",
    description: "Plan a secure workflow tool for an existing team.",
    projectName: "Team Operations Tool",
    idea: "Create an internal tool for a team that currently coordinates a recurring operational process by email and spreadsheets. Identify the people who create, review, and approve work; map the current handoffs; and reduce missed updates. The first version must fit the team's existing access rules, preserve an audit history, and make ownership clear. Define the smallest pilot workflow and how the team will know it is faster and more reliable.",
  },
  {
    key: "research_prototype",
    name: "Research Prototype",
    description: "Validate an uncertain concept with explicit evidence and assumptions.",
    projectName: "Research Prototype",
    idea: "Explore a prototype for a new product concept where the main user need and technical approach still need validation. State the problem as a hypothesis, list the people who should be interviewed or observed, and define what evidence would support or disprove the idea. Keep the prototype small, avoid collecting unnecessary personal data, and define the learning goals before implementation. Record assumptions separately from findings and decide what result would justify a larger build.",
  },
] as const;

export const WORKFLOW_TEMPLATES = [
  {
    key: "full_product",
    label: "Full product journey",
    description: "Run all six review stages from discovery through final package.",
    stagePlan: ["idea_discovery", "market_research", "technical_feasibility", "prd_architecture", "quality_review", "final_approval"],
  },
  {
    key: "lean_mvp",
    label: "Lean MVP",
    description: "Focus on brief, feasibility, requirements, and a final review.",
    stagePlan: ["idea_discovery", "technical_feasibility", "prd_architecture", "final_approval"],
  },
  {
    key: "validation",
    label: "Idea validation",
    description: "Focus on discovery, evidence planning, and feasibility.",
    stagePlan: ["idea_discovery", "market_research", "technical_feasibility", "final_approval"],
  },
] as const;
