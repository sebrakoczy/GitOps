import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Brain, Camera, CheckCircle2, CloudCog, Code2, FileText, ListChecks, Play, ShieldCheck, TerminalSquare, Timer, Trophy, Video } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || '/api';

async function api(path, options = {}) {
  const headers = options.body instanceof FormData ? (options.headers || {}) : { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const res = await fetch(`${API}${path}`, { headers, ...options });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function Pill({ children }) {
  return <span className="pill">{children}</span>;
}

function Score({ value }) {
  const v = Number(value || 0);
  return <div className="score"><strong>{v}</strong><span>/100</span></div>;
}

function SectionTitle({ icon, eyebrow, title, children }) {
  return (
    <div className="section-title">
      <div className="section-icon">{icon}</div>
      <div>
        <p>{eyebrow}</p>
        <h2>{title}</h2>
        {children && <span>{children}</span>}
      </div>
    </div>
  );
}

function Dashboard({ roles, selectedRole, setSelectedRole, health }) {
  return (
    <section className="card hero-card">
      <div>
        <p className="eyebrow">Homelab skills assessment platform</p>
        <h1>Practice like HackerRank, interview like micro1, deploy like a platform engineer.</h1>
        <p className="muted large">Run timed coding assessments, Kubernetes/Terraform/DevSecOps scenarios, video mock interviews, and AI-assisted feedback inside your own Kubernetes homelab.</p>
        <div className="hero-actions">
          <Pill>API: {health?.status || 'loading'}</Pill>
          <Pill>LLM: {health?.llm_enabled ? 'Ollama enabled' : 'rule-based fallback'}</Pill>
          <Pill>Judge: {health?.k8s_judge_enabled ? `K8s jobs in ${health.judge_namespace}` : 'disabled until enabled'}</Pill>
          <Pill>Longhorn-ready</Pill>
        </div>
      </div>
      <div className="role-picker">
        <h3>Choose a role track</h3>
        {roles.map(role => (
          <button key={role.slug} className={selectedRole === role.slug ? 'role active' : 'role'} onClick={() => setSelectedRole(role.slug)}>
            <strong>{role.title}</strong>
            <span>{role.description}</span>
            <small>{(role.focus_areas || []).slice(0, 3).join(' • ')}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function AssessmentCenter({ selectedRole, onSelectChallenge }) {
  const [assessments, setAssessments] = useState([]);

  useEffect(() => {
    api(`/assessments?role_slug=${selectedRole}`).then(setAssessments).catch(console.error);
  }, [selectedRole]);

  return (
    <section className="card assessment-card">
      <SectionTitle icon={<ListChecks />} eyebrow="HackerRank-style module" title="Timed Assessments">
        Choose a curated screen made of multiple coding challenges and interview follow-ups.
      </SectionTitle>
      <div className="assessment-grid">
        {assessments.map(a => (
          <article className="assessment" key={a.id}>
            <div className="assessment-top">
              <div>
                <h3>{a.title}</h3>
                <p>{a.description}</p>
              </div>
              <Pill><Timer size={13}/> {a.duration_minutes} min</Pill>
            </div>
            <div className="rubric">
              {(a.instructions || []).map(i => <Pill key={i}>{i}</Pill>)}
            </div>
            <div className="assessment-challenges">
              {(a.challenges || []).map(c => (
                <button key={c.id} onClick={() => onSelectChallenge(c)}>
                  <Code2 size={15}/>
                  <span>{c.title}</span>
                  <small>{c.difficulty}</small>
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function CodeArena({ selectedRole, forcedChallenge }) {
  const [challenges, setChallenges] = useState([]);
  const [active, setActive] = useState(null);
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [result, setResult] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api(`/code-challenges?role_slug=${selectedRole}`).then(rows => {
      setChallenges(rows);
      const first = forcedChallenge || rows[0] || null;
      setActive(first);
      const lang = first?.languages?.[0] || 'python';
      setLanguage(lang);
      setCode(first?.starter_code?.[lang] || '');
      setResult(null);
    }).catch(console.error);
  }, [selectedRole]);

  useEffect(() => {
    if (forcedChallenge) {
      setActive(forcedChallenge);
      const lang = forcedChallenge.languages?.[0] || 'python';
      setLanguage(lang);
      setCode(forcedChallenge.starter_code?.[lang] || '');
      setResult(null);
    }
  }, [forcedChallenge]);

  useEffect(() => {
    if (active?.id) api(`/leaderboard?code_challenge_id=${active.id}`).then(setLeaderboard).catch(console.error);
  }, [active?.id, result]);

  function selectChallenge(c) {
    setActive(c);
    const lang = c.languages?.[0] || 'python';
    setLanguage(lang);
    setCode(c.starter_code?.[lang] || '');
    setResult(null);
  }

  function selectLanguage(lang) {
    setLanguage(lang);
    setCode(active?.starter_code?.[lang] || '');
    setResult(null);
  }

  async function run() {
    if (!active || !code.trim()) return;
    setBusy(true);
    setResult(null);
    try {
      const data = await api('/code-submissions', {
        method: 'POST',
        body: JSON.stringify({ code_challenge_id: active.id, candidate_name: 'Sebastian', language, source_code: code, include_hidden: true }),
      });
      setResult(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid code-layout">
      <div className="card">
        <SectionTitle icon={<Code2 />} eyebrow="Coding challenge arena" title="HackerRank-style Problems">
          Solve function challenges with visible and hidden test cases.
        </SectionTitle>
        <div className="list">
          {challenges.map(c => (
            <button key={c.id} className={active?.id === c.id ? 'challenge active' : 'challenge'} onClick={() => selectChallenge(c)}>
              <div><strong>{c.title}</strong><span>{c.category}</span></div>
              <Pill>{c.difficulty}</Pill>
            </button>
          ))}
        </div>
        <div className="leaderboard">
          <h3><Trophy size={17}/> Leaderboard</h3>
          {leaderboard.length === 0 && <p className="muted">No scored submissions yet.</p>}
          {leaderboard.slice(0, 5).map((r, idx) => (
            <div className="leader-row" key={r.id}>
              <span>#{idx + 1}</span>
              <strong>{r.candidate_name}</strong>
              <small>{r.language}</small>
              <b>{r.score}</b>
            </div>
          ))}
        </div>
      </div>
      <div className="card workspace code-workspace">
        {active ? (
          <>
            <div className="workspace-header">
              <div>
                <p className="eyebrow">{active.category} • {active.difficulty} • {active.points} pts</p>
                <h3>{active.title}</h3>
              </div>
              {result && <Score value={result.score} />}
            </div>
            <p className="prompt">{active.prompt_md}</p>
            <div className="rubric">
              {(active.tags || []).map(k => <Pill key={k}>{k}</Pill>)}
            </div>
            <div className="test-strip">
              {(active.visible_tests || []).map(t => (
                <div className="test-card" key={t.name}>
                  <strong>{t.name}</strong>
                  <span>input: {JSON.stringify(t.input)}</span>
                  <span>expected: {JSON.stringify(t.expected)}</span>
                </div>
              ))}
            </div>
            <div className="editor-toolbar">
              <select value={language} onChange={e => selectLanguage(e.target.value)}>
                {(active.languages || []).map(l => <option key={l} value={l}>{l}</option>)}
              </select>
              <button className="primary" onClick={run} disabled={busy}><Play size={16}/> {busy ? 'Running...' : 'Run tests'}</button>
            </div>
            <textarea className="code-editor" value={code} onChange={e => setCode(e.target.value)} spellCheck="false" />
            {result && <CodeResult result={result} />}
          </>
        ) : <p>No coding challenges loaded.</p>}
      </div>
    </section>
  );
}

function CodeResult({ result }) {
  return (
    <div className="feedback code-result">
      <div className="result-head">
        <h4>Submission result: {result.status}</h4>
        <Pill>{result.judge_mode}</Pill>
        <Pill>{result.passed}/{result.total} tests</Pill>
      </div>
      <div className="result-grid">
        {(result.results || []).map((r, i) => (
          <div className={r.passed ? 'case pass' : 'case fail'} key={`${r.name}-${i}`}>
            <strong>{r.visible === false ? 'Hidden test' : r.name}</strong>
            <span>{r.passed ? 'passed' : 'failed'}</span>
            {r.visible !== false && <small>expected: {JSON.stringify(r.expected)} | actual: {JSON.stringify(r.actual)}</small>}
            {r.error && <small className="error">{r.error}</small>}
          </div>
        ))}
      </div>
    </div>
  );
}

function ChallengeArena({ selectedRole }) {
  const [challenges, setChallenges] = useState([]);
  const [active, setActive] = useState(null);
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api(`/challenges?role_slug=${selectedRole}`).then(rows => {
      setChallenges(rows);
      setActive(rows[0] || null);
      setAnswer('');
      setResult(null);
    }).catch(console.error);
  }, [selectedRole]);

  async function submit() {
    if (!active || !answer.trim()) return;
    setBusy(true);
    setResult(null);
    try {
      const data = await api('/submissions', {
        method: 'POST',
        body: JSON.stringify({ challenge_id: active.id, candidate_name: 'Sebastian', answer }),
      });
      setResult(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid two">
      <div className="card">
        <SectionTitle icon={<TerminalSquare />} eyebrow="Architecture and DevOps prompts" title="Scenario Lab">
          Practice explaining designs, incident response, Terraform, GitOps, and security decisions.
        </SectionTitle>
        <div className="list">
          {challenges.map(c => (
            <button key={c.id} className={active?.id === c.id ? 'challenge active' : 'challenge'} onClick={() => { setActive(c); setResult(null); }}>
              <div><strong>{c.title}</strong><span>{c.category}</span></div>
              <Pill>{c.difficulty}</Pill>
            </button>
          ))}
        </div>
      </div>
      <div className="card workspace">
        {active ? (
          <>
            <div className="workspace-header">
              <div>
                <p className="eyebrow">{active.category} • {active.difficulty}</p>
                <h3>{active.title}</h3>
              </div>
              {result && <Score value={result.score} />}
            </div>
            <p className="prompt">{active.prompt}</p>
            <div className="rubric">
              {(active.expected_keywords || []).slice(0, 10).map(k => <Pill key={k}>{k}</Pill>)}
            </div>
            <textarea value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Write your design, pseudo-code, Terraform plan, or incident response here..." />
            <button className="primary" onClick={submit} disabled={busy}>{busy ? 'Scoring...' : 'Submit for scoring'}</button>
            {result && <Feedback result={result.feedback} />}
          </>
        ) : <p>No scenario challenges loaded.</p>}
      </div>
    </section>
  );
}

function Feedback({ result }) {
  return (
    <div className="feedback">
      <h4>Feedback</h4>
      <p>{result?.summary || 'No feedback summary available.'}</p>
      {result?.hits?.length > 0 && <p><strong>Covered:</strong> {result.hits.join(', ')}</p>}
      {result?.missing?.length > 0 && <p><strong>Missing:</strong> {result.missing.join(', ')}</p>}
      {Array.isArray(result?.recommendations) && result.recommendations.length > 0 && (
        <ul>{result.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
      )}
    </div>
  );
}

function Recorder({ sessionId, questionIndex }) {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [recording, setRecording] = useState(false);
  const [message, setMessage] = useState('Camera is optional. Start recording when you want video practice.');

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    videoRef.current.srcObject = stream;
    chunksRef.current = [];
    const mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
    mediaRecorder.ondataavailable = e => chunksRef.current.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      const form = new FormData();
      form.append('file', blob, `answer-q${questionIndex}.webm`);
      const res = await fetch(`${API}/interviews/${sessionId}/recording?question_index=${questionIndex}`, { method: 'POST', body: form });
      if (res.ok) setMessage('Recording uploaded to the API pod volume.');
      stream.getTracks().forEach(t => t.stop());
    };
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setRecording(true);
    setMessage('Recording...');
  }

  function stop() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="recorder">
      <video ref={videoRef} autoPlay muted playsInline />
      <div className="recorder-actions">
        {!recording ? <button onClick={start}><Camera size={16}/> Start video</button> : <button onClick={stop}><Video size={16}/> Stop & upload</button>}
        <span>{message}</span>
      </div>
    </div>
  );
}

function MockInterview({ selectedRole }) {
  const [templates, setTemplates] = useState([]);
  const [template, setTemplate] = useState(null);
  const [session, setSession] = useState(null);
  const [qIndex, setQIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [answerFeedback, setAnswerFeedback] = useState(null);
  const [report, setReport] = useState(null);

  useEffect(() => {
    api(`/interview-templates?role_slug=${selectedRole}`).then(rows => {
      setTemplates(rows);
      setTemplate(rows[0] || null);
      setSession(null);
      setReport(null);
    }).catch(console.error);
  }, [selectedRole]);

  async function start() {
    const data = await api('/interviews/start', { method: 'POST', body: JSON.stringify({ template_id: template.id, candidate_name: 'Sebastian' }) });
    setSession(data);
    setQIndex(0);
    setAnswer('');
    setAnswerFeedback(null);
    setReport(null);
  }

  async function submitAnswer() {
    const question = session.questions[qIndex];
    const data = await api(`/interviews/${session.id}/answers`, {
      method: 'POST',
      body: JSON.stringify({ question_index: qIndex, question, answer_text: answer }),
    });
    setAnswerFeedback(data.feedback);
  }

  async function next() {
    setAnswer('');
    setAnswerFeedback(null);
    if (qIndex + 1 < session.questions.length) setQIndex(qIndex + 1);
    else {
      const data = await api(`/interviews/${session.id}/complete`, { method: 'POST', body: JSON.stringify({ finalize: true }) });
      setReport(data.report);
    }
  }

  return (
    <section className="card interview-card">
      <SectionTitle icon={<Brain />} eyebrow="AI and video practice" title="Mock Technical Interview">
        Timed question flow, video recording, transcript/text answer, and scoring report.
      </SectionTitle>
      {!session && (
        <div className="interview-start">
          <select value={template?.id || ''} onChange={e => setTemplate(templates.find(t => String(t.id) === e.target.value))}>
            {templates.map(t => <option key={t.id} value={t.id}>{t.name} — {t.duration_minutes} min</option>)}
          </select>
          <button className="primary" disabled={!template} onClick={start}>Start mock interview</button>
        </div>
      )}
      {session && !report && (
        <div className="interview-workspace">
          <div>
            <p className="eyebrow">Question {qIndex + 1} of {session.questions.length}</p>
            <h3>{session.questions[qIndex]}</h3>
            <Recorder sessionId={session.id} questionIndex={qIndex} />
          </div>
          <div>
            <textarea value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Paste a transcript or type your spoken answer. Structure it: context → decision → trade-offs → outcome." />
            <div className="button-row">
              <button className="primary" onClick={submitAnswer}>Score this answer</button>
              <button onClick={next}>{qIndex + 1 < session.questions.length ? 'Next question' : 'Complete interview'}</button>
            </div>
            {answerFeedback && <Feedback result={answerFeedback} />}
          </div>
        </div>
      )}
      {report && (
        <div className="report">
          <CheckCircle2 size={36}/>
          <h3>Interview complete</h3>
          <Score value={report.overall_score}/>
          <p>{report.summary}</p>
          <ul>{report.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
          <button onClick={() => { setSession(null); setReport(null); }}>Run another interview</button>
        </div>
      )}
    </section>
  );
}

function Roadmap() {
  const cards = [
    { icon: <TerminalSquare/>, title: 'K8s code judge', text: 'Runs code in short-lived Kubernetes Jobs with no service account token, non-root execution, resource limits, RuntimeDefault seccomp, and cleanup TTL.' },
    { icon: <ShieldCheck/>, title: 'DevSecOps controls', text: 'Add image signing, SBOM scans, Trivy/Grype, Kyverno policies, network deny, and GitOps promotion gates.' },
    { icon: <CloudCog/>, title: 'Homelab operations', text: 'Longhorn PVCs, Prometheus metrics, Loki logs, Argo CD app-of-apps, backups, and restore runbooks.' },
    { icon: <FileText/>, title: 'Question bank', text: 'Import YAML challenge packs and generate adaptive interview tracks using Ollama or OpenAI-compatible APIs.' },
  ];
  return <section className="grid four">{cards.map(c => <div className="card mini" key={c.title}>{c.icon}<h3>{c.title}</h3><p>{c.text}</p></div>)}</section>;
}

function App() {
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('senior-platform-engineer');
  const [health, setHealth] = useState(null);
  const [forcedChallenge, setForcedChallenge] = useState(null);

  useEffect(() => {
    api('/health').then(setHealth).catch(console.error);
    api('/roles').then(rows => {
      setRoles(rows);
      if (rows[0]) setSelectedRole(rows[0].slug);
    }).catch(console.error);
  }, []);

  const roleTitle = useMemo(() => roles.find(r => r.slug === selectedRole)?.title || 'Platform Engineer', [roles, selectedRole]);

  return (
    <main>
      <nav>
        <div className="brand"><span>SF</span><strong>SkillForge</strong></div>
        <div><Pill>{roleTitle}</Pill></div>
      </nav>
      <Dashboard roles={roles} selectedRole={selectedRole} setSelectedRole={slug => { setSelectedRole(slug); setForcedChallenge(null); }} health={health} />
      <AssessmentCenter selectedRole={selectedRole} onSelectChallenge={setForcedChallenge} />
      <CodeArena selectedRole={selectedRole} forcedChallenge={forcedChallenge} />
      <ChallengeArena selectedRole={selectedRole} />
      <MockInterview selectedRole={selectedRole} />
      <Roadmap />
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
