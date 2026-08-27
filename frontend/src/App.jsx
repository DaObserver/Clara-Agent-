import { useEffect, useRef, useState } from "react";
import "./App.css";

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState("");
  const [resultTitle, setResultTitle] = useState("Clara's Review");
  const [sessionId, setSessionId] = useState("");
  const [latestReview, setLatestReview] = useState(
    () => localStorage.getItem("claraLatestReview") || ""
  );
  const [taskToComplete, setTaskToComplete] = useState("");
  const [activeSection, setActiveSection] = useState("");

  const fileInputRef = useRef(null);
  const API_BASE = "/api";

  useEffect(() => {
    if (latestReview) {
      localStorage.setItem("claraLatestReview", latestReview);
    }
  }, [latestReview]);

  const cleanClaraText = (text = "") =>
    text
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/__(.*?)__/g, "$1")
      .replace(/^[-*]\s+/gm, "• ")
      .replace(/`([^`]+)`/g, "$1");

  const scrollToResults = () => {
    setTimeout(() => {
      document.getElementById("clara-results")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  const readApiError = async (response) => {
    try {
      const data = await response.json();
      return data.detail || data.message || JSON.stringify(data);
    } catch {
      return await response.text();
    }
  };

  const fileToBase64 = (file) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(",")[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const runQuery = async (message) => {
    const response = await fetch(`${API_BASE}/clara/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(await readApiError(response));
    }

    return await response.json();
  };

  const handleFileSelect = (event) => {
    const incomingFiles = Array.from(event.target.files || []);

    if (incomingFiles.length) {
      setSelectedFiles((currentFiles) => {
        const combined = [...currentFiles, ...incomingFiles];

        return combined.filter(
          (file, index, allFiles) =>
            index ===
            allFiles.findIndex(
              (candidate) =>
                candidate.name === file.name &&
                candidate.size === file.size &&
                candidate.lastModified === file.lastModified
            )
        );
      });

      setResult("");
      setSessionId("");
      setActiveSection("");

      // Allows the same file to be chosen again later if it was removed.
      event.target.value = "";
    }
  };

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((currentFiles) =>
      currentFiles.filter((_, index) => index !== indexToRemove)
    );
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) {
      fileInputRef.current?.click();
      return;
    }

    if (selectedFiles.length > 10) {
      setResultTitle("Upload Documents");
      setResult("Please select 10 or fewer documents at a time.");
      return;
    }

    setIsProcessing(true);
    setResultTitle("Clara's Review");
    setActiveSection("visit");
    setResult("");

    try {
      const documents = await Promise.all(
        selectedFiles.map(async (file) => ({
          file_name: file.name,
          mime_type: file.type || "application/octet-stream",
          file_base64: await fileToBase64(file),
        }))
      );

      const response = await fetch(`${API_BASE}/clara/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          documents,
          prompt:
            "Review all uploaded medical documents together. Explain them in plain English and create one combined My Plan using only actions explicitly documented in the paperwork.",
        }),
      });

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const data = await response.json();
      const review =
        data.response || "Clara reviewed your medical documents successfully.";

      setSessionId(data.session_id || "");
      setResult(review);
      setLatestReview(review);
      scrollToResults();
    } catch (error) {
      setResult(`Clara could not review these documents. ${error.message}`);
      scrollToResults();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSavePlan = async () => {
    if (!sessionId) {
      setResultTitle("My Plan");
      setResult("Review your medical documents first, then Clara can save My Plan.");
      return;
    }

    setIsProcessing(true);
    setResultTitle("My Plan");
    setActiveSection("plan");

    try {
      const response = await fetch(`${API_BASE}/clara/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message:
            "Save the combined My Plan to the persistent care plan. Only save actions documented in the uploaded medical paperwork. Avoid duplicate tasks across documents.",
        }),
      });

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const data = await response.json();
      setResult(data.response || "My Plan was saved successfully.");
      scrollToResults();
    } catch (error) {
      setResult(`Clara could not save My Plan. ${error.message}`);
      scrollToResults();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDashboardAction = async (section, title, message) => {
    setIsProcessing(true);
    setActiveSection(section);
    setResultTitle(title);
    setResult("");

    try {
      const data = await runQuery(message);
      setResult(
        data.response || `No saved information is available for ${title} yet.`
      );
      scrollToResults();
    } catch (error) {
      setResult(`Clara could not load ${title}. ${error.message}`);
      scrollToResults();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVisitSummary = () => {
    setActiveSection("visit");
    setResultTitle("Visit Summary");
    setResult(
      latestReview ||
        "No visit summary is available yet. Upload and review medical documents first."
    );
    scrollToResults();
  };

  const handleMyPlan = () =>
    handleDashboardAction(
      "plan",
      "My Plan",
      "Retrieve my saved care plan from Firestore and show My Plan. If there is no saved care plan, clearly say that no plan has been saved yet. Show only documented medications, tests, follow-ups, instructions, restrictions, and task statuses. Do not invent information."
    );

  const handleMedications = () =>
    handleDashboardAction(
      "medications",
      "Medications",
      "Retrieve my saved care plan from Firestore and show only documented medication information. If there are no saved medications, clearly say so. Include medication name, dose, frequency, and timing only when documented. Do not guess or prescribe."
    );

  const handlePendingTasks = () =>
    handleDashboardAction(
      "tasks",
      "Pending Tasks",
      "Retrieve my saved care plan from Firestore and show only tasks whose current status is pending. If there is no saved care plan, clearly say so. If no pending tasks remain, say all saved tasks are complete. Do not show completed tasks."
    );

  const handleCompleteTask = async () => {
    const task = taskToComplete.trim();

    if (!task) {
      setActiveSection("tasks");
      setResultTitle("Pending Tasks");
      setResult("Enter the task you completed, then press Mark Complete.");
      return;
    }

    setIsProcessing(true);
    setActiveSection("tasks");
    setResultTitle("Pending Tasks");
    setResult("");

    try {
      const completion = await runQuery(
        `Update my saved care plan in Firestore. Mark the existing task matching "${task}" as completed using the care-plan task update tool. Do not create a new task. Confirm completion only after the saved status actually updates. If no task matches, say so clearly.`
      );

      const refreshed = await runQuery(
        "Retrieve my saved care plan from Firestore and show only tasks whose current status is pending. Do not show completed tasks. If none remain, say all saved tasks are complete."
      );

      setResult(
        `${completion.response || "Task update processed."}\n\nUpdated Pending Tasks\n${refreshed.response || "No pending tasks returned."}`
      );

      setTaskToComplete("");
      scrollToResults();
    } catch (error) {
      setResult(`Clara could not update that task. ${error.message}`);
      scrollToResults();
    } finally {
      setIsProcessing(false);
    }
  };

  const selectedLabel =
    selectedFiles.length === 0
      ? "Choose Documents"
      : "Add More Documents";

  return (
    <div className="app">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,image/*"
        multiple
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />

      <header className="topbar">
        <div className="brand">
          <div className="logo">C</div>
          <div>
            <h1>Clara</h1>
            <p>AI Healthcare Navigation</p>
          </div>
        </div>
        <button className="profile-button">Demo User</button>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">YOUR CARE, MADE CLEAR</span>
            <h2>
              Understand what happened.
              <br />
              Know what comes next.
            </h2>

            <p className="hero-description">
              Clara helps turn medical paperwork into plain-English explanations,
              organized next steps, medication guidance, and a care plan you can actually follow.
            </p>

            <div className="hero-actions">
              <button
                className="primary-button"
                onClick={handleUpload}
                disabled={isProcessing}
              >
                {isProcessing
                  ? "Clara is working..."
                  : selectedFiles.length
                    ? "Review Medical Documents"
                    : "Upload Medical Documents"}
              </button>

              <button
                className="secondary-button"
                onClick={handleMyPlan}
                disabled={isProcessing}
              >
                View My Plan
              </button>
            </div>

            <p className="supported-files">
              Upload one or more after-visit summaries, discharge documents, PDFs, or photos.
            </p>
          </div>

          <div className="upload-card">
            <button
              type="button"
              className="upload-icon"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Add medical documents"
              title="Add medical documents"
              style={{
                border: "none",
                cursor: "pointer",
              }}
            >
              ＋
            </button>
            <h3>Start with your paperwork</h3>
            <p>
              Select multiple medical documents and Clara will review them together as one care episode.
            </p>

            <button
              className="upload-button"
              onClick={() => fileInputRef.current?.click()}
            >
              {selectedLabel}
            </button>

            {selectedFiles.length > 0 && (
              <div className="supported-files">
                <p>
                  {selectedFiles.length} document{selectedFiles.length === 1 ? "" : "s"} selected.
                  Press <strong>Review Medical Documents</strong> to send them to Clara.
                </p>
                <ul
                  style={{
                    textAlign: "left",
                    marginTop: "8px",
                    paddingLeft: "0",
                    listStyle: "none",
                  }}
                >
                  {selectedFiles.map((file, index) => (
                    <li
                      key={`${file.name}-${file.size}-${file.lastModified}`}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "12px",
                        marginBottom: "8px",
                      }}
                    >
                      <span>• {file.name}</span>

                      <button
                        type="button"
                        onClick={() => handleRemoveFile(index)}
                        disabled={isProcessing}
                        style={{
                          border: "1px solid #cfd5df",
                          borderRadius: "8px",
                          padding: "4px 8px",
                          cursor: "pointer",
                          background: "white",
                        }}
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="coming-soon">
              <span>MyChart connection</span>
              <span className="badge">Coming Soon</span>
            </div>
          </div>
        </section>

        {result && (
          <section className="safety" id="clara-results">
            <div className="shield">C</div>

            <div style={{ width: "100%" }}>
              <h3>{resultTitle}</h3>
              <p style={{ whiteSpace: "pre-wrap" }}>
                {cleanClaraText(result)}
              </p>

              {sessionId && resultTitle === "Clara's Review" && (
                <div className="hero-actions">
                  <button
                    className="primary-button"
                    onClick={handleSavePlan}
                    disabled={isProcessing}
                  >
                    {isProcessing ? "Saving..." : "Save My Plan"}
                  </button>
                </div>
              )}

              {activeSection === "tasks" && (
                <div
                  className="hero-actions"
                  style={{
                    marginTop: "18px",
                    alignItems: "center",
                    flexWrap: "wrap",
                  }}
                >
                  <input
                    type="text"
                    value={taskToComplete}
                    onChange={(e) => setTaskToComplete(e.target.value)}
                    placeholder="Example: Schedule follow-up"
                    disabled={isProcessing}
                    style={{
                      minWidth: "260px",
                      flex: "1",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      border: "1px solid #cfd5df",
                      fontSize: "15px",
                    }}
                  />
                  <button
                    className="primary-button"
                    onClick={handleCompleteTask}
                    disabled={isProcessing}
                  >
                    {isProcessing ? "Updating..." : "Mark Complete"}
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">YOUR CLARA DASHBOARD</span>
              <h2>Everything important, in one place.</h2>
            </div>
          </div>

          <div className="feature-grid">
            <article className={`feature-card ${activeSection === "visit" ? "featured" : ""}`}>
              <div className="feature-icon">📄</div>
              <h3>Visit Summary</h3>
              <p>Understand diagnoses, procedures, tests, and provider notes in everyday language.</p>
              <button onClick={handleVisitSummary} disabled={isProcessing}>
                Open Summary →
              </button>
            </article>

            <article className={`feature-card ${activeSection === "plan" ? "featured" : ""}`}>
              <div className="feature-icon">✓</div>
              <h3>My Plan</h3>
              <p>See your documented medications, tests, follow-ups, restrictions, and next steps.</p>
              <button onClick={handleMyPlan} disabled={isProcessing}>
                View My Plan →
              </button>
            </article>

            <article className={`feature-card ${activeSection === "medications" ? "featured" : ""}`}>
              <div className="feature-icon">💊</div>
              <h3>Medications</h3>
              <p>Organize documented medication instructions without guessing doses or timing.</p>
              <button onClick={handleMedications} disabled={isProcessing}>
                View Medications →
              </button>
            </article>

            <article className={`feature-card ${activeSection === "tasks" ? "featured" : ""}`}>
              <div className="feature-icon">◷</div>
              <h3>Pending Tasks</h3>
              <p>Keep track of what still needs to be completed across your saved care plan.</p>
              <button onClick={handlePendingTasks} disabled={isProcessing}>
                View Tasks →
              </button>
            </article>
          </div>
        </section>

        <section className="how-it-works">
          <span className="eyebrow">HOW CLARA WORKS</span>
          <h2>From paperwork to a clear plan.</h2>

          <div className="steps">
            <div className="step"><span>01</span><h3>Upload</h3><p>Share one or more medical documents with Clara.</p></div>
            <div className="step"><span>02</span><h3>Understand</h3><p>Clara identifies and explains the important information.</p></div>
            <div className="step"><span>03</span><h3>Organize</h3><p>Your documented next steps become one structured My Plan.</p></div>
            <div className="step"><span>04</span><h3>Keep Track</h3><p>Return later to see what is pending and what is complete.</p></div>
          </div>
        </section>

        <section className="safety">
          <div className="shield">✚</div>
          <div>
            <h3>Designed to explain — not diagnose.</h3>
            <p>
              Clara is an AI healthcare navigation assistant, not a doctor. Clara does not diagnose
              conditions, prescribe medications, or replace your healthcare team. Medical decisions
              should always be made with a qualified healthcare professional.
            </p>
          </div>
        </section>
      </main>

      <footer>
        <strong>Clara</strong>
        <span>AI Healthcare Navigation</span>
        <span>Hackathon Prototype · 2026</span>
      </footer>
    </div>
  );
}

export default App;
