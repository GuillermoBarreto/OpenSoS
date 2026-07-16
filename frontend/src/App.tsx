import './App.css'

function App() {
  return (
    <main className="app-shell">
      <section className="hero-section">
        <div className="hero-panel">
          <h1>OpenSoS</h1>
          <p>
            Open Source for Society is a community-driven platform for reporting,
            verifying, and visualizing public issues, emergencies, and
            humanitarian needs.
          </p>
          <div className="hero-actions">
            <a
              className="button primary"
              href="https://github.com/GuillermoBarreto/OpenSoS"
              target="_blank"
              rel="noreferrer"
            >
              View repository
            </a>
            <a
              className="button secondary"
              href="https://github.com/GuillermoBarreto/OpenSoS/pull/3"
              target="_blank"
              rel="noreferrer"
            >
              Review current PR
            </a>
          </div>
        </div>
      </section>

      <section className="features-section">
        <article className="feature-card">
          <h2>Project status</h2>
          <p>
            Frontend is configured with React, TypeScript, and Vite. Backend
            services and API endpoints are planned but not yet implemented.
          </p>
        </article>
        <article className="feature-card">
          <h2>Documentation</h2>
          <p>
            Docs are available in the repository under the `docs/` folder with
            architecture, deployment, and testing guides.
          </p>
        </article>
        <article className="feature-card">
          <h2>Goals</h2>
          <p>
            Build a collaborative platform for issue reporting, verification,
            and public data sharing across communities.
          </p>
        </article>
      </section>
    </main>
  )
}

export default App
