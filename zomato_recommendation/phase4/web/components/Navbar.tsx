import Link from "next/link";

const links = [
  { href: "#", label: "Home", active: true },
  { href: "#", label: "Dining Out" },
  { href: "#", label: "Delivery" },
  { href: "#", label: "Profile" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-[#E23744]">zomato</span>
          <span className="text-lg font-semibold text-[#1C1C1C]">Zomato AI</span>
        </Link>
        <nav className="hidden gap-6 text-sm font-medium sm:flex">
          {links.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              className={
                l.active
                  ? "text-[#E23744] underline decoration-2 underline-offset-4"
                  : "text-[#696969] hover:text-[#1C1C1C]"
              }
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
