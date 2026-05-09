I need a simple local library management system that a librarian can use at their desk to place a hold on a book for a customer. 

The librarian will enter the customer's ID and the book's ID. The system should check if the customer is allowed to place a hold (they shouldn't have any unpaid fines, and they can't have reached their maximum hold limit). It also needs to verify that the book is currently checked out to someone else and is actually eligible for holds (like not being a reference-only book). 

If everything is valid, the system should add the customer to the book's waitlist and show a success message.