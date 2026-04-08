### **Use Case: Package Locker Pickup**

**Level:** Sea-level 
**Primary Actor:** Customer  
**Secondary Actors:** 
* **Locker Database**: Stores package records, pickup codes, door assignments, and overdue fee amounts.
* **Payment Terminal**: Processes credit card transactions and void requests.
* **Hardware Controller**: Physically opens locker doors and reports door status.

**Preconditions:** 
* System is idle and displaying the "Enter Pickup Code" screen.

**Minimal Guarantees (Failure Post-conditions):**
* Locker door remains closed.
* Package status in the database is not changed to "Picked Up".
* If a payment was collected but the door failed to open, the payment transaction is voided.

**Success Post-conditions:**
* The assigned locker door is open.
* Any required overdue fees are successfully charged.
* Package status in the Locker Database is updated to "Picked Up".

**Main Success Scenario:**
1. **Customer** enters their pickup code into the **System**.
2. **System** requests package details for the code from the **Locker Database**.
3. **Locker Database** returns package details including the door number and an overdue fee of $0.00.
4. **System** commands the **Hardware Controller** to open the specified door.
5. **Hardware Controller** confirms the door has successfully opened.
6. **System** commands the **Locker Database** to update the package status to "Picked Up".
7. **System** displays a success message to the **Customer** indicating their door is open.

**Extensions (Failure Paths & Conditionals):**
* **3a. Package has an Overdue Fee:**
    * 3a1. **Locker Database** returns package details with an overdue fee > $0.00.
    * 3a2. **System** prompts the **Customer** to pay the specified fee amount.
    * 3a3. **Customer** taps their card on the **Payment Terminal**.
    * 3a4. **Payment Terminal** confirms a successful payment to the **System**.
    * 3a5. **System** resumes at step 4.
* **3a4a. Payment Declined:**
    * 1. **Payment Terminal** reports that the payment was declined.
    * 2. **System** displays a "Payment Failed" error message to the **Customer**.
    * 3. **System** aborts the pickup process and returns to the idle screen.
* **3b. Invalid or Expired Pickup Code:**
    * 3b1. **Locker Database** returns a "Not Found" or "Expired" status.
    * 3b2. **System** displays an "Invalid Code" error message to the **Customer**.
    * 3b3. **System** aborts the pickup process and returns to the idle screen.
* **5a. Hardware Door Jam:**
    * 5a1. **Hardware Controller** reports a failure to open the specified door.
    * 5a2. **System** displays a "Hardware Error - Please contact support" message.
    * 5a3. **System** checks if a fee was paid during this session. If yes, **System** commands the **Payment Terminal** to void the transaction.
    * 5a4. **System** aborts the pickup process (package status remains unchanged).
* **1-4a. Customer Cancels:**
    * 1. **Customer** presses the 'Cancel' button on the screen.
    * 2. **System** aborts the pickup process and returns to the idle screen.