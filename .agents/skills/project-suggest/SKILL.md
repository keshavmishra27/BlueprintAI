---
name: project-suggest
description: Understands a developer's profile and suggests personalized projects optimized for resume gaps and hackathon competitiveness without accessing credentials.
---

# Project Suggest Skill

The goal of Project Suggest is to understand the developer from their resume, LinkedIn profile, and GitHub activity/projects, then recommend exactly:

1. ONE project optimized for strengthening their resume/portfolio.
2. TWO projects optimized for hackathon competitiveness.

The recommendations must be personalized to the developer's demonstrated skills, interests, existing projects, and missing portfolio signals.

Do NOT generate generic project ideas merely based on a list of technologies.

## 1. Developer Context

Build a Developer Profile using available evidence from:

### Resume

Analyze the user's resume when provided or accessible.

Extract:

* demonstrated technologies
* projects already built
* internships/work experience
* technical domains
* strongest engineering evidence
* weaker/missing engineering evidence
* repeated project patterns
* claimed skills that lack supporting projects

### LinkedIn

If the user provides a LinkedIn profile URL and current web access allows useful inspection, use publicly accessible information to enrich the profile.

Do not require LinkedIn access for the skill to work.

Do not fabricate information when LinkedIn content cannot be accessed.

### GitHub

When GitHub/repository information is available through safe host capabilities, inspect relevant public/user-authorized repository information such as:

* repositories
* languages
* project descriptions
* README files
* architecture/technology evidence
* recent meaningful activity
* repeated technologies/project types

Do not evaluate a developer merely from GitHub contribution counts.

Quality and technical evidence matter more than raw activity.

## 2. Credential Safety

NEVER read, expose, print, summarize, or reason about secrets or authentication credentials.

This includes:

* GitHub tokens
* API keys
* passwords
* `.env` secrets
* access tokens

Do NOT inspect `.env` to obtain a GitHub token.

Authentication must be handled by the host environment or an authorized integration/tool.

The skill should consume GitHub information, not credentials.

Never include private resume information, private repository contents, tokens, source code, or personal information in external web searches.

## 3. Developer Profile

Before generating projects, construct an internal profile containing:

### Demonstrated Strengths

Technologies/domains for which actual evidence exists.

### Claimed but Weakly Demonstrated Skills

Skills appearing in the resume/profile but lacking strong project evidence.

### Portfolio Saturation

Identify things the developer has already demonstrated repeatedly.

Examples:

* too many CRUD applications
* multiple RAG chatbots
* repeated dashboards
* several basic ML classifiers
* many similar agent wrappers

### Portfolio Gaps

Identify valuable engineering signals currently missing.

Examples may include:

* system design
* distributed systems
* asynchronous processing
* databases
* testing
* observability
* deployment
* security
* performance engineering
* real-time systems
* infrastructure
* production ML
* evaluation systems

Do not assume every developer needs every category.

## 4. Resume Project

Generate exactly ONE Resume Project.

The objective is:

"What single realistic project would add the most valuable NEW engineering evidence to this developer's existing profile?"

The Resume Project should:

* use a meaningful portion of the developer's existing stack
* introduce a small number of strategically useful new concepts
* avoid duplicating projects they already have
* fill an identifiable portfolio/resume gap
* be realistic enough to complete
* produce strong technical discussion points for interviews
* demonstrate engineering rather than merely API wrapping

Do NOT recommend a project solely because it uses the developer's strongest technology.

Explain exactly what missing signal the project adds to their resume.

## 5. Hackathon Projects

Generate exactly TWO Hackathon Projects.

These should optimize for:

* meaningful problem
* novelty/differentiation
* strong live demo
* technical depth
* feasibility during a hackathon
* clear story for judges
* alignment with the developer's existing skills
* potential for refinement into a serious project later

The two ideas must be meaningfully different from each other.

Do not produce two variations of the same concept.

Avoid generic ideas such as:

* generic AI chatbot
* basic RAG assistant
* generic recommendation system
* simple task manager with AI
* basic disease prediction
* generic resume analyzer

unless there is a genuinely unusual mechanism or problem framing that makes the project materially different.

## 6. Hackathon Reality Check

Do not call a project "hackathon winning" as a guaranteed outcome.

Instead evaluate its `Hackathon Potential`.

Winning depends on execution, judging criteria, competitors, presentation, and event-specific constraints.

If the hackathon theme, duration, judging criteria, or team size is provided, adapt recommendations accordingly.

If those details are absent, produce generally competitive software-project concepts and clearly state the assumptions.

## 7. Existing Project Awareness

Before suggesting anything, compare candidate ideas against projects the developer has already built.

Reject or substantially transform candidates that duplicate existing portfolio evidence.

The goal is not:

"What can this developer build?"

The goal is:

"What should this developer build NEXT?"

## 8. Scoring

Score each recommended project using evidence-backed dimensions.

### Resume Project Score

Score out of 100:

* Portfolio Gap Filled: /25
* Existing Skill Fit: /20
* New Engineering Signal: /20
* Interview Value: /15
* Feasibility: /10
* Differentiation From Existing Projects: /10

### Hackathon Project Score

Score each hackathon project out of 100:

* Problem Impact: /20
* Novelty / Differentiation: /20
* Demo Potential: /20
* Technical Depth: /15
* Feasibility: /15
* Developer Skill Fit: /10

For every score:

* explain important points gained
* explain important points lost
* include confidence: High / Medium / Low

Scores represent the BlueprintAI Project Suggest rubric only.

They do NOT represent probability of getting hired or winning a hackathon.

## 9. Evidence Discipline

Clearly distinguish:

**Verified Profile Evidence**
Information directly supported by resume, GitHub, LinkedIn, or user-provided context.

**Reasoned Assessment**
A conclusion inferred from that evidence.

**Assumption**
Something required for recommendation but not established.

Do not invent developer experience.

If LinkedIn or GitHub information cannot be accessed, continue using available evidence and explicitly state the limitation.

## 10. Output Contract

Produce:

### 1. Developer Snapshot

Summarize the developer's demonstrated technical identity.

### 2. Strongest Signals

What their current profile already proves.

### 3. Portfolio Gaps

What important capabilities are poorly demonstrated.

### 4. Project #1 — Resume Builder

Include:

* Project name
* One-sentence concept
* Problem
* Why THIS developer should build it
* Portfolio gap it fills
* Core architecture
* Existing skills reused
* New concepts learned
* MVP
* Advanced version
* Resume bullets this project could eventually support if actually implemented
* Score /100
* Confidence

### 5. Project #2 — Hackathon Candidate

Include:

* Project name
* problem
* target users
* key mechanism
* why it is interesting
* demo moment
* likely architecture
* 24-48 hour MVP
* major risk
* Hackathon Potential score /100
* Confidence

### 6. Project #3 — Hackathon Candidate

Use the same structure but make it meaningfully different from Project #2.

### 7. Why These Three

Explain why these projects were selected over more obvious ideas.

### 8. Recommended Order

Tell the developer which project to build first and why.

## 11. Completion

The skill is complete when it has produced:

* a developer profile grounded in available evidence
* one project filling a meaningful resume gap
* two distinct hackathon-oriented projects
* evidence-backed scores
* realistic MVPs
* and an explanation of why these projects are appropriate specifically for this developer
