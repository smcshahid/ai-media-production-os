import { useState, type FormEvent } from "react";

import { ApiError, submitIdea } from "../api/client";

const PARAGRAPH_MIN = 50;
const PARAGRAPH_MAX = 2000;
const TITLE_MAX = 200;
const STYLE_NOTE_MAX = 500;

export interface IdeaCaptureFormProps {
  projectId: string;
  onSaved: () => void;
}

/**
 * Structured idea capture (US-11). Submits to ``POST /ideas``; does not start
 * the pipeline.
 */
export function IdeaCaptureForm({ projectId, onSaved }: IdeaCaptureFormProps) {
  const [title, setTitle] = useState("");
  const [paragraph, setParagraph] = useState("");
  const [styleNote, setStyleNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validateClient(): string | null {
    const trimmedTitle = title.trim();
    const trimmedParagraph = paragraph.trim();
    const trimmedStyle = styleNote.trim();

    if (!trimmedTitle) {
      return "Title is required.";
    }
    if (trimmedTitle.length > TITLE_MAX) {
      return `Title must be at most ${TITLE_MAX} characters.`;
    }
    if (trimmedParagraph.length < PARAGRAPH_MIN) {
      return `Idea paragraph must be at least ${PARAGRAPH_MIN} characters.`;
    }
    if (trimmedParagraph.length > PARAGRAPH_MAX) {
      return `Idea paragraph must be at most ${PARAGRAPH_MAX} characters.`;
    }
    if (trimmedStyle.length > STYLE_NOTE_MAX) {
      return `Style note must be at most ${STYLE_NOTE_MAX} characters.`;
    }
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clientError = validateClient();
    if (clientError) {
      setError(clientError);
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await submitIdea({
        project_id: projectId,
        title: title.trim(),
        paragraph: paragraph.trim(),
        style_note: styleNote.trim() || undefined,
      });
      setTitle("");
      setParagraph("");
      setStyleNote("");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save idea.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="idea-form" onSubmit={handleSubmit}>
      <label className="form-row form-row--stacked" htmlFor="idea-title">
        <span className="form-row__label">Title</span>
        <input
          id="idea-title"
          className="idea-form__input"
          type="text"
          value={title}
          maxLength={TITLE_MAX}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Working title"
          required
        />
      </label>

      <label className="form-row form-row--stacked" htmlFor="idea-paragraph">
        <span className="form-row__label">Idea</span>
        <textarea
          id="idea-paragraph"
          className="idea-form__textarea"
          rows={5}
          value={paragraph}
          maxLength={PARAGRAPH_MAX}
          onChange={(event) => setParagraph(event.target.value)}
          placeholder={`One paragraph (${PARAGRAPH_MIN}–${PARAGRAPH_MAX} characters)…`}
          required
        />
      </label>

      <label className="form-row form-row--stacked" htmlFor="idea-style">
        <span className="form-row__label">Style note</span>
        <input
          id="idea-style"
          className="idea-form__input"
          type="text"
          value={styleNote}
          maxLength={STYLE_NOTE_MAX}
          onChange={(event) => setStyleNote(event.target.value)}
          placeholder="Optional tone or visual direction"
        />
      </label>

      {error && (
        <p className="page__error" role="alert">
          {error}
        </p>
      )}

      <div className="card__actions">
        <button type="submit" className="button button--primary" disabled={submitting}>
          {submitting ? "Saving…" : "Save Idea"}
        </button>
      </div>
    </form>
  );
}
