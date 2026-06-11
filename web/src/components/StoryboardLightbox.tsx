import type { AssetVersion } from "../api/types";

interface StoryboardLightboxProps {
  frames: AssetVersion[];
  imageUrls: Record<string, string>;
  index: number;
  onClose: () => void;
  onNavigate: (nextIndex: number) => void;
}

/** Single-frame enlarged preview (US-17 T-17-02). */
export function StoryboardLightbox({
  frames,
  imageUrls,
  index,
  onClose,
  onNavigate,
}: StoryboardLightboxProps) {
  const frame = frames[index];
  if (!frame) {
    return null;
  }
  const url = imageUrls[frame.id];
  const meta = frame.metadata_json ?? {};
  const shotLabel = typeof meta.shot_label === "string" ? meta.shot_label : null;
  const frameNum =
    typeof meta.frame_index === "number"
      ? meta.frame_index
      : typeof meta.frame_index === "string"
        ? meta.frame_index
        : index + 1;

  return (
    <div
      className="storyboard-lightbox"
      role="dialog"
      aria-modal="true"
      aria-label={`Frame ${frameNum} preview`}
      onClick={onClose}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          onClose();
        }
      }}
    >
      <div className="storyboard-lightbox__panel" onClick={(event) => event.stopPropagation()}>
        <header className="storyboard-lightbox__header">
          <span>
            Frame {frameNum}
            {shotLabel ? ` · ${shotLabel}` : ""}
          </span>
          <button type="button" className="button" onClick={onClose}>
            Close
          </button>
        </header>
        {url ? (
          <img className="storyboard-lightbox__image" src={url} alt={`Storyboard frame ${frameNum}`} />
        ) : (
          <p className="page__error">Image unavailable.</p>
        )}
        <footer className="storyboard-lightbox__footer">
          <button
            type="button"
            className="button"
            disabled={index <= 0}
            onClick={() => onNavigate(index - 1)}
          >
            Previous
          </button>
          <button
            type="button"
            className="button"
            disabled={index >= frames.length - 1}
            onClick={() => onNavigate(index + 1)}
          >
            Next
          </button>
        </footer>
      </div>
    </div>
  );
}
