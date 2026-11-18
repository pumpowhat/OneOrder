"""Draft changes are validated before mutation and committed by the router."""
import json
from fastapi import HTTPException
from backend.db import OrderLineModel, order_model_to_dict, record_audit_log
from backend.services.matching import load_catalog
from backend.services.orders.crm_link import set_crm_link, unlink_if_customer_changed


def catalog_items():
    try:
        return load_catalog()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        raise HTTPException(503, f"Catalogue service unavailable: {exc}") from exc


def update_draft(db, order, payload):
    if order.status != "draft":
        raise HTTPException(409, "Only draft orders can be edited")
    catalog = {p.sku: p for p in catalog_items()}
    current = {line.line_index: line for line in order.lines}
    incoming = payload.lines
    if incoming is not None:
        indices = [line.line_index for line in incoming if line.line_index is not None]
        if len(indices) != len(set(indices)) or any(i not in current for i in indices):
            raise HTTPException(400, "Duplicate or unknown line index")
        for line in incoming:
            if line.sku and line.sku not in catalog:
                raise HTTPException(400, f"Invalid SKU '{line.sku}': not found in catalogue")
    before = order_model_to_dict(order)
    for name in ("customer", "customer_phone", "delivery_site", "requested_date"):
        if name in payload.model_fields_set:
            value = getattr(payload, name)
            setattr(order, name, value.isoformat() if name == "requested_date" and value else value or None)
    link_fields = {"crm_account_id", "crm_contact_id"} & payload.model_fields_set
    if link_fields:
        account = payload.crm_account_id if "crm_account_id" in link_fields else order.crm_account_id
        contact = payload.crm_contact_id if "crm_contact_id" in link_fields else order.crm_contact_id
        if "crm_account_id" in link_fields and account != order.crm_account_id and "crm_contact_id" not in link_fields:
            contact = None  # a new (or no) account never keeps the previous account's contact
        set_crm_link(db, order, account, contact, payload.user)
    else:
        unlink_if_customer_changed(db, order, before["customer"], before["customer_phone"], payload.user)
    if incoming is not None:
        # Include deleted lines in the high-water mark so indices never change meaning.
        historic = []
        for log in order.audit_logs:
            snapshot = log.payload_before if log.action == "delete_line" else log.payload_after
            if log.action in ("add_line", "delete_line") and snapshot:
                historic.append(json.loads(snapshot).get("line_index", -1))
        next_index = max([*current, *historic], default=-1) + 1
        retained = set()
        for item in incoming:
            product = catalog.get(item.sku)
            if item.line_index is None:
                line = OrderLineModel(line_index=next_index, confidence=0, source_text=None,
                                      candidates=None, match_score=None, ambiguous=0)
                order.lines.append(line)
                next_index += 1
                action = "add_line"
            else:
                line = current[item.line_index]
                retained.add(item.line_index)
                action = "edit_line"
            old = next((l for l in before["lines"] if l["line_index"] == line.line_index), None)
            changed = old is None or any((old["matched_sku"] != (item.sku or None),
                        old["description"] != item.description, old["quantity"] != item.quantity,
                        product is not None and old["unit"] != product.unit))
            line.description = item.description
            line.quantity = item.quantity
            line.matched_sku = item.sku or None
            if product:
                line.unit = product.unit
            if changed:
                # A previous AI match no longer establishes correctness after a manual edit.
                line.match_score = 0
            line.confirmed = int(item.confirmed)
            if changed or item.confirmed:
                line.ambiguous = 0
            after = {"line_index": line.line_index, "description": line.description,
                     "quantity": line.quantity, "matched_sku": line.matched_sku,
                     "confirmed": bool(line.confirmed), "unit": line.unit}
            if changed or (old and old["confirmed"] != item.confirmed):
                record_audit_log(db, order.id, action, payload.user, old, after)
        for idx, line in current.items():
            if idx not in retained:
                record_audit_log(db, order.id, "delete_line", payload.user,
                                 next(l for l in before["lines"] if l["line_index"] == idx), None)
                order.lines.remove(line)
    after_header = {name: getattr(order, name) for name in ("customer", "customer_phone", "delivery_site", "requested_date")}
    before_header = {name: before[name] for name in after_header}
    if before_header != after_header:
        record_audit_log(db, order.id, "edit_order", payload.user, before_header, after_header)
