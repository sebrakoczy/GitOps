import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Code2,
  Filter,
  Layers,
  ListChecks,
  Search,
  ShieldCheck,
  Target,
  TerminalSquare,
  Trophy,
  XCircle,
} from "lucide-react";
import { api } from "./api";
import type { Attempt, Category, Challenge, Dashboard, Question, Submission } from "./types";

type Mode = "questions" | "challenges";

const DIFFICULTIES = ["", "Beginner", "Intermediate", "Advanced"];

function badgeClass(difficulty: string) {
  return `badge ${difficulty.toLowerCase()}`;
}

function starterText(challenge: Challenge) {
  if (!challenge.starter_files) return "";
  return Object.entries(challenge.starter_files)
    .map(([name, body]) => `# ${name}\n${body}`)
    .join("\n\n");
}

export function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [mode, setMode] = useState<Mode>("questions");
  const [category, setCategory] = useState<string>("");
  const [difficulty, setDifficulty] = useState<string>("");
  const [query, setQuery] = useState("");
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState<string | string[]>("");
  const [solution, setSolution] = useState("");
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [d, c, q, ch] = await Promise.all([
        api.dashboard(),
        api.categories(),
        api.questions(category || undefined, query || undefined, difficulty || undefined),
        api.challenges(category || undefined, query || undefined, difficulty || undefined),
      ]);
      setDashboard(d);
      setCategories(c);
      setQuestions(q);
      setChallenges(ch);
      setSelectedQuestion(q[0] ?? null);
      setSelectedChallenge(ch[0] ?? null);
      setAnswer(q[0]?.type === "multi_select" ? [] : "");
      setSolution(ch[0] ? starterText(ch[0]) : "");
      setAttempt(null);
      setSubmission(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, difficulty, query]);

  const activeItems = useMemo(() => (mode === "questions" ? questions : challenges), [mode, questions, challenges]);
  const selectedCategoryName = categories.find((item) => item.slug === category)?.name ?? "All domains";

  async function submitAnswer() {
    if (!selectedQuestion) return;
    const payload = selectedQuestion.type === "multi_select" ? answer : String(answer);
    const result = await api.submitAttempt(selectedQuestion.id, payload);
    setAttempt(result);
    setDashboard(await api.dashboard());
  }

  async function submitSolution() {
    if (!selectedChallenge) return;
    const result = await api.submitChallenge(selectedChallenge.id, solution);
    setSubmission(result);
    setDashboard(await api.dashboard());
  }

  function selectQuestion(question: Question) {
    setSelectedQuestion(question);
    setSelectedChallenge(null);
    setAnswer(question.type === "multi_select" ? [] : "");
    setAttempt(null);
  }

  function selectChallenge(challenge: Challenge) {
    setSelectedChallenge(challenge);
    setSelectedQuestion(null);
    setSolution(starterText(challenge));
    setSubmission(null);
  }

  function resetFilters() {
    setCategory("");
    setDifficulty("");
    setQuery("");
  }

  return (
    <main>
      <nav className="topbar">
        <div className="brand">
          <div className="brand-mark"><TerminalSquare size={22} /></div>
          <div>
            <strong>SkillForge</strong>
            <span>Platform Engineering Interview OS</span>
          </div>
        </div>
        <div className="top-actions">
          <span className="pill"><ShieldCheck size={15} /> Kubernetes-native</span>
          <span className="pill"><Trophy size={15} /> Senior-track</span>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><Target size={18} /> Comprehensive platform engineering preparation</div>
          <h1>Practice like the interview is production.</h1>
          <p>
            A clean HackerRank-style workspace for Kubernetes, Linux, Bash, Terraform, Ansible, GitOps,
            DevSecOps, SRE, cloud networking, systems design, troubleshooting, and leadership scenarios.
          </p>
        </div>
        <div className="readiness-card">
          <span>Readiness score</span>
          <strong>{dashboard?.readiness_score ?? 0}%</strong>
          <div className="scorebar"><i style={{ width: `${Math.min(dashboard?.readiness_score ?? 0, 100)}%` }} /></div>
          <small>{dashboard?.attempts ?? 0} question attempts · {dashboard?.submissions ?? 0} lab submissions</small>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="metrics">
        <Metric icon={<BookOpen />} label="Interview questions" value={dashboard?.total_questions ?? 0} />
        <Metric icon={<Code2 />} label="Scenario labs" value={dashboard?.total_challenges ?? 0} />
        <Metric icon={<Activity />} label="Average score" value={`${dashboard?.average_score ?? 0}%`} />
        <Metric icon={<Layers />} label="Domains" value={dashboard?.domain_breakdown.length ?? 0} />
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="tabs">
            <button className={mode === "questions" ? "active" : ""} onClick={() => setMode("questions")}>
              <BookOpen size={16} /> Questions
            </button>
            <button className={mode === "challenges" ? "active" : ""} onClick={() => setMode("challenges")}>
              <TerminalSquare size={16} /> Labs
            </button>
          </div>

          <div className="filter-title"><Filter size={15} /> Filters</div>
          <label className="search">
            <Search size={16} />
            <input placeholder="Search Kubernetes, Terraform, SRE..." value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>

          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All domains</option>
            {categories.map((cat) => (
              <option key={cat.slug} value={cat.slug}>{cat.name}</option>
            ))}
          </select>

          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {DIFFICULTIES.map((item) => <option key={item || "all"} value={item}>{item || "All difficulties"}</option>)}
          </select>

          <button className="ghost" onClick={resetFilters}>Reset filters</button>

          <div className="list-summary">
            <strong>{activeItems.length}</strong>
            <span>{mode === "questions" ? "questions" : "labs"} · {selectedCategoryName}</span>
          </div>

          <div className="item-list">
            {mode === "questions" && questions.map((q) => (
              <button key={q.id} className={selectedQuestion?.id === q.id ? "item active" : "item"} onClick={() => selectQuestion(q)}>
                <span>{q.title}</span>
                <small>{q.category?.name} · {q.difficulty}</small>
              </button>
            ))}
            {mode === "challenges" && challenges.map((ch) => (
              <button key={ch.id} className={selectedChallenge?.id === ch.id ? "item active" : "item"} onClick={() => selectChallenge(ch)}>
                <span>{ch.title}</span>
                <small>{ch.category?.name} · {ch.difficulty}</small>
              </button>
            ))}
          </div>
        </aside>

        <section className="panel">
          {mode === "questions" && selectedQuestion && (
            <QuestionPanel
              question={selectedQuestion}
              answer={answer}
              setAnswer={setAnswer}
              submit={submitAnswer}
              attempt={attempt}
            />
          )}

          {mode === "challenges" && selectedChallenge && (
            <ChallengePanel
              challenge={selectedChallenge}
              solution={solution}
              setSolution={setSolution}
              submit={submitSolution}
              submission={submission}
            />
          )}

          {!activeItems.length && <div className="empty">No items match this filter yet.</div>}
        </section>
      </section>

      <section className="domain-grid">
        <div className="section-heading">
          <div>
            <h2>Domain coverage</h2>
            <p>Designed around senior platform engineering interviews, not generic trivia.</p>
          </div>
          <BarChart3 />
        </div>
        <div className="cards">
          {dashboard?.domain_breakdown.map((domain) => (
            <div className="domain" key={domain.slug}>
              <div>
                <strong>{domain.name}</strong>
                <span>{domain.questions} questions · {domain.challenges} labs</span>
              </div>
              <b>{domain.score}%</b>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return <div className="metric"><span>{icon}</span><small>{label}</small><strong>{value}</strong></div>;
}

function QuestionPanel({ question, answer, setAnswer, submit, attempt }: {
  question: Question;
  answer: string | string[];
  setAnswer: (value: string | string[]) => void;
  submit: () => void;
  attempt: Attempt | null;
}) {
  const isMulti = question.type === "multi_select";
  return (
    <div>
      <div className="panel-head">
        <div>
          <span className={badgeClass(question.difficulty)}>{question.difficulty}</span>
          <h2>{question.title}</h2>
          <p>{question.prompt}</p>
          {question.tags?.length ? <div className="tags">{question.tags.slice(0, 5).map((tag) => <span key={tag}>{tag}</span>)}</div> : null}
        </div>
        <ListChecks />
      </div>

      {question.choices?.length ? (
        <div className="choices">
          {question.choices.map((choice) => {
            const selected = isMulti ? (answer as string[]).includes(choice) : answer === choice;
            return (
              <label key={choice} className={selected ? "choice selected" : "choice"}>
                <input
                  type={isMulti ? "checkbox" : "radio"}
                  checked={selected}
                  onChange={() => {
                    if (isMulti) {
                      const current = new Set(answer as string[]);
                      selected ? current.delete(choice) : current.add(choice);
                      setAnswer(Array.from(current));
                    } else {
                      setAnswer(choice);
                    }
                  }}
                />
                {choice}
              </label>
            );
          })}
        </div>
      ) : (
        <textarea className="answer" value={String(answer)} onChange={(e) => setAnswer(e.target.value)} placeholder="Write a structured interview answer. Mention commands, tradeoffs, failure modes, rollback, and validation where relevant." />
      )}

      <button className="primary" onClick={submit}>Submit answer</button>
      {attempt && <Result passed={attempt.passed} score={attempt.score} feedback={attempt.feedback} />}
    </div>
  );
}

function ChallengePanel({ challenge, solution, setSolution, submit, submission }: {
  challenge: Challenge;
  solution: string;
  setSolution: (value: string) => void;
  submit: () => void;
  submission: Submission | null;
}) {
  return (
    <div>
      <div className="panel-head">
        <div>
          <span className={badgeClass(challenge.difficulty)}>{challenge.difficulty}</span>
          <h2>{challenge.title}</h2>
          <p>{challenge.prompt}</p>
          {challenge.tags?.length ? <div className="tags">{challenge.tags.slice(0, 5).map((tag) => <span key={tag}>{tag}</span>)}</div> : null}
        </div>
        <Code2 />
      </div>
      <textarea className="code" value={solution} onChange={(e) => setSolution(e.target.value)} spellCheck={false} />
      <button className="primary" onClick={submit}>Run static checks</button>
      {submission && (
        <div className={submission.passed ? "result passed" : "result failed"}>
          <div className="result-head">
            {submission.passed ? <CheckCircle2 /> : <XCircle />}
            <strong>{submission.score}% · {submission.passed ? "Passed" : "Needs work"}</strong>
          </div>
          {submission.result?.checks.map((check) => (
            <div className="check" key={check.name}>
              {check.passed ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
              <span>{check.name}</span>
              <small>{check.details}</small>
            </div>
          ))}
          <p>{submission.result?.note}</p>
        </div>
      )}
    </div>
  );
}

function Result({ passed, score, feedback }: { passed: boolean; score: number; feedback: string }) {
  return (
    <div className={passed ? "result passed" : "result failed"}>
      <div className="result-head">
        {passed ? <CheckCircle2 /> : <XCircle />}
        <strong>{score}% · {passed ? "Correct" : "Review"}</strong>
      </div>
      <p>{feedback}</p>
    </div>
  );
}
