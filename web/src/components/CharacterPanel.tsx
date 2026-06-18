import { useCallback, useEffect, useState } from "react";

import { ApiError, createCharacter, listCharacters } from "../api/client";
import type { Character } from "../api/types";

interface CharacterPanelProps {
  projectId: string;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

const MAX_CHARACTERS = 3;

export function CharacterPanel({
  projectId,
  selectedIds,
  onSelectionChange,
}: CharacterPanelProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [description, setDescription] = useState("");
  const [visualTraits, setVisualTraits] = useState("");
  const [personality, setPersonality] = useState("");
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
    if (!name.trim()) {
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
        name: name.trim(),
        role: role.trim() || null,
        description: description.trim() || null,
        visual_traits: visualTraits.trim() || null,
        personality_notes: personality.trim() || null,
      });
      setName("");
      setRole("");
      setDescription("");
      setVisualTraits("");
      setPersonality("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create character.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <h2 className="card__title">Characters</h2>
      <p className="card__hint">
        Pilot: up to {MAX_CHARACTERS} characters per project. Select up to {MAX_CHARACTERS} for the next pipeline run.
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
              {character.visual_traits && (
                <p className="card__hint">Visual: {character.visual_traits}</p>
              )}
            </li>
          ))}
        </ul>
      )}
      {characters.length < MAX_CHARACTERS && (
        <div className="card__field">
          <input
            className="input"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="input"
            placeholder="Role (e.g. protagonist)"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <textarea
            className="input"
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
          />
          <textarea
            className="input"
            placeholder="Visual traits"
            value={visualTraits}
            onChange={(e) => setVisualTraits(e.target.value)}
            rows={2}
          />
          <textarea
            className="input"
            placeholder="Personality notes"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            rows={2}
          />
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
