import type { Breach } from "@/lib/types";

interface Props {
  breaches: Breach[];
}

export function BreachList({ breaches }: Props) {
  if (breaches.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-panel p-8 text-center text-muted">
        No known breaches found for this user&#39;s email addresses.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {breaches.map((b) => {
        const fields: string[] = (() => {
          try {
            return JSON.parse(b.exposed_fields);
          } catch {
            return [];
          }
        })();

        return (
          <div
            key={b.id}
            className="flex items-start gap-4 rounded-lg border border-border bg-panel p-4"
          >
            {b.catalogue?.LogoPath && (
              <img
                src={b.catalogue.LogoPath}
                alt={b.catalogue.Title}
                className="h-10 w-10 rounded object-contain flex-shrink-0 bg-gray-800"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-semibold text-gray-100">
                  {b.catalogue?.Title ?? b.breach_name}
                </h3>
                {b.breach_date && (
                  <span className="text-xs text-muted flex-shrink-0">
                    {new Date(b.breach_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                    })}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted mt-0.5">{b.email}</p>
              {b.catalogue?.Description && (
                <p
                  className="mt-1 text-xs text-gray-400 line-clamp-2"
                  dangerouslySetInnerHTML={{ __html: b.catalogue.Description }}
                />
              )}
              {fields.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {fields.map((field) => (
                    <span
                      key={field}
                      className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-400"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {b.hibp_url && (
              <a
                href={b.hibp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-accent hover:text-accent-hover flex-shrink-0"
              >
                Details ↗
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}
