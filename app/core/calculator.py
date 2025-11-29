from app.models.schemas import ExtractionData, PageWiseItems, BillItem

def reconcile_totals(raw_data: dict) -> ExtractionData:
    pagewise_items = []
    grand_total_items = 0
    raw_pages = raw_data.get("pagewise_line_items", [])

    for page in raw_pages:
        p_no = str(page.get("page_no", "1"))
        p_type = page.get("page_type", "Bill Detail")
        if p_type not in ["Bill Detail", "Final Bill", "Pharmacy"]:
            p_type = "Bill Detail"

        valid_items = []
        for item in page.get("bill_items", []):
            try:
                def clean_num(val):
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        c = val.replace(",", "").replace("₹", "").strip()
                        return float(c) if c else 0.0
                    return 0.0

                name = str(item.get("item_name", "Unknown"))
                qty = clean_num(item.get("item_quantity", 1))
                rate = clean_num(item.get("item_rate", 0))
                amount = clean_num(item.get("item_amount", 0))

                if amount == 0 and rate > 0:
                    amount = rate * qty

                valid_items.append(BillItem(
                    item_name=name,
                    item_amount=amount,
                    item_rate=rate,
                    item_quantity=qty
                ))
                grand_total_items += 1
            except:
                continue

        pagewise_items.append(PageWiseItems(
            page_no=p_no,
            page_type=p_type,
            bill_items=valid_items
        ))

    return ExtractionData(
        pagewise_line_items=pagewise_items,
        total_item_count=grand_total_items
    )
