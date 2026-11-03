import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function ReviewPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.review"));

  return (
    <div>
      <PageHeader
        title={t("review.title")}
        subtitle={t("review.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("review.title")}
        description={t("review.subtitle")}
        stepHint="Step 8 will build interactive line verification, SKU candidate selection, and audit trail"
      />
    </div>
  );
}
