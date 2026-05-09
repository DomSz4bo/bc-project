### **Use Case: Place Hold on Checked-Out Book**

**Primary Actor:** Librarian  
**Secondary Actors:** 
* **Library Database**: Stores all records for both customers (fines, current hold counts) and books (availability status, hold queues).

**Minimal Guarantees (Failure Post-conditions):**
* No hold is placed on the book.
* The customer's hold count remains unchanged.
* The book's hold queue remains unchanged.

**Success Post-conditions:**
* The customer is added to the hold queue for the specified book.
* The customer's active hold count is incremented by 1 in the database.
* The system displays a successful hold confirmation.

**Main Success Scenario:**
1. **Librarian** enters the Customer ID and Book ID to place a hold.
2. **System** requests the customer's record (fines and current hold count) from the **Library Database**.
3. **Library Database** returns the customer record, showing no unpaid fines and a hold count below the maximum limit.
4. **System** requests the book's record from the **Library Database**.
5. **Library Database** returns the book's record, showing its status as "Checked Out" and eligible for holds.
6. **System** commands the **Library Database** to add the Customer ID to the book's hold queue.
7. **System** commands the **Library Database** to increment the customer's active hold count.
8. **System** displays a confirmation message to the **Librarian**.

**Extensions (Failure Paths):**
* **3a. Customer entry not found:**
    * 3a1. **Library Database** doesn't find the customer entry.
    * 3a2. **System** displays an error message stating the customer cannot be found.
    * 3a3. **System** aborts the hold process.
* **3b. Customer has Unpaid Fines:**
    * 3b1. **Library Database** returns a record indicating unpaid fines.
    * 3b2. **System** displays an error message stating the customer cannot place holds until fines are paid.
    * 3b3. **System** aborts the hold process.
* **3c. Customer Reached Maximum Holds:**
    * 3c1. **Library Database** returns a hold count at or exceeding the allowed limit.
    * 3c2. **System** displays an error message stating the customer has reached the maximum hold limit.
    * 3c3. **System** aborts the hold process.
* **5a. Book entry not found:**
    * 5a1. **Library Database** doesn't find the book entry.
    * 5a2. **System** displays a error message stating the book cannot be found.
    * 5a3. **System** aborts the hold process.
* **5b. Book is Actually Available:**
    * 5b1. **Library Database** returns the book's status as "Available".
    * 5b2. **System** displays a message to the Librarian that the book is currently on the shelf and cannot be put on hold.
    * 5b3. **System** aborts the hold process.
* **5c. Book Not Eligible for Holds (e.g., Reference or Lost):**
    * 5c1. **Library Database** returns a status indicating the book cannot be reserved.
    * 5c2. **System** displays an error message stating the book is not eligible for holds.
    * 5c3. **System** aborts the hold process.
