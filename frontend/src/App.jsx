import { useEffect, useState } from "react";
import "./App.css";

const API_BASE = `http://${window.location.hostname}:5000`;

function App() {
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [authStep, setAuthStep] = useState("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [authError, setAuthError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [optimizationMode, setOptimizationMode] = useState("balanced");
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [offlineMode, setOfflineMode] = useState(false);
  const [error, setError] = useState("");
  const [isEditingTask, setIsEditingTask] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`, { credentials: "include" })
      .then((response) => response.json())
      .then((data) => {
        if (data.authenticated) {
          setAuthUser(data);
        }
      })
      .finally(() => setAuthLoading(false));
  }, []);

  const submitAuth = async (event) => {
    event.preventDefault();
    setAuthError("");

    try {
      const response = await fetch(`${API_BASE}/api/auth/${authMode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Authentication failed");
      if (authMode === "register") {
        setAuthMode("login");
        setAuthMessage(data.message);
      } else {
        setAuthStep("otp");
        setAuthMessage(`A verification code was sent to ${data.email}.`);
      }
      setPassword("");
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const verifyOtp = async (event) => {
    event.preventDefault();
    setAuthError("");

    try {
      const response = await fetch(`${API_BASE}/api/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ otp }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Verification failed");
      setAuthUser(data);
      setOtp("");
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const resendOtp = async () => {
    setAuthError("");
    const response = await fetch(`${API_BASE}/api/auth/resend-otp`, {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
      setAuthError(data.message || "Unable to resend code");
      return;
    }
    setAuthMessage("A new verification code was sent.");
  };

  const logout = async () => {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    setAuthUser(null);
    setResult(null);
  };

  const optimizeWorkflow = async () => {
    if (!task.trim()) {
      setError("Enter an AI task first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/analyze-and-schedule`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            task: task,
            optimization_mode: optimizationMode,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Something went wrong");
      }

      setResult(data);
      setOfflineMode(data.offline);
      setIsEditingTask(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return <div className="auth-shell">Loading GreenRoute...</div>;
  }

  if (!authUser) {
    return (
      <div className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">GREENROUTE</p>
          <h1>
            {authStep === "otp"
              ? "Check your email"
              : authMode === "login"
                ? "Welcome back"
                : "Create your account"}
          </h1>
          <p className="auth-description">
            {authStep === "otp"
              ? "Enter the 6-digit code to finish signing in."
              : "Sign in to optimize AI workflows with a lower resource footprint."}
          </p>
          {authStep === "otp" ? (
            <form onSubmit={verifyOtp}>
              <label htmlFor="otp">VERIFICATION CODE</label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))}
                required
                autoComplete="one-time-code"
              />
              <button type="submit">VERIFY CODE</button>
              <button type="button" className="auth-switch" onClick={resendOtp}>
                RESEND CODE
              </button>
            </form>
          ) : (
            <form onSubmit={submitAuth}>
              <label htmlFor="email">EMAIL</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />
              <label htmlFor="password">PASSWORD</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={8}
                autoComplete={authMode === "login" ? "current-password" : "new-password"}
              />
              <button type="submit">
                {authMode === "login" ? "CONTINUE TO EMAIL VERIFICATION" : "CREATE ACCOUNT"}
              </button>
            </form>
          )}
          {authMessage && <p className="auth-message">{authMessage}</p>}
          {authError && <p className="error">{authError}</p>}
          {authStep === "credentials" && (
            <button
              className="auth-switch"
              onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setAuthError("");
                setAuthMessage("");
              }}
            >
              {authMode === "login"
                ? "Need an account? Register"
                : "Already have an account? Sign in"}
            </button>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>GreenRoute</h1>
          <p>Carbon- & Latency-Aware AI Workflow Scheduler</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          <span>{authUser.email}</span>
          <button className="logout-button" onClick={logout}>SIGN OUT</button>
        </div>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">AI RESOURCE OPTIMIZATION</p>
            <h2>Run every AI task<br />where it makes the most sense.</h2>

            <p className="description">
              GreenRoute analyzes your workflow and selects an execution
              configuration by balancing latency, accuracy, cost, energy,
              and carbon emissions.
            </p>
          </div>
        </section>

        {isEditingTask || !result ? (
          <section className="input-card">
            <label>AI WORKFLOW TASK</label>

            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Example: Analyze 5000 customer reviews and summarize the major complaints."
            />
            <label>OPTIMIZATION MODE</label>

              <select
                value={optimizationMode}
                onChange={(e) => setOptimizationMode(e.target.value)}
              >
                <option value="balanced">Balanced</option>
                <option value="carbon">Carbon First</option>
                <option value="latency">Latency First</option>
                <option value="cost">Cost First</option>
                <option value="energy">Energy First</option>
              </select>
          
            <button onClick={optimizeWorkflow} disabled={loading}>
              {loading ? "ANALYZING..." : "OPTIMIZE WORKFLOW →"}
            </button>

            {error && <p className="error">{error}</p>}
          </section>
        ) : (
          <section className="input-card collapsed-input-card">
            <div className="collapsed-task">
              <div>
                <label>AI WORKFLOW TASK</label>
                <p>{task}</p>
                <span className="selected-mode">
                MODE · {optimizationMode.replace("-", " ").toUpperCase()}
              </span>
              </div>

              <button
                className="edit-task-button"
                onClick={() => setIsEditingTask(true)}
              >
                EDIT TASK
              </button>
            </div>
          </section>
        )}

        {result && result.schedule && result.schedule.selected ? (
           <>
           

          <div className={`connection-status ${offlineMode ? "offline" : "online"}`}>
            <span className="status-dot"></span>
            {offlineMode
              ? "OFFLINE FALLBACK · LOCAL ANALYZER"
              : "ONLINE · GEMINI ANALYZER"}
          </div>
            <section className="requirements">
              <h3>Task Analysis</h3>

              <div className="requirement-grid">
                <div>
                  <span>Task Type</span>
                  <strong>{result.requirements.task_type}</strong>
                </div>

                <div>
                  <span>Complexity</span>
                  <strong>{result.requirements.complexity}</strong>
                </div>

                <div>
                  <span>Required Accuracy</span>
                  <strong>{result.requirements.recommended_accuracy}%</strong>
                </div>

                <div>
                  <span>Urgency</span>
                  <strong>{result.requirements.urgency}</strong>
                </div>

                <div>
                  <span>Can Be Delayed</span>
                  <strong>
                    {result.requirements.can_be_delayed ? "Yes" : "No"}
                  </strong>
                </div>
              </div>
            </section>

            <section className="recommendation">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">RECOMMENDED EXECUTION</p>
                  <h3>Optimal Configuration</h3>
                </div>

                <span className="selected-badge">SELECTED</span>
              </div>

              <div className="selected-main">
                <div className="model-info">
                  <h2>{result.schedule.selected.model}</h2>
                  <p>
                    {result.schedule.selected.location} ·{" "}
                    {result.schedule.selected.timing}
                  </p>
                </div>

                <div className="reason">
                  {result.schedule.reason}
                </div>
              </div>

              <div className="metrics">
                <Metric
                  label="Accuracy"
                  value={`${result.schedule.selected.accuracy}%`}
                />

                <Metric
                  label="Latency"
                  value={`${result.schedule.selected.latency}s`}
                />

                <Metric
                  label="Cost"
                  value={`$${result.schedule.selected.cost}`}
                />

                <Metric
                  label="Energy"
                  value={`${result.schedule.selected.energy} units`}
                />

                <Metric
                  label="Carbon"
                  value={`${result.schedule.selected.carbon} gCO₂`}
                />
              </div>
            </section>
            <section className="impact-card">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">RESOURCE IMPACT</p>
                      <h3>GreenRoute Impact</h3>
                    </div>
                  </div>

                  {result.impact && (
                    <>
                      <div className="impact-grid">
                        <div>
                          <span>CARBON REDUCTION</span>
                          <strong>{result.impact.carbon_reduction}%</strong>
                        </div>

                        <div>
                          <span>COST REDUCTION</span>
                          <strong>{result.impact.cost_reduction}%</strong>
                        </div>

                        <div>
                          <span>ENERGY REDUCTION</span>
                          <strong>{result.impact.energy_reduction}%</strong>
                        </div>
                      </div>

                      <p className="impact-note">
                        Compared with the highest-resource feasible configuration.
                        Values are simulated estimates.
                      </p>
                    </>
                  )}
                </section>  
            <section className="alternatives">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">DECISION SPACE</p>
                  <h3>Available Alternatives</h3>
                </div>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Location</th>
                      <th>Timing</th>
                      <th>Accuracy</th>
                      <th>Latency</th>
                      <th>Cost</th>
                      <th>Energy</th>
                      <th>Carbon</th>
                    </tr>
                  </thead>

                  <tbody>
                    {result.schedule.alternatives.map((option) => (
                      <tr
                        key={option.id}
                        className={
                          option.id === result.schedule.selected.id
                            ? "selected-row"
                            : ""
                        }
                      >
                        <td>{option.model}</td>
                        <td>{option.location}</td>
                        <td>{option.timing}</td>
                        <td>{option.accuracy}%</td>
                        <td>{option.latency}s</td>
                        <td>${option.cost}</td>
                        <td>{option.energy}</td>
                        <td>{option.carbon} g</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
             <p className="data-note">
                Resource metrics are simulated estimates for prototype demonstration.
            </p>       
            <section className="workflow">
          <p className="eyebrow">STEP-LEVEL SCHEDULING</p>

          <h3>GreenRoute routes each workflow step independently</h3>

          <p className="workflow-description">
            Different steps have different resource requirements. GreenRoute
            selects the execution configuration for each step instead of using
            one configuration for the entire workflow.
          </p>

          <div className="workflow-pipeline">
            {result.workflow.map((step, index) => {
              const selected = step.schedule.selected;

              return (
                <div className="workflow-item" key={step.name}>
                  <div className="step-number">
                    0{index + 1}
                  </div>

                  <div className="workflow-card">
                    <div className="workflow-card-header">
                      <div>
                        <span className="step-label">{step.name}</span>
                        <p>{step.description}</p>
                        <div className="step-reason">
                          {step.reason}
                          </div>
                      </div>

                      <span className="selected-badge">
                        OPTIMIZED
                      </span>
                    </div>

                    <div className="workflow-route">
                      <div>
                        <span>MODEL</span>
                        <strong>{selected.model}</strong>
                      </div>

                      <div>
                        <span>LOCATION</span>
                        <strong>{selected.location}</strong>
                      </div>

                      <div>
                        <span>TIMING</span>
                        <strong>{selected.timing}</strong>
                      </div>

                      <div>
                        <span>LATENCY</span>
                        <strong>{selected.latency}s</strong>
                      </div>

                      <div>
                        <span>CARBON</span>
                        <strong>{selected.carbon} g</strong>
                      </div>
                    </div>
                  </div>

                  {index < result.workflow.length - 1 && (
                    <div className="workflow-connector">
                      ↓
                    </div>
                  )}
                </div>
              );
            })}
          </div>

  <p className="data-note">
    Resource metrics are simulated estimates for prototype demonstration.
  </p>
</section>
          </>
        ) : result ? (
         <section className="input-card">
         <p className="error">
            Scheduler could not find a valid configuration.
         </p>
         </section>
          ) : null  }
      </main>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;