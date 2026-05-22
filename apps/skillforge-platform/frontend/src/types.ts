export type Category = {
  id: number;
  slug: string;
  name: string;
  description: string;
};

export type Question = {
  id: number;
  slug: string;
  title: string;
  category_id: number;
  difficulty: string;
  type: string;
  prompt: string;
  choices?: string[] | null;
  explanation?: string | null;
  tags?: string[] | null;
  category?: Category | null;
};

export type Challenge = {
  id: number;
  slug: string;
  title: string;
  category_id: number;
  difficulty: string;
  type: string;
  prompt: string;
  starter_files?: Record<string, string> | null;
  test_rules?: Record<string, unknown>[] | null;
  explanation?: string | null;
  tags?: string[] | null;
  category?: Category | null;
};

export type Attempt = {
  id: number;
  question_id: number;
  answer: unknown;
  score: number;
  passed: boolean;
  feedback: string;
};

export type Submission = {
  id: number;
  challenge_id: number;
  score: number;
  passed: boolean;
  result?: {
    score: number;
    passed: boolean;
    checks: { name: string; passed: boolean; details: string }[];
    mode: string;
    note: string;
  };
};

export type Dashboard = {
  total_questions: number;
  total_challenges: number;
  attempts: number;
  submissions: number;
  average_score: number;
  readiness_score: number;
  domain_breakdown: { slug: string; name: string; questions: number; challenges: number; score: number }[];
};
