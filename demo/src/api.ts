export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_KEY = import.meta.env.VITE_API_KEY || '';

export function getHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  };
}

// Simulate network delay
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
    ];
  }

  throw new Error(`Mock GET for ${path} not implemented`);
}

export async function apiPost(path: string, _data: any, _timeout = 900000): Promise<any> {
  await delay(1200);

  if (path === '/repo-judge/analyze') {
    return {
      score: 85,
      feedback: [
        { category: "Code Quality", score: 9, max_score: 10, comments: "Excellent code structure and naming conventions." },
        { category: "Architecture", score: 8, max_score: 10, comments: "Good separation of concerns, could improve modularity." },
        { category: "Documentation", score: 8, max_score: 10, comments: "README is thorough, but inline comments are sparse." },
      ],
      hackathons: [
        { name: "Global Hackathon 2026", date: "July 2026", description: "A great fit for your tech stack.", link: "#" },
        { name: "AI Innovators Challenge", date: "August 2026", description: "Perfect for AI-focused projects.", link: "#" }
      ]
    };
  }

  if (path === '/project-suggest/suggest') {
    return {
      suggestions: [
        {
          title: "Automated Code Review Assistant",
          overview: "An AI tool that reviews pull requests automatically.",
          features: ["Linting integration", "Security vulnerability scanning", "Style enforcement"],
          difficulty: "Intermediate",
          market_need: "High"
        },
        {
          title: "Decentralized Identity Provider",
          overview: "A blockchain-based SSO solution for web3 apps.",
          features: ["Zero-knowledge proofs", "Wallet integration", "Revocable access"],
          difficulty: "Advanced",
          market_need: "Medium"
        },
        {
          title: "Developer Portfolio Generator",
          overview: "Instantly generates a stunning portfolio from a GitHub profile.",
          features: ["Theme selection", "Automatic repo fetching", "SEO optimization"],
          difficulty: "Beginner",
          market_need: "High"
        }
      ]
    };
  }

  if (path === '/idea-validator/check') {
    return {
      gaps_and_loopholes: "The current market lacks tools that integrate seamlessly with legacy enterprise systems.",
      search_sources: [
        "GitHub Repositories",
        "Product Hunt",
        "Hacker News Discussions"
      ],
      similar_projects: [
        {
          name: "LegacyBridge",
          type: "Enterprise Tool",
          overview: "Connects old mainframes to modern APIs.",
          relevance_score: 85,
          comparison: "They focus on specific IBM systems, while your idea is more generic."
        },
        {
          name: "ApiWrap",
          type: "Open Source Library",
          overview: "Generates REST APIs from SQL databases.",
          relevance_score: 60,
          comparison: "Only handles databases, not arbitrary legacy protocols."
        }
      ]
    };
  }

  if (path === '/idea-validator/refine') {
    return {
      uniqueness: {
        verdict: "MODERATELY_UNIQUE",
        score: 75,
        rationale: "While similar tools exist, your specific approach to arbitrary protocol parsing is novel."
      },
      refined_concept: {
        final_direction: "Focus on a visual protocol builder that lets enterprises map their legacy systems without writing code.",
        quick_win_variant: {
          description: "Build a command-line tool first to prove the parsing engine works."
        }
      }
    };
  }

  if (path === '/assess/generate-mcq') {
    return {
      session_id: 123,
      questions: [
        {
          index: 0,
          question: "Which protocol is primarily used for secure web browsing?",
          options: ["HTTPS", "FTP", "SMTP", "Telnet"],
          difficulty: "easy"
        },
        {
          index: 1,
          question: "In React, what hook is used to manage side effects?",
          options: ["useEffect", "useState", "useContext", "useReducer"],
          difficulty: "medium"
        }
      ]
    };
  }

  if (path === '/assess/submit-mcq') {
    return {
      session_id: 123,
      student_name: "Demo User",
      scores: {
        total: 2,
        correct: 2,
        wrong: 0,
        percentile: 95,
        percentile_message: "You performed better than 95% of candidates."
      }
    };
  }

  throw new Error(`Mock POST for ${path} not implemented`);
}
