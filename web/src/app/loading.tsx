export default function Loading() {
  return (
    <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-solid border-[#00d4aa] border-r-transparent" />
        <p className="mt-4 text-white/60">Loading INDmoney Review Insights…</p>
      </div>
    </div>
  );
}
