import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function ModelPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.model"));

  return (
    <div>
      <PageHeader
        title={t("model.title")}
        subtitle={t("model.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("model.title")}
        description={t("model.subtitle")}
        stepHint="Step 12 will build ETA model metrics, 8-feature importance chart, and What-If simulator"
      />
    </div>
  );
}
