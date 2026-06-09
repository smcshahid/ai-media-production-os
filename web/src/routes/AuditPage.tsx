/**
 * Audit route placeholder (US-26). The audit timeline (immutable event log) is a
 * Sprint 1+ screen; Sprint 0 ships the route with an empty state so navigation is
 * complete.
 */
export function AuditPage() {
  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Audit</h1>
      </header>
      <div className="card card--empty">
        <p>The audit timeline arrives in Sprint 1.</p>
        <p className="card__hint">
          It will render the immutable event log (uploads, approvals, pipeline runs) for the
          project.
        </p>
      </div>
    </section>
  );
}
