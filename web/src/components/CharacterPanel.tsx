import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  createCharacter,
  deleteCharacter,
  listCharacters,
  updateCharacter,
} from "../api/client";
import type { Character } from "../api/types";

interface CharacterPanelProps {
  projectId: string;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

const MAX_CHARACTERS = 3;

type FormState = {
  name: string;
  role: string;
  description: string;
  visualTraits: string;
  personality: string;
};

const emptyForm = (): FormState => ({
  name: "",
  role: "",
  description: "",
  visualTraits: "",
  personality: "",
});

function formFromCharacter(character: Character): FormState {
  return {
    name: character.name,
    role: character.role ?? "",
    description: character.description ?? "",
    visualTraits: character.visual_traits ?? "",
    personality: character.personality_notes ?? "",
  };
}

export function CharacterPanel({
  projectId,
  selectedIds,
  onSelectionChange,
}: CharacterPanelProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState<FormState>(emptyForm);
  const [viewId, setViewId] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);

  const refresh = useCallback(async () => {
    const response = await listCharacters(projectId);
    setCharacters(response.characters);
  }, [projectId]);

  useEffect(() => {
    void refresh().catch(() => setError("Failed to load characters."));
  }, [refresh]);

  function toggleSelection(id: string) {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((x) => x !== id));
      return;
    }
    if (selectedIds.length >= MAX_CHARACTERS) {
      setError(`Select at most ${MAX_CHARACTERS} characters per run.`);
      return;
    }
    setError(null);
    onSelectionChange([...selectedIds, id]);
  }

  async function handleCreate() {
    if (!createForm.name.trim()) {
      setError("Character name is required.");
      return;
    }
    if (characters.length >= MAX_CHARACTERS) {
      setError(`Maximum ${MAX_CHARACTERS} characters per project.`);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createCharacter({
        project_id: projectId,
        name: createForm.name.trim(),
        role: createForm.role.trim() || null,
        description: createForm.description.trim() || null,
        visual_traits: createForm.visualTraits.trim() || null,
        personality_notes: createForm.personality.trim() || null,
      });
      setCreateForm(emptyForm());
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create character.");
    } finally {
      setSaving(false);
    }
  }

  function startEdit(character: Character) {
    setViewId(null);
    setEditId(character.id);
    setEditForm(formFromCharacter(character));
    setError(null);
  }

  async function handleSaveEdit(characterId: string) {
    if (!editForm.name.trim()) {
      setError("Character name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateCharacter(characterId, projectId, {
        name: editForm.name.trim(),
        role: editForm.role.trim() || null,
        description: editForm.description.trim() || null,
        visual_traits: editForm.visualTraits.trim() || null,
        personality_notes: editForm.personality.trim() || null,
      });
      setEditId(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update character.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(character: Character) {
    const confirmed = window.confirm(
      `Delete ${character.name}? Completed pipeline exports keep their snapshot; active runs block deletion.`,
    );
    if (!confirmed) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await deleteCharacter(character.id, projectId);
      if (selectedIds.includes(character.id)) {
        onSelectionChange(selectedIds.filter((id) => id !== character.id));
      }
      if (viewId === character.id) {
        setViewId(null);
      }
      if (editId === character.id) {
        setEditId(null);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete character.");
    } finally {
      setSaving(false);
    }
  }

  function renderField(
    label: string,
    value: string,
    onChange: (value: string) => void,
    multiline = false,
  ) {
    const common = {
      className: "input",
      value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        onChange(e.target.value),
    };
    return (
      <label className="card__field">
        {label}
        {multiline ? <textarea {...common} rows={2} /> : <input {...common} />}
      </label>
    );
  }

  return (
    <div className="card">
      <h2 className="card__title">Characters</h2>
      <p className="card__hint">
        Up to {MAX_CHARACTERS} characters per project. Select up to {MAX_CHARACTERS} for the next
        pipeline run. Edits apply to future runs; completed exports keep their start-time snapshot.
      </p>
      {characters.length > 0 && (
        <ul className="card__list">
          {characters.map((character) => (
            <li key={character.id}>
              <label>
                <input
                  type="checkbox"
                  checked={selectedIds.includes(character.id)}
                  onChange={() => toggleSelection(character.id)}
                />{" "}
                <strong>{character.name}</strong>
                {character.role ? ` (${character.role})` : ""}
              </label>
              <div className="card__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => {
                    setEditId(null);
                    setViewId(viewId === character.id ? null : character.id);
                  }}
                >
                  {viewId === character.id ? "Hide" : "View"}
                </button>
                <button
                  type="button"
                  className="button button--secondary"
                  disabled={saving}
                  onClick={() => startEdit(character)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="button button--secondary"
                  disabled={saving}
                  onClick={() => void handleDelete(character)}
                >
                  Delete
                </button>
              </div>
              {viewId === character.id && editId !== character.id && (
                <div className="card__detail">
                  {character.description && <p>{character.description}</p>}
                  {character.visual_traits && (
                    <p className="card__hint">Visual: {character.visual_traits}</p>
                  )}
                  {character.personality_notes && (
                    <p className="card__hint">Personality: {character.personality_notes}</p>
                  )}
                </div>
              )}
              {editId === character.id && (
                <div className="card__field">
                  {renderField("Name", editForm.name, (v) =>
                    setEditForm((f) => ({ ...f, name: v })),
                  )}
                  {renderField("Role", editForm.role, (v) =>
                    setEditForm((f) => ({ ...f, role: v })),
                  )}
                  {renderField(
                    "Description",
                    editForm.description,
                    (v) => setEditForm((f) => ({ ...f, description: v })),
                    true,
                  )}
                  {renderField(
                    "Visual traits",
                    editForm.visualTraits,
                    (v) => setEditForm((f) => ({ ...f, visualTraits: v })),
                    true,
                  )}
                  {renderField(
                    "Personality notes",
                    editForm.personality,
                    (v) => setEditForm((f) => ({ ...f, personality: v })),
                    true,
                  )}
                  <button
                    type="button"
                    className="button"
                    disabled={saving}
                    onClick={() => void handleSaveEdit(character.id)}
                  >
                    {saving ? "Saving…" : "Save"}
                  </button>
                  <button
                    type="button"
                    className="button button--secondary"
                    disabled={saving}
                    onClick={() => setEditId(null)}
                  >
                    Cancel
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {characters.length < MAX_CHARACTERS && (
        <div className="card__field">
          {renderField("Name", createForm.name, (v) =>
            setCreateForm((f) => ({ ...f, name: v })),
          )}
          {renderField("Role", createForm.role, (v) =>
            setCreateForm((f) => ({ ...f, role: v })),
          )}
          {renderField(
            "Description",
            createForm.description,
            (v) => setCreateForm((f) => ({ ...f, description: v })),
            true,
          )}
          {renderField(
            "Visual traits",
            createForm.visualTraits,
            (v) => setCreateForm((f) => ({ ...f, visualTraits: v })),
            true,
          )}
          {renderField(
            "Personality notes",
            createForm.personality,
            (v) => setCreateForm((f) => ({ ...f, personality: v })),
            true,
          )}
          <button type="button" className="button" disabled={saving} onClick={() => void handleCreate()}>
            {saving ? "Saving…" : "Add Character"}
          </button>
        </div>
      )}
      {error && (
        <p className="page__error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
