import { PageHeader } from "../components/ui/PageHeader.tsx";
import { MockDataBanner } from "../components/ui/MockDataBanner.tsx";
import { PageStub } from "../components/shared/PageStub.tsx";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";

export default function StockPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.stock"));

  return (
    <div>
      <PageHeader
        title={t("stock.title")}
        subtitle={t("stock.subtitle")}
      />
      <MockDataBanner />
      <PageStub
        title={t("stock.title")}
        description={t("stock.subtitle")}
        stepHint="Step 10 will display unified inventory across DK, SE, NO with native ERP adapters"
      />
    </div>
  );
}
