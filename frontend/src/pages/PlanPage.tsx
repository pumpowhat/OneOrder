import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function PlanPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.plan"));

  return (
    <div>
      <PageHeader
        title={t("plan.title")}
        subtitle={t("plan.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("plan.title")}
        description={t("plan.subtitle")}
        stepHint="Step 9 will build multi-country orchestration, crane allocation, and P50/P90 ETA comparison"
      />
    </div>
  );
}
