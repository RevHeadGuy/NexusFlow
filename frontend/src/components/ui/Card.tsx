import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
  interactive,
}: {
  className?: string;
  children: React.ReactNode;
  interactive?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-xl overflow-hidden",
        interactive ? "surface-interactive" : "surface",
        className
      )}
    >
      {children}
    </div>
  );
}

export function GlassCard({ className, children, glow }: { className?: string; children: React.ReactNode; glow?: "blue" | "purple" }) {
  return (
    <div
      className={cn(
        "rounded-xl glass overflow-hidden",
        glow === "blue" && "glow-blue",
        glow === "purple" && "glow-purple",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("px-5 pt-5 pb-0", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <h3 className={cn("text-sm font-semibold text-[var(--text-primary)] tracking-tight", className)}>
      {children}
    </h3>
  );
}

export function CardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("p-5", className)}>{children}</div>;
}

export function CardDivider() {
  return <div className="h-px bg-white/5 mx-5" />;
}
