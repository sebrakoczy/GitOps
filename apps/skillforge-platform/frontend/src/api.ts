import type { Attempt, Category, Challenge, Dashboard, Question, Submission } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<Dashboard>("/dashboard"),
  categories: () => request<Category[]>("/categories"),
  questions: (category?: string, q?: string) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    return request<Question[]>(`/questions?${params.toString()}`);
  },
  challenges: (category?: string, q?: string) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    return request<Challenge[]>(`/challenges?${params.toString()}`);
  },
  submitAttempt: (question_id: number, answer: unknown) =>
    request<Attempt>("/attempts", { method: "POST", body: JSON.stringify({ question_id, answer }) }),
  submitChallenge: (challenge_id: number, solution: string) =>
    request<Submission>("/submissions", { method: "POST", body: JSON.stringify({ challenge_id, solution }) }),
};
