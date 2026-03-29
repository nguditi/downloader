type ProgressBarProps = {
  progress: number;
};

export function ProgressBar({ progress }: ProgressBarProps) {
  return (
    <div className="progress-wrap" aria-label="download progress">
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${Math.max(0, Math.min(progress, 100))}%` }} />
      </div>
      <span className="progress-label">{progress}%</span>
    </div>
  );
}
