import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function RulesPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.rules"));

  return (
    <div>
      <PageHeader
        title={t("rules.title")}
        subtitle={t("rules.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("rules.title")}
        description={t("rules.subtitle")}
        stepHint="Step 11 will build interactive rules configuration with live rules.json preview"
      />
    </div>
  );
}
