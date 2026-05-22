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

function itemParams(category?: string, q?: string, difficulty?: string) {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (q) params.set("q", q);
  if (difficulty) params.set("difficulty", difficulty);
  params.set("limit", "1000");
  return params.toString();
}

export const api = {
  dashboard: () => request<Dashboard>("/dashboard"),
  categories: () => request<Category[]>("/categories"),
  questions: (category?: string, q?: string, difficulty?: string) =>
    request<Question[]>(`/questions?${itemParams(category, q, difficulty)}`),
  challenges: (category?: string, q?: string, difficulty?: string) =>
    request<Challenge[]>(`/challenges?${itemParams(category, q, difficulty)}`),
  submitAttempt: (question_id: number, answer: unknown) =>
    request<Attempt>("/attempts", { method: "POST", body: JSON.stringify({ question_id, answer }) }),
  submitChallenge: (challenge_id: number, solution: string) =>
    request<Submission>("/submissions", { method: "POST", body: JSON.stringify({ challenge_id, solution }) }),
};
