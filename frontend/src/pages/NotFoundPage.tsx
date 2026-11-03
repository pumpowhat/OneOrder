import { Link } from "react-router";
import { AlertCircle } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function NotFoundPage() {
  const { t } = useI18n();
  useDocumentTitle(t("notFound.title"));

  return (
    <div className="py-12">
      <PageHeader title={t("notFound.title")} />
      <div className="max-w-md mx-auto text-center space-y-4 pt-10">
        <div className="w-12 h-12 rounded-full bg-warn-soft text-warn mx-auto flex items-center justify-center">
          <AlertCircle className="w-6 h-6" />
        </div>
        <p className="text-sm text-ink-muted">{t("notFound.description")}</p>
        <Link to="/inbox">
          <Button variant="primary">{t("notFound.backHome")}</Button>
        </Link>
      </div>
    </div>
  );
}
