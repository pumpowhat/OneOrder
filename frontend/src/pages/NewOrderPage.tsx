import { Link, useNavigate } from "react-router";
import { createManualOrder } from "../api/orders.ts";
import { useI18n } from "../i18n/useI18n.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { Card } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";
import { OrderDraftForm } from "../components/orders/OrderDraftForm.tsx";

export default function NewOrderPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  useDocumentTitle(t("draft.create"));
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link className="text-sm text-ink-muted hover:text-ink" to="/orders">
        {t("order.back")}
      </Link>
      <PageHeader title={t("draft.create")} subtitle={t("draft.subtitle")} />
      <Card>
        <OrderDraftForm
          onSave={async (payload) => {
            const order = await createManualOrder(payload);
            navigate(`/orders/${order.id}`);
          }}
          onCancel={() => navigate("/orders")}
        />
      </Card>
    </div>
  );
}
