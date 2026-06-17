interface Stat {
  label: string;
  value: number;
  accent?: "danger" | "warning" | "success" | "default";
}

const ACCENT_CLASSES = {
  danger: "text-red-400",
  warning: "text-yellow-400",
  success: "text-green-400",
  default: "text-indigo-400",
};

interface Props {
  stats: Stat[];
}

export function StatCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-lg border border-border bg-panel p-4"
        >
          <p className="text-sm text-muted">{s.label}</p>
          <p
            className={`mt-1 text-3xl font-bold ${
              ACCENT_CLASSES[s.accent ?? "default"]
            }`}
          >
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}
