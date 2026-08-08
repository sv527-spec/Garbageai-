export default function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="card">
      <p className="text-sm text-primary-600 dark:text-primary-300">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
      {sub && <p className="text-xs text-primary-500 dark:text-primary-400 mt-1">{sub}</p>}
    </div>
  );
}
