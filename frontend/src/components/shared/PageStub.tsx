import type { ReactNode } from "react";
import { Construction } from "lucide-react";
import { Card, CardBody } from "../ui/Card";

export interface PageStubProps {
  title: string;
  description: string;
  icon?: ReactNode;
  stepHint?: string;
}

export function PageStub({ title, description, icon, stepHint }: PageStubProps) {
  return (
    <Card className="border-dashed">
      <CardBody className="py-16 text-center flex flex-col items-center">
        <div className="w-12 h-12 rounded-2xl bg-brand-soft border border-brand/20 flex items-center justify-center text-brand mb-4">
          {icon || <Construction className="w-6 h-6" />}
        </div>
        <h3 className="text-lg font-semibold text-ink mb-1">{title}</h3>
        <p className="text-sm text-ink-muted max-w-md mb-4">{description}</p>
        {stepHint && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-surface-2 text-ink-muted border border-line">
            {stepHint}
          </span>
        )}
      </CardBody>
    </Card>
  );
}
