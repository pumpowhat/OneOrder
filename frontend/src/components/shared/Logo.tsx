import { cn } from "../../lib/cn.ts";

/** Many inputs merge into one line that ends in one delivery promise (the orange dot). */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg className={cn("w-8 h-8 shrink-0", className)} viewBox="0 0 120 120" fill="none" aria-hidden="true">
      <rect width="120" height="120" rx="26" fill="#15233F" stroke="rgba(245,242,236,0.18)" strokeWidth="2" />
      <g stroke="#F5F2EC" strokeWidth="9" strokeLinecap="round">
        <path d="M22 38H38C56 38 58 60 76 60" />
        <path d="M22 60H76" />
        <path d="M22 82H38C56 82 58 60 76 60" />
      </g>
      <path d="M72 60H90" stroke="#D9622B" strokeWidth="9" strokeLinecap="round" />
      <circle cx="98" cy="60" r="8.5" fill="#D9622B" />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="font-display text-[22px] leading-none font-semibold tracking-tight" aria-label="OneOrder">
        <span className="text-accent-ink">One</span>
        <span className="text-ink">Order</span>
      </span>
    </span>
  );
}
