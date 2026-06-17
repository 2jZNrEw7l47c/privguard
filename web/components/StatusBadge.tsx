import type { FindingStatus } from "@/lib/types";

const LABELS: Record<FindingStatus, string> = {
  found: "Found",
  not_found: "Not Found",
  submitted: "Submitted",
  pending_verification: "Pending Verification",
  manual_required: "Manual Required",
  cleared: "Cleared",
};

const CLASSES: Record<FindingStatus, string> = {
  found: "bg-red-900 text-red-200",
  not_found: "bg-gray-800 text-gray-400",
  submitted: "bg-indigo-900 text-indigo-200",
  pending_verification: "bg-yellow-900 text-yellow-200",
  manual_required: "bg-orange-900 text-orange-200",
  cleared: "bg-green-900 text-green-200",
};

interface Props {
  status: FindingStatus;
}

export function StatusBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CLASSES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
