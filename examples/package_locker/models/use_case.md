### **Use Case: Package Locker Pickup**

**Primary Actor:** Customer  
**Secondary Actors:** 
* **Locker Database**: Stores package records, pickup codes, door assignments, and delivery timestamps.
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
3. **Locker Database** returns package details including the door number and the delivery timestamp.
4. **System** calculates the overdue fee based on the delivery timestamp (1.00€ per day after 3 days). The calculated fee is 0.00€.
5. **System** commands the **Hardware Controller** to open the specified door.
6. **Hardware Controller** confirms the door has successfully opened.
7. **System** commands the **Locker Database** to update the package status to "Picked Up".
8. **System** displays a success message to the **Customer** indicating their door is open.

**Extensions (Failure Paths & Conditionals):**
* **3a. Invalid or Expired Pickup Code:**
    * 3a1. **Locker Database** returns a "Not Found" or "Expired" status.
    * 3a2. **System** displays an "Invalid Code" error message to the **Customer**.
    * 3a3. **System** aborts the pickup process and returns to the idle screen.
* **4a. Package has an Overdue Fee:**
    * 4a1. **System** calculates an overdue fee > 0.00€ based on the delivery timestamp.
    * 4a2. **System** prompts the **Customer** to pay the specified fee amount.
    * 4a3. **Customer** taps their card on the **Payment Terminal**.
    * 4a4. **Payment Terminal** confirms a successful payment to the **System**.
    * 4a5. **System** resumes at step 5.
* **4a4a. Payment Declined:**
    * 4a4a1. **Payment Terminal** reports that the payment was declined.
    * 4a4a2. **System** displays a "Payment Failed" error message to the **Customer**.
    * 4a4a3. **System** aborts the pickup process and returns to the idle screen.
* **6a. Hardware Door Jam:**
    * 6a1. **Hardware Controller** reports a failure to open the specified door.
    * 6a2. **System** displays a "Hardware Error - Please contact support" message.
    * 6a3. **System** checks if a fee was paid during this session. If yes, **System** commands the **Payment Terminal** to void the transaction.
    * 6a4. **System** aborts the pickup process (package status remains unchanged).
