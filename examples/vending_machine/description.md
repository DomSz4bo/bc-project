### **System Intent: Vending Machine**

**Goal:** Allow a Customer to purchase a snack using coins, ensuring correct inventory management and change delivery.

**Core Logic:**
1.  **Product Selection:** The system maintains a list of products (e.g., "Cola" at $1.50, "Chips" at $1.00) and their current stock levels.
2.  **Payment:** The user inserts coins. The system tracks the "Current Balance."
3.  **Validation:** 
    *   The user must have enough balance for the selected item.
    *   The item must be in stock.
    *   The system must be able to return the exact change.
4.  **Dispensing:** On success, the system reduces stock, resets the balance, and returns any surplus as change.

---