export type Platform = "youtube" | "tiktok";

export type VideoFormat = {
  id: string;
  label: string;
  ext: string;
};

export type ResolveResponse = {
  platform: Platform;
  canonical_url: string;
  title: string;
  thumbnail_url: string;
  duration_seconds: number;
  formats: VideoFormat[];
};

export type CreateDownloadResponse = {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
};

export type DownloadStatusResponse = {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  file_name?: string;
  error?: string;
};

const API_BASE = "http://localhost:8001/api/v1";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? "Request failed");
  }
  return (await res.json()) as T;
}

export async function resolveUrl(url: string): Promise<ResolveResponse> {
  const res = await fetch(`${API_BASE}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return parseJson<ResolveResponse>(res);
}

export async function createDownload(url: string, formatId: string, agreedToTerms: boolean): Promise<CreateDownloadResponse> {
  const res = await fetch(`${API_BASE}/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      format_id: formatId,
      agreed_to_terms: agreedToTerms,
    }),
  });
  return parseJson<CreateDownloadResponse>(res);
}

export async function getDownloadStatus(jobId: string): Promise<DownloadStatusResponse> {
  const res = await fetch(`${API_BASE}/download/${jobId}`);
  return parseJson<DownloadStatusResponse>(res);
}

export function getDownloadFileUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}/file`;
}
