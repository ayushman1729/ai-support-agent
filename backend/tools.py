from backend.database import get_db_connection

def get_order_details(order_id: int) -> dict:
    """
    Fetch live order details, delivery status, courier, and tracking details by order_id.
    Args:
        order_id: The integer ID of the order (e.g. 101, 102).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"Order #{order_id} not found in the database. Please verify the order number."}

    return {
        "order_id": row["order_id"],
        "customer_name": row["customer_name"],
        "item_name": row["item_name"],
        "status": row["status"],
        "courier": row["courier"],
        "tracking_id": row["tracking_id"],
        "estimated_delivery": row["estimated_delivery"],
        "total_amount": row["total_amount"]
    }

def cancel_order(order_id: int, reason: str = "Customer request") -> dict:
    """
    Cancel an existing order if it is in 'Processing' or 'Placed' status.
    Args:
        order_id: The integer ID of the order to cancel.
        reason: The reason for cancellation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, item_name FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": f"Order #{order_id} not found."}

    current_status = row["status"]

    if current_status == "Cancelled":
        conn.close()
        return {"success": False, "message": f"Order #{order_id} is already cancelled."}
    
    if current_status == "Delivered":
        conn.close()
        return {"success": False, "message": f"Order #{order_id} has already been delivered. It cannot be cancelled directly, but a return or ticket can be initiated."}

    if current_status == "Shipped":
        conn.close()
        return {"success": False, "message": f"Order #{order_id} is already shipped and in transit with courier. You can refuse delivery at doorstep or request a return once it arrives."}

    # If Processing or Placed, allow cancellation
    cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Order #{order_id} ({row['item_name']}) has been successfully cancelled. Refund will be processed in 24 hours.",
        "reason": reason
    }

def create_support_ticket(customer_name: str, issue_description: str, priority: str = "MEDIUM", order_id: int = None) -> dict:
    """
    Create a high-priority customer support ticket for escalation to human support agents.
    Args:
        customer_name: Name of the customer.
        issue_description: Detailed summary of what went wrong or why customer is unhappy.
        priority: Urgency level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
        order_id: Optional order ID if related to an order.
    """
    valid_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if priority.upper() not in valid_priorities:
        priority = "MEDIUM"
    else:
        priority = priority.upper()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (customer_name, order_id, issue_description, priority, status)
        VALUES (?, ?, ?, ?, 'OPEN')
    """, (customer_name, order_id, issue_description, priority))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "priority": priority,
        "message": f"Support ticket #{ticket_id} created with priority '{priority}'. A senior support manager has been assigned."
    }

def get_company_policy(topic: str) -> str:
    """
    Get company policy details regarding refunds, returns, warranty, or delivery times.
    Args:
        topic: Keyword such as 'refund', 'return', 'warranty', 'cancellation', 'shipping'.
    """
    topic = topic.lower()
    if "return" in topic or "refund" in topic:
        return "Return Policy: Products can be returned within 7 days of delivery if unopened or defective. Refund is credited within 24-48 hours after item pickup."
    elif "cancel" in topic:
        return "Cancellation Policy: Orders can be cancelled anytime before dispatch (status: Processing). Once shipped, delivery can be refused at doorstep."
    elif "warranty" in topic:
        return "Warranty Policy: All electronic products come with 1 year manufacturer brand warranty. Invoice can be downloaded from account."
    else:
        return "Shipping Policy: Standard shipping takes 2-4 business days. Express shipping delivers within 24 hours in metro cities."

# Registry mapping tool names to actual functions
AVAILABLE_TOOLS = {
    "get_order_details": get_order_details,
    "cancel_order": cancel_order,
    "create_support_ticket": create_support_ticket,
    "get_company_policy": get_company_policy
}
