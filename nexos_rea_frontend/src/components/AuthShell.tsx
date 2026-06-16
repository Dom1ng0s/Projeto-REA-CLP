import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { BookOpen } from "lucide-react";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col justify-center px-4 sm:px-6 py-12">
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-secondary/40 via-background to-background" />
      <Link
        to="/"
        className="mx-auto mb-8 inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <BookOpen className="h-5 w-5" />
        </div>
        <span className="font-display text-xl">Nexos REA</span>
      </Link>

      <div className="rounded-xl border border-border bg-card p-8 shadow-sm">
        <h1 className="font-display text-3xl text-card-foreground">{title}</h1>
        {subtitle && (
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
        )}
        <div className="mt-6">{children}</div>
      </div>
    </div>
  );
}
