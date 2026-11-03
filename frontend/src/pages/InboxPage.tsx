import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function InboxPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.inbox"));

  return (
    <div>
      <PageHeader
        title={t("inbox.title")}
        subtitle={t("inbox.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("inbox.title")}
        description={t("inbox.subtitle")}
        stepHint="Step 7 will populate this screen with realistic B2B contractor intake data"
      />
    </div>
  );
}
