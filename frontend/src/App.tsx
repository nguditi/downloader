import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { ProgressBar } from "./components/ProgressBar";
import {
  createDownload,
  getDownloadFileUrl,
  getDownloadStatus,
  resolveUrl,
  ResolveResponse,
  DownloadStatusResponse,
} from "./lib/api";

export function App() {
  const [url, setUrl] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resolved, setResolved] = useState<ResolveResponse | null>(null);
  const [formatId, setFormatId] = useState("mp4-720p");
  const [job, setJob] = useState<DownloadStatusResponse | null>(null);

  const timerRef = useRef<number | null>(null);

  const canStartDownload = useMemo(() => {
    return Boolean(resolved && formatId && agreed && !loading);
  }, [resolved, formatId, agreed, loading]);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, []);

  async function onResolve(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setJob(null);
    setResolved(null);

    if (!url.trim()) {
      setError("Please paste a video URL first.");
      return;
    }

    try {
      setLoading(true);
      const data = await resolveUrl(url.trim());
      setResolved(data);
      setFormatId(data.formats[0]?.id ?? "mp4-720p");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cannot resolve URL.");
    } finally {
      setLoading(false);
    }
  }

  async function onCreateDownload() {
    if (!resolved) return;

    try {
      setLoading(true);
      setError(null);
      const created = await createDownload(resolved.canonical_url, formatId, agreed);

      const firstStatus = await getDownloadStatus(created.job_id);
      setJob(firstStatus);

      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }

      timerRef.current = window.setInterval(async () => {
        try {
          const status = await getDownloadStatus(created.job_id);
          setJob(status);

          if (status.status === "completed" || status.status === "failed") {
            if (timerRef.current) {
              window.clearInterval(timerRef.current);
              timerRef.current = null;
            }
          }
        } catch (pollErr) {
          setError(pollErr instanceof Error ? pollErr.message : "Cannot get job status.");
          if (timerRef.current) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
          }
        }
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create download.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="noise" />
      <main className="container">
        <header className="hero">
          <p className="kicker">ClipNest</p>
          <h1>YouTube + TikTok Downloader MVP</h1>
          <p>
            Use only for content you own or are authorized to use. This build supports real YouTube download and keeps TikTok behind a guarded fallback.
          </p>
        </header>

        <section className="card">
          <form onSubmit={onResolve} className="form">
            <label htmlFor="url">Video URL</label>
            <div className="row">
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
              />
              <button type="submit" disabled={loading}>Resolve</button>
            </div>
          </form>

          {error && <p className="error">{error}</p>}

          {resolved && (
            <div className="resolved">
              <img src={resolved.thumbnail_url} alt={resolved.title} />
              <div className="meta">
                <h2>{resolved.title}</h2>
                <p>Platform: {resolved.platform}</p>
                <p>Duration: {resolved.duration_seconds}s</p>

                <label htmlFor="format">Format</label>
                <select id="format" value={formatId} onChange={(e) => setFormatId(e.target.value)}>
                  {resolved.formats.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
                </select>

                <label className="checkbox">
                  <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
                  I confirm I own this content or have authorization to download it.
                </label>

                <button type="button" onClick={onCreateDownload} disabled={!canStartDownload}>
                  Start Download Job
                </button>
              </div>
            </div>
          )}

          {job && (
            <div className="job">
              <h3>Job: {job.job_id.slice(0, 8)}</h3>
              <p>Status: {job.status}</p>
              <ProgressBar progress={job.progress} />

              {job.status === "completed" && (
                <a className="download-link" href={getDownloadFileUrl(job.job_id)}>
                  Download File
                </a>
              )}

              {job.status === "failed" && <p className="error">{job.error ?? "Job failed"}</p>}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
