type Props = {
  label: string;
  value: string | number;
  sub?: string;
  tone?: "default" | "risk" | "ok" | "warn";
  big?: boolean;
};

const toneClass: Record<string, string> = {
  default: "text-ink",
  risk: "text-risk",
  ok: "text-ok",
  warn: "text-warn",
};

export default function StatTile({ label, value, sub, tone = "default", big }: Props) {
  return (
    <div className="flex flex-col gap-0.5 min-w-[120px]">
      <div className="text-[10px] uppercase tracking-[0.1em] text-muted font-medium">
        {label}
      </div>
      <div className={`display ${big ? "text-4xl" : "text-2xl"} ${toneClass[tone]} leading-none`}>
        {value}
      </div>
      {sub && (
        <div className="text-[11px] text-inkDim mono mt-1">{sub}</div>
      )}
    </div>
  );
}
