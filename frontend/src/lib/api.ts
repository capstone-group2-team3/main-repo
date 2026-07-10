import type { AnalyzePayload, AnalyzeResponse, PanelTemplate, TemplateOption } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function buildApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;

  const base = API_BASE_URL.replace(/\/+$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${cleanPath}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch {
    throw new Error(`Backend is not reachable. Start FastAPI on ${API_BASE_URL}.`);
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}.`);
  }
  try {
    return await response.json() as T;
  } catch {
    throw new Error("The backend returned an invalid JSON response.");
  }
}

export async function healthCheck(): Promise<boolean> {
  const response = await requestJson<{ status?: string }>("/health");
  return response.status === "ok";
}

export function normalizeTemplates(value: unknown): TemplateOption[] {
  let source: unknown = value;
  if (source && typeof source === "object" && !Array.isArray(source)) {
    const record = source as Record<string, unknown>;
    if (Array.isArray(record.templates)) source = record.templates;
    else if (Array.isArray(record.panels)) source = record.panels;
    else {
      return Object.entries(record)
        .filter(([key]) => !key.startsWith("_"))
        .map(([key, item]) => {
          const detail = item && typeof item === "object" ? item as Record<string, unknown> : {};
          return {
            name: key,
            display_name: String(detail.display_name || detail.name || key),
          };
        });
    }
  }
  if (!Array.isArray(source)) return [];
  return source.flatMap((item): TemplateOption[] => {
    if (typeof item === "string") return [{ name: item, display_name: item }];
    if (!item || typeof item !== "object") return [];
    const record = item as Record<string, unknown>;
    const name = record.name || record.panel_name || record.key || record.id || record.value;
    return name
      ? [{ name: String(name), display_name: String(record.display_name || record.label || name) }]
      : [];
  });
}

export async function fetchTemplates(): Promise<TemplateOption[]> {
  return normalizeTemplates(await requestJson<unknown>("/templates"));
}

export async function fetchTemplate(panelName: string): Promise<PanelTemplate> {
  const response = await requestJson<PanelTemplate | { template: PanelTemplate }>(
    `/templates/${encodeURIComponent(panelName)}`,
  );
  return "template" in response ? response.template : response;
}

export function analyzeReport(payload: AnalyzePayload): Promise<AnalyzeResponse> {
  return requestJson<AnalyzeResponse>("/reports/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
