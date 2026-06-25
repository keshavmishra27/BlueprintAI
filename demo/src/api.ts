export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_KEY = import.meta.env.VITE_API_KEY || '';
export function getHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  };
}
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
export async function apiGet(path: string, _timeout = 900000): Promise<any> {
  await delay(800);
  if (path === '/assess/domains') {
    return [
      "Web Development",
      "Machine Learning",
      "Cybersecurity",
      "Cloud Computing",
      "App Development",
      "Agentic AI",
      "Healthcare IT"
    ];
  }
  throw new Error(`Mock GET for ${path} not implemented`);
}
export async function apiPost(path: string, data: any, _timeout = 900000): Promise<any> {
  await delay(1200);
  if (path === '/repo-judge/analyze') {
    return {
      student_name: data?.student_name || "Student",
      repo_url: data?.github_url || "https://github.com/demo/repo",
      total_score: 85,
      overall_score: 85,
      scores: {
        functionality: { score: 9, reasons: ["Core features work flawlessly."] },
        code_quality: { score: 9, reasons: ["Excellent code structure and naming conventions."] },
        documentation: { score: 8, reasons: ["README is thorough, but inline comments are sparse."] },
        architecture: { score: 8, reasons: ["Good separation of concerns, could improve modularity."] },
        testing_ci: { score: 7, reasons: ["Has unit tests but missing CI/CD pipeline."] },
        innovation_ux: { score: 10, reasons: ["Incredibly unique approach to the problem."] }
      },
      mentor_notes: "This is a fantastic repository. The code is clean and the problem you solved is highly relevant to today's market. With a few tweaks to your automated testing, this is a top-tier project.",
      strengths: [
        "Strong use of modern frameworks",
        "Clean folder structure",
        "Excellent use of async/await"
      ],
      top_issues: [
        { title: "Missing CI/CD", description: "Consider adding GitHub actions to automatically run tests." },
        { title: "Sparse Inline Comments", description: "Add JSDoc or docstrings to your main utility functions." }
      ],
      hackathon_recommendations: [
        { name: "Global Hackathon 2026", date: "July 2026", description: "A great fit for your tech stack.", registration_link: "#" },
        { name: "AI Innovators Challenge", date: "August 2026", description: "Perfect for AI-focused projects.", registration_link: "#" }
      ]
    };
  }
  if (path === '/project-suggest/suggest') {
    const query = (data?.themes?.join(" ") || "").toLowerCase();
    const themeName = data?.themes?.[0] || "Custom Themes";
    if (query.includes("health") || query.includes("med")) {
      return {
        theme: themeName,
        resume_projects: [
          { title: "Smart ICU Monitoring Agent", description: "An AI agent that monitors patient vitals and alerts staff to anomalies before they become critical.", tech_stack: ["Python", "TensorFlow", "React", "WebSockets"], why_great_for_resume: "Shows ability to handle real-time streaming data and critical systems." },
          { title: "AI Medical Record Summarizer", description: "Automatically extracts key insights and action items from lengthy patient history documents.", tech_stack: ["OpenAI API", "LangChain", "Next.js", "PostgreSQL"], why_great_for_resume: "Demonstrates NLP skills and working with unstructured enterprise data." }
        ],
        hackathon_projects: [
          { title: "Hospital Resource Prediction System", description: "Uses ML to forecast bed availability and staff requirements based on local health trends.", tech_stack: ["Python", "Pandas", "Scikit-Learn", "FastAPI"], why_it_wins: "Solves a real-world supply chain problem with clear ROI." }
        ],
        recommended_hackathons: [
          { name: "HealthTech Innovators 2026", date: "October 2026", description: "Build the future of healthcare.", registration_link: "#" }
        ]
      };
    }
    if (query.includes("cyber") || query.includes("security")) {
       return {
        theme: themeName,
        resume_projects: [
          { title: "Zero-Trust Network Analyzer", description: "Monitors network traffic for unauthorized lateral movement in real-time.", tech_stack: ["Go", "eBPF", "React", "ClickHouse"], why_great_for_resume: "Deep systems programming and high-performance network analysis." }
        ],
        hackathon_projects: [
          { title: "Automated Penetration Testing Agent", description: "An AI that autonomously probes web apps for common vulnerabilities (OWASP top 10).", tech_stack: ["Python", "Playwright", "LLMs"], why_it_wins: "High wow factor when the AI hacks a test site live on stage." }
        ],
        recommended_hackathons: [
          { name: "CyberSec Hackathon", date: "November 2026", description: "Protect the web.", registration_link: "#" }
        ]
      };
    }
    return {
      theme: themeName,
      resume_projects: [
        { title: "Automated Code Review Assistant", description: "An AI tool that reviews pull requests automatically.", tech_stack: ["TypeScript", "GitHub Actions", "OpenAI"], why_great_for_resume: "Shows deep understanding of CI/CD and developer workflows." },
        { title: "Decentralized Identity Provider", description: "A blockchain-based SSO solution for web3 apps.", tech_stack: ["Solidity", "Next.js", "Ethers.js"], why_great_for_resume: "Proves you understand modern auth and web3 architectures." }
      ],
      hackathon_projects: [
        { title: "Developer Portfolio Generator", description: "Instantly generates a stunning portfolio from a GitHub profile.", tech_stack: ["React", "Tailwind", "Vite", "GitHub API"], why_it_wins: "Everyone loves tools that save them time, incredibly relatable for judges." }
      ],
      recommended_hackathons: [
        { name: "Global Hackathon 2026", date: "July 2026", description: "A great fit for your tech stack.", registration_link: "#" }
      ]
    };
  }
  if (path === '/idea-validator/check') {
    const idea = (data?.idea || "").toLowerCase();
    if (idea.includes("ambulance") || idea.includes("health")) {
      return {
        gaps_and_loopholes: "Small city emergency coordination is a major gap. Current tools lack real-time hospital bed availability integration.",
        search_sources: ["Medical Journals", "Product Hunt", "Government Health Tech RFPs"],
        similar_projects: [
          { name: "Google Maps Emergency Routing", type: "Navigation SaaS", overview: "Provides fast routes for emergency vehicles.", relevance_score: 85, comparison: "They focus strictly on traffic routing, ignoring hospital capacity and bed availability." },
          { name: "Waze Emergency Services", type: "Navigation Tool", overview: "Crowdsourced traffic data for first responders.", relevance_score: 72, comparison: "Lacks deep integration with hospital ER admitting systems." }
        ]
      };
    }
    if (idea.includes("notes") || idea.includes("summary")) {
      return {
        gaps_and_loopholes: "The general AI note-taking market is heavily saturated. You must find a specific niche to succeed.",
        search_sources: ["Product Hunt", "Reddit r/productivity", "G2 Crowd"],
        similar_projects: [
          { name: "Otter.ai", type: "Transcription SaaS", overview: "General purpose meeting notes.", relevance_score: 95, comparison: "Massive market leader, very hard to compete on general features." },
          { name: "Fireflies.ai", type: "Meeting Assistant", overview: "AI assistant for zoom calls.", relevance_score: 90, comparison: "They dominate corporate meetings, but ignore niche physical workflows." }
        ]
      };
    }
    return {
      gaps_and_loopholes: "The current market lacks tools that integrate seamlessly with legacy enterprise systems.",
      search_sources: ["GitHub Repositories", "Product Hunt", "Hacker News Discussions"],
      similar_projects: [
        { name: "LegacyBridge", type: "Enterprise Tool", overview: "Connects old mainframes to modern APIs.", relevance_score: 85, comparison: "They focus on specific IBM systems, while your idea is more generic." },
        { name: "ApiWrap", type: "Open Source Library", overview: "Generates REST APIs from SQL databases.", relevance_score: 60, comparison: "Only handles databases, not arbitrary legacy protocols." }
      ]
    };
  }
  if (path === '/idea-validator/refine') {
    const idea = (data?.idea || "").toLowerCase();
    if (idea.includes("ambulance") || idea.includes("health")) {
      return {
        uniqueness: { verdict: "HIGHLY_UNIQUE", score: 88, rationale: "Combining navigation with real-time ER bed capacity is a highly novel approach that solves a real bottleneck." },
        refined_concept: {
          final_direction: "An ambulance routing system that dynamically redirects drivers to hospitals with confirmed open beds, rather than just the closest geographic hospital.",
          quick_win_variant: { description: "Build a prototype for a single city's dispatch center using simulated traffic and hospital capacity data." }
        }
      };
    }
    if (idea.includes("notes") || idea.includes("summary")) {
      return {
        uniqueness: { verdict: "LOW_UNIQUENESS", score: 35, rationale: "General AI note taking is a solved problem with massive incumbents." },
        refined_concept: {
          final_direction: "Pivot to a hyper-specific vertical: 'AI Notes for Veterinarians' that automatically understands animal breeds, standard dosages, and formats into veterinary compliance standards.",
          quick_win_variant: { description: "Build a mobile voice-memo app that outputs perfectly formatted SOAP notes for a single local vet clinic." }
        }
      };
    }
    return {
      uniqueness: { verdict: "MODERATELY_UNIQUE", score: 75, rationale: "While similar tools exist, your specific approach to arbitrary protocol parsing is novel." },
      refined_concept: {
        final_direction: "Focus on a visual protocol builder that lets enterprises map their legacy systems without writing code.",
        quick_win_variant: { description: "Build a command-line tool first to prove the parsing engine works." }
      }
    };
  }
  if (path === '/assess/generate-mcq') {
    const domain = (data?.domains?.join(" ") || "").toLowerCase();
    if (domain.includes("agentic")) {
      return {
        session_id: 201,
        questions: [
          { index: 0, question: "Which pattern allows an LLM to decide when and how to execute external functions?", options: ["Tool Calling / Function Calling", "Zero-Shot Prompting", "Retrieval Augmented Generation", "Fine-Tuning"], difficulty: "medium" },
          { index: 1, question: "What is a common architectural pattern used to prevent Agent loops from running infinitely?", options: ["Max Iterations Guardrail", "Temperature Scaling", "Cosine Similarity", "Gradient Clipping"], difficulty: "easy" },
          { index: 2, question: "Which memory type allows an agent to recall events from previous, distinct sessions?", options: ["Long-Term Memory (Vector DB)", "Short-Term Memory (Context Window)", "Working Memory", "Sensory Memory"], difficulty: "medium" }
        ]
      };
    }
    if (domain.includes("web")) {
      return {
        session_id: 202,
        questions: [
          { index: 0, question: "In React, what hook is used to manage side effects?", options: ["useEffect", "useState", "useContext", "useReducer"], difficulty: "medium" },
          { index: 1, question: "Which CSS property is used to change the background color?", options: ["background-color", "color", "bgcolor", "fill"], difficulty: "easy" }
        ]
      };
    }
    return {
      session_id: 123,
      questions: [
        { index: 0, question: "What does API stand for?", options: ["Application Programming Interface", "Advanced Protocol Integration", "Automated Process Interchange", "Application Process Interface"], difficulty: "easy" },
        { index: 1, question: "Which data structure uses LIFO (Last In First Out)?", options: ["Stack", "Queue", "Array", "Tree"], difficulty: "easy" }
      ]
    };
  }
  if (path === '/assess/submit-mcq') {
    const sessionId = data?.session_id;
    if (sessionId === 201) { 
      return {
        session_id: 201,
        student_name: "Demo User",
        scores: {
          total: 3,
          correct: 2,
          wrong: 1,
          percentile: 88,
          percentile_message: "You performed better than 88% of candidates."
        },
        level: "Advanced",
        strengths: ["Tool Calling", "Memory Management"],
        weaknesses: ["Evaluation Frameworks", "Infinite Loop Guardrails"]
      };
    }
    if (sessionId === 202) { 
      return {
        session_id: 202,
        student_name: "Demo User",
        scores: { total: 2, correct: 2, wrong: 0, percentile: 95, percentile_message: "You performed better than 95% of candidates." },
        level: "Expert",
        strengths: ["React Hooks", "CSS Fundamentals"],
        weaknesses: ["Advanced State Management"]
      };
    }
    return {
      session_id: 123,
      student_name: "Demo User",
      scores: { total: 2, correct: 1, wrong: 1, percentile: 50, percentile_message: "You performed exactly average." },
      level: "Intermediate",
      strengths: ["Basic terminology"],
      weaknesses: ["Data structures"]
    };
  }
  throw new Error(`Mock POST for ${path} not implemented`);
}
