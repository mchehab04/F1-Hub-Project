// Real-world F1 constructor livery colors, keyed by the Jolpica constructorRef
// used throughout this app's API (see docs/api-contract.md). Approximate --
// liveries shift slightly year to year -- close enough for UI accenting.
const TEAM_COLORS: Record<string, string> = {
  red_bull: "#3671C6",
  ferrari: "#E8002D",
  mercedes: "#27F4D2",
  mclaren: "#FF8000",
  aston_martin: "#229971",
  alpine: "#2293D1",
  williams: "#64C4FF",
  rb: "#6692FF",
  haas: "#B6BABD",
  sauber: "#52E252",
};

const FALLBACK_COLOR = "#94A3B8";

export function getTeamColor(constructorId: string | null | undefined): string {
  if (!constructorId) return FALLBACK_COLOR;
  return TEAM_COLORS[constructorId] ?? FALLBACK_COLOR;
}

// Simple WCAG-ish relative luminance check to decide readable text color
// against a team color used as a solid background.
export function getContrastText(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const [rl, gl, bl] = [r, g, b].map((c) =>
    c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  );
  const luminance = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
  return luminance > 0.55 ? "#111827" : "#ffffff";
}
