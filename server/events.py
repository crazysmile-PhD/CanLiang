"""Simple event utilities for product emission."""
emitted_products = []


def emit_product(configGroupId, runId, productType, qty):
    """Record a product emission event.

    Args:
        configGroupId: Identifier of the config group.
        runId: Identifier of the current run.
        productType: Type of product generated.
        qty: Quantity of product generated.
    """
    emitted_products.append(
        {
            "configGroupId": configGroupId,
            "runId": runId,
            "productType": productType,
            "qty": qty,
        }
    )
