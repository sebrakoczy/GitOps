import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Activity, BookOpen, CheckCircle2, Code2, Flame, Layers, Search, ShieldCheck, TerminalSquare, XCircle } from "lucide-react";
import { api } from "./api";
import type { Attempt, Category, Challenge, Dashboard, Question, Submission } from "./types";

type Mode = "questions" | "challenges";

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
        api.questions(category || undefined, query || undefined),
        api.challenges(category || undefined, query || undefined),
      ]);
      setDashboard(d);
      setCategories(c);
      setQuestions(q);
      setChallenges(ch);
      if (!selectedQuestion && q.length > 0) setSelectedQuestion(q[0]);
      if (!selectedChallenge && ch.length > 0) {
        setSelectedChallenge(ch[0]);
        setSolution(starterText(ch[0]));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, query]);

  const activeItems = useMemo(() => (mode === "questions" ? questions : challenges), [mode, questions, challenges]);

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

  return (
    <main>
      <section className="hero">
        <div>
          <div className="eyebrow"><ShieldCheck size={18} /> Kubernetes-native interview training</div>
          <h1>SkillForge Platform</h1>
          <p>
            HackerRank-style prep for Senior Platform Engineer interviews: Kubernetes, Linux, Bash, Terraform,
            Ansible, GitOps, SRE, cloud networking, and system design.
          </p>
        </div>
        <div className="hero-card">
          <span>Readiness score</span>
          <strong>{dashboard?.readiness_score ?? 0}%</strong>
          <small>{dashboard?.attempts ?? 0} question attempts · {dashboard?.submissions ?? 0} lab submissions</small>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="metrics">
        <Metric icon={<BookOpen />} label="Questions" value={dashboard?.total_questions ?? 0} />
        <Metric icon={<Code2 />} label="Labs" value={dashboard?.total_challenges ?? 0} />
        <Metric icon={<Activity />} label="Average score" value={`${dashboard?.average_score ?? 0}%`} />
        <Metric icon={<Flame />} label="Domains" value={dashboard?.domain_breakdown.length ?? 0} />
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

          <label className="search">
            <Search size={16} />
            <input placeholder="Search topics..." value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>

          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All domains</option>
            {categories.map((cat) => (
              <option key={cat.slug} value={cat.slug}>{cat.name}</option>
            ))}
          </select>

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
        <h2>Domain coverage</h2>
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
        </div>
        <Layers />
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
        <textarea className="answer" value={String(answer)} onChange={(e) => setAnswer(e.target.value)} placeholder="Write your answer..." />
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
