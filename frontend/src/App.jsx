import { useState } from "react";
import "./App.css";

function App() {
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

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
        "http://127.0.0.1:5000/api/analyze-and-schedule",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            task: task,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Something went wrong");
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>GreenRoute</h1>
          <p>Carbon- & Latency-Aware AI Workflow Scheduler</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Scheduler Online
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

        <section className="input-card">
          <label>AI WORKFLOW TASK</label>

          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Example: Analyze 5000 customer reviews and summarize the major complaints."
          />

          <button onClick={optimizeWorkflow} disabled={loading}>
            {loading ? "ANALYZING..." : "OPTIMIZE WORKFLOW →"}
          </button>

          {error && <p className="error">{error}</p>}
        </section>

        {result && result.schedule && result.schedule.selected ? (
           <>
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
                          {step.schedule.reason}
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

function FlowStep({ title, text }) {
  return (
    <div className="flow-step">
      <span>{title}</span>
      <strong>{text}</strong>
    </div>
  );
}

export default App;