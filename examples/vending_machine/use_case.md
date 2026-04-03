### **Use Case: Purchase Product**

**Level:** Sea-level 
**Primary Actor:** Customer  
**Secondary Actors:** 
* **Inventory**: Manages product stock levels.
* **Bank**: Manages physical coin validation and change dispensing.

**Preconditions:** 
* Vending Machine is powered on and displaying the "Select Product" screen.

**Minimal Guarantees (Failure Post-conditions):**
* No product is dispensed.
* Any coins inserted by the Customer during the current session are returned in full.
* Inventory levels remain unchanged.

**Success Post-conditions:**
* Customer has the selected product.
* Customer has correct change (Inserted - Price).
* Inventory for the selected product is decremented by 1.
* System balance is updated (Current Balance = 0).

**Main Success Scenario:**
1. **Customer** selects a product ID.
2. **System** checks with **Inventory** if the product is in stock.
3. **System** requests the price from the **Inventory**.
4. **Inventory** returns the price.
5. **System** prompts the **Customer** to insert coins.
6. **Customer** inserts coins into the **Bank**.
7. **Bank** notifies the **System** of the total inserted amount.
8. **System** validates that the inserted amount >= price.
9. **System** asks **Bank** if exact change can be dispensed (Amount - Price).
10. **System** commands **Inventory** to dispense the product.
11. **System** commands **Bank** to dispense the calculated change.
12. **System** records the transaction and resets the session balance.

**Extensions (Failure Paths):**
* **2a. Product Out of Stock:**
    * 2a1. **System** displays "Out of Stock" message.
    * 2a2. **System** resets to the "Select Product" state.
* **8a. Insufficient Funds:**
    * 8a1. **System** displays "Remaining Balance Required" and returns to step 6.
* **9a. Unable to Provide Change:**
    * 9a1. **System** displays "Exact Change Required" message.
    * 9a2. **System** commands **Bank** to return all inserted coins.
* **2-9a. Customer Cancels:**
    1. **Customer** presses the 'Cancel' button.
    2. **System** commands **Bank** to return all currently inserted coins.
    3. **System** resets to the "Select Product" state.
