import type { Metadata } from "next";
import { Suspense } from "react";
import { NavLinks } from "@/components/NavLinks";
import "./globals.css";

export const metadata: Metadata = {
  title: "Corneal Topography",
  description: "Browse corneal topography exams and the values printed on their maps.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <div className="container topbar__inner">
            <span className="brand">Corneal Topography</span>
            <Suspense fallback={null}>
              <NavLinks />
            </Suspense>
          </div>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
