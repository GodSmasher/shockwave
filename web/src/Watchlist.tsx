type Company = { ticker: string; name: string; sector: string; alert?: number };

const WATCHLIST: Company[] = [
  { ticker: "AAPL",  name: "Apple",           sector: "Tech",       alert: 3 },
  { ticker: "NVDA",  name: "Nvidia",          sector: "Semis",      alert: 3 },
  { ticker: "TSLA",  name: "Tesla",           sector: "Auto",       alert: 2 },
  { ticker: "BA",    name: "Boeing",          sector: "Aerospace",  alert: 2 },
  { ticker: "AMD",   name: "AMD",             sector: "Semis",      alert: 2 },
  { ticker: "ASML",  name: "ASML",            sector: "Semi Eq.",   alert: 2 },
  { ticker: "NVO",   name: "Novo Nordisk",    sector: "Pharma",     alert: 2 },
  { ticker: "LLY",   name: "Eli Lilly",       sector: "Pharma",     alert: 2 },
  { ticker: "PFE",   name: "Pfizer",          sector: "Pharma",     alert: 1 },
  { ticker: "VOW3",  name: "Volkswagen",      sector: "Auto",       alert: 2 },
  { ticker: "GEHC",  name: "GE Healthcare",   sector: "MedTech",    alert: 2 },
  { ticker: "LMT",   name: "Lockheed Martin", sector: "Defense",    alert: 2 },
  { ticker: "HSY",   name: "Hershey",         sector: "Consumer",   alert: 1 },
  { ticker: "SBUX",  name: "Starbucks",       sector: "Consumer",   alert: 1 },
];

export { WATCHLIST };

export default function Watchlist({
  onSelect,
  active,
}: {
  onSelect: (query: string) => void;
  active?: string;
}) {
  // (legacy sidebar view, no longer used in dossier layout)
  return (
    <div className="h-full flex flex-col bg-panel/40 border-r border-hairline">
      {WATCHLIST.map((c) => (
        <button
          key={c.ticker}
          onClick={() => onSelect(`What hidden risks does ${c.name} carry?`)}
          className={`text-left px-4 py-2 border-b border-hairline/50 hover:bg-panelHi transition ${
            active === c.name ? "bg-panelHi" : ""
          }`}
        >
          <div className="flex items-baseline gap-2">
            <span className="mono text-[10px] text-inkDim">{c.ticker}</span>
            <span className="text-sm">{c.name}</span>
          </div>
          <div className="text-[10px] text-muted">{c.sector}</div>
        </button>
      ))}
    </div>
  );
}
