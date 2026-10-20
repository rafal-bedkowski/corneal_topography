"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Exams" },
  { href: "/stats", label: "Statistics" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main">
      <ul className="nav">
        {LINKS.map(({ href, label }) => {
          const active =
            href === "/"
              ? pathname === "/" || pathname.startsWith("/exams")
              : pathname.startsWith(href);
          return (
            <li key={href}>
              <Link
                href={href}
                className={active ? "nav__link nav__link--active" : "nav__link"}
                aria-current={active ? "page" : undefined}
              >
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
