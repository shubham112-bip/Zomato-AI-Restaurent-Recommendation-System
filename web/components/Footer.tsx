export function Footer() {
  return (
    <footer className="border-t border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6">
        <div className="flex flex-col items-center gap-1 text-center sm:items-start sm:text-left">
          <span className="text-lg font-bold text-[#E23744]">zomato</span>
          <p className="text-xs text-[#696969]">
            © {new Date().getFullYear()} Zomato AI · Demo UI · All rights reserved.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[#696969]">Follow Us:</span>
          <div className="flex gap-2 text-[#696969]">
            {["f", "𝕏", "◎", "♪", "▶"].map((icon, i) => (
              <span
                key={i}
                className="flex h-8 w-8 cursor-default items-center justify-center rounded-full border border-zinc-200 text-xs hover:border-[#E23744] hover:text-[#E23744]"
                title="Social"
              >
                {icon}
              </span>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
