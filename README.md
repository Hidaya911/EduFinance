# EduFinance

## School Financial Management System – Lebanese School Context

EduFinance is a full-stack **School Financial Management System** designed to centralize and simplify the financial operations of a Lebanese school.

The system provides authorized school staff with a centralized platform for managing the complete student financial lifecycle, including academic-year configuration, fee structures, invoices, payments, installments, receipts, scholarships, discounts, refunds, expenses, suppliers, reporting, notifications, and audit records.

EduFinance is designed with a strong focus on **financial accuracy, security, accountability, traceability, automation, and ease of use**.

---

## 📌 Project Overview

Traditional school financial management may rely on spreadsheets, paper receipts, separate accounting files, or disconnected systems. This can make it difficult to:

* Track how much each student owes
* Manage partial payments
* Track installments
* Maintain accurate outstanding balances
* Generate receipts
* Apply discounts and scholarships consistently
* Identify overdue payments
* Track school expenses and suppliers
* Prepare financial reports
* Maintain financial history and auditability
* Control access to sensitive financial information

EduFinance addresses these challenges through one centralized web-based financial management platform.

---

## 🎯 Business Objectives

EduFinance aims to:

* Centralize school financial operations
* Improve financial calculation accuracy
* Simplify payment and installment tracking
* Improve financial transparency
* Support management decision-making through dashboards and reports
* Reduce manual financial operations
* Provide secure role-based access
* Maintain complete financial transaction history
* Provide a professional and easy-to-use interface

---

## 🏫 Lebanese School Context

The system is designed specifically with Lebanese school operations in mind.

The financial system supports configurable:

* USD and/or LBP currencies
* Tuition fees
* Registration fees
* Books
* Uniforms
* Technology fees
* Activities
* Sports
* Laboratory fees
* Transportation fees
* Scholarships
* Discounts
* Installments
* School expenses
* Supplier payments

### Transportation Fees

Transportation is treated as a configurable school fee category rather than a hardcoded pricing model.

Schools may configure transportation according to factors such as:

* Pickup/drop-off area
* Route
* Zone
* One-way transportation
* Two-way transportation
* Academic year

Examples may include Beirut / Mount Lebanon routes, local-area routes, and distant-area routes.

---

## 👥 System Users

EduFinance supports different user roles with different levels of access.

### Super Administrator

Has complete control over the application, including:

* User management
* Role and permission management
* School settings
* Academic configuration
* Financial configuration
* System configuration
* Audit logs
* Financial records
* Reports

### School Administrator / Manager

Responsible for school-level management operations, including:

* Management dashboard
* Financial reports
* Student information
* Invoices
* Payments
* Expenses
* Suppliers
* Academic years
* Fee structures
* Approval of sensitive financial operations

### Accountant

The accountant manages the majority of financial operations:

* Student financial accounts
* Invoice generation
* Payments
* Partial payments
* Installment plans
* Receipts
* Discounts
* Scholarships
* Refunds
* Expenses
* Suppliers
* Supplier bills
* Supplier payments
* Account statements
* Financial reports
* Overdue accounts

### Cashier

The cashier has limited payment-related permissions:

* Search students
* View student balances
* Receive payments
* Record payment methods
* Generate receipts
* Print receipts
* View daily transactions

The cashier does not have permission to modify fee structures, approve discounts or refunds, manage users, delete financial records, or access sensitive management reports.

### Parent / Student Portal

An optional portal may allow parents or students to view information related only to their own financial account, including:

* Current balance
* Invoices
* Payments
* Receipts
* Installments
* Upcoming payments
* Overdue payments
* Scholarships
* Discounts
* Account statements
* Notifications

### Auditor / Read-Only User

Auditors can view:

* Financial transactions
* Reports
* Statements
* Audit history

Auditors cannot create, edit, delete, or approve financial transactions.

---

# 🧩 Main Modules

EduFinance is planned around the following modules:

1. Authentication
2. User Management
3. Role & Permission Management
4. School Configuration
5. Academic Year Management
6. Grade & Class Management
7. Student Management
8. Guardian Management
9. Student Financial Accounts
10. Fee Categories
11. Fee Structures
12. Student Invoices
13. Invoice Items
14. Payments
15. Partial Payments
16. Payment Allocation
17. Receipts
18. Installment Plans
19. Discounts
20. Scholarships
21. Financial Assistance
22. Refunds
23. Late Payment Tracking
24. Payment Reminders
25. Expense Management
26. Expense Categories
27. Supplier Management
28. Supplier Bills
29. Supplier Payments
30. Employee Financial Records
31. Student Account Statements
32. Financial Reports
33. Dashboard & Analytics
34. Notifications
35. Approval Workflows
36. Audit Logs
37. File & Document Attachments
38. PDF Export
39. Excel Export
40. Search & Filtering

---

# 💰 Financial Management

## Fee Management

Administrators can configure fee categories and fee structures based on:

* Academic year
* Grade
* Student group
* Fee category

Example:

| Fee Category |     Amount |
| ------------ | ---------: |
| Tuition      |     $3,000 |
| Registration |       $200 |
| Books        |       $250 |
| Activities   |       $100 |
| Technology   |       $150 |
| **Total**    | **$3,700** |

---

## 🧾 Invoices

Invoices contain:

* Invoice number
* Student
* Academic year
* Issue date
* Due date
* Invoice items
* Subtotal
* Discounts
* Scholarships
* Final amount
* Amount paid
* Outstanding amount
* Status
* Notes

Supported invoice statuses include:

* Draft
* Issued
* Partially Paid
* Paid
* Overdue
* Cancelled
* Refunded

Invoices can be generated individually or in bulk.

---

## 💵 Payments

The system supports:

* Cash
* Card
* Bank transfer
* Cheque
* Online payment
* Other

The school may configure USD and/or LBP as supported currencies according to its financial policy.

Every payment records:

* Payment number
* Student
* Amount
* Date
* Payment method
* Reference number
* Employee who received the payment
* Notes
* Status

Outstanding balances are updated after payments are recorded.

---

## 💳 Partial Payments

EduFinance supports partial payments.

For example:

**Invoice:** $3,000

**Payments:**

* $500
* $800

**Total Paid:** $1,300

**Remaining:** $1,700

The invoice is automatically marked as **Partially Paid** while maintaining each payment as a separate historical transaction.

---

## 🧾 Receipts

A successful payment generates a unique receipt.

A receipt may contain:

* School information
* Receipt number
* Payment date
* Student
* Student ID
* Related invoice(s)
* Amount paid
* Payment method
* Reference number
* Remaining balance
* Received by

Receipts can be:

* Viewed
* Printed
* Downloaded as PDF
* Emailed where email support is configured

---

## 📅 Installment Plans

The system supports dividing financial obligations into scheduled installments.

Each installment includes:

* Installment number
* Due date
* Original amount
* Amount paid
* Remaining amount
* Status

Installment statuses include:

* Upcoming
* Due
* Partially Paid
* Paid
* Overdue
* Cancelled

---

## 🎓 Scholarships & Discounts

### Discounts

Supported discount types may include:

* Sibling discount
* Early payment discount
* Employee child discount
* Promotional discount
* Special discount
* Other

Discounts can be configured as either:

* Fixed amounts
* Percentages

Sensitive discounts may require approval.

### Scholarships

Scholarships are managed separately from discounts and may include:

* Scholarship name
* Student
* Academic year
* Provider
* Fixed amount or percentage
* Start date
* End date
* Supporting documents
* Reason
* Status
* Approver

---

## 💸 Refunds

Refunds are processed without deleting the original payment.

Refund records include:

* Refund number
* Student
* Original payment
* Refund amount
* Refund reason
* Refund method
* Requested by
* Approved by
* Processed by
* Date
* Status

---

# 🏢 Expenses & Suppliers

EduFinance also manages school expenses and supplier-related financial operations.

### Expense Categories

Examples include:

* Electricity
* Internet
* Water
* Maintenance
* Equipment
* Stationery
* Transportation
* Cleaning
* Rent
* Marketing
* Training
* Salaries / employee-related expenses
* Other

### Supplier Management

Supplier records can contain:

* Supplier ID
* Supplier name
* Contact person
* Phone
* Email
* Address
* Tax information
* Current balance
* Notes
* Status

Supplier financial profiles can include:

* Bills
* Payments
* Expenses
* Documents
* Statements

---

# 📊 Dashboard & Analytics

The financial dashboard provides key financial indicators such as:

* Expected revenue
* Total collected
* Outstanding amount
* Overdue amount
* Current month revenue
* Current month expenses
* Net financial position
* Number of overdue students
* Active scholarships
* Pending approvals

Possible dashboard visualizations include:

* Revenue vs Expenses
* Collection Progress
* Payment Methods
* Outstanding Balances by Grade
* Monthly Collections
* Expense Distribution

The dashboard may also show:

* Recent payments
* Recent expenses
* Upcoming installments
* Overdue payments
* Pending approvals
* Important notifications

---

# 📈 Reporting

EduFinance provides financial reports including:

* Fee Collection Report
* Student Balance Report
* Payment Report
* Daily Collection Report
* Monthly Revenue Report
* Expense Report
* Revenue vs Expense Report
* Scholarship Report
* Discount Report
* Installment Report
* Overdue Payment Report
* Refund Report
* Supplier Balance Report
* Payment Method Report
* Financial Assistance Report

Reports can be filtered by:

* Date range
* Academic year
* Student
* Grade
* Class
* Fee category
* Payment method
* Status

Where applicable, reports support:

* PDF export
* Excel export
* Printing

---

# 🔔 Notifications

EduFinance includes an internal notification center.

Notifications may be generated for events such as:

* Payment overdue
* Installment due soon
* Scholarship awaiting approval
* Discount awaiting approval
* Refund awaiting approval
* Supplier bill due
* Payment received
* Financial assistance request received

Users can mark notifications as read.

---

# 🔐 Security & Authorization

Because EduFinance handles sensitive student and financial information, security is a major requirement.

The system uses:

* Django authentication
* Password hashing
* Role-based authorization
* Permission checks
* CSRF protection
* Input validation
* File validation
* Protected sessions
* Secure database credentials
* Audit logging

Users can only access information and actions allowed by their assigned permissions.

---

# 📝 Audit Logging

Important financial operations must remain traceable.

Audit records may contain:

* User
* Action
* Date/time
* Entity type
* Entity ID
* Previous values
* New values
* IP address where practical

Sensitive financial operations such as payments, refunds, discounts, scholarships, invoice cancellation, payment voiding, expenses, and approval decisions should be auditable.

Financial history should not normally be permanently deleted. Where appropriate, the system uses statuses such as:

* Cancelled
* Voided
* Reversed

This preserves the financial history of the school.

---

# 🔎 Search & Filtering

The application provides global search for:

* Students
* Student IDs
* Invoices
* Receipt numbers
* Payment numbers
* Suppliers

Search results respect the user's permissions.

Major financial lists also support filtering, sorting, and pagination.

---

# 📎 File Management

The system supports document attachments where appropriate, including:

* Supplier invoices
* Expense receipts
* Scholarship documentation
* Financial assistance documents
* Refund documentation

Uploaded files must be validated before acceptance.

---

# 📤 Data Export

Authorized users can export financial information.

### PDF

PDF export may be available for:

* Receipts
* Invoices
* Statements
* Selected reports

### Excel

Excel export may be available for:

* Financial reports
* Payment lists
* Outstanding balances
* Expenses
* Supplier information

---

# 🔄 Core Payment Workflow

One of the main workflows of EduFinance is receiving a student payment:

```text
Search Student
      ↓
Open Student Financial Profile
      ↓
View Balance / Outstanding Invoices / Installments
      ↓
Receive Payment
      ↓
Enter Amount / Payment Method / Reference / Date
      ↓
Confirm
      ↓
Create Payment
      ↓
Allocate Payment
      ↓
Update Invoice Balance
      ↓
Update Student Financial Balance
      ↓
Generate Receipt
      ↓
Create Audit Entry
      ↓
Update Reporting Figures
      ↓
Display Receipt
```

The workflow is designed to be fast and simple for accountants and cashiers.

---

# 🏗️ Technical Architecture

EduFinance is implemented as a full-stack Django web application.

```text
Browser
   ↓
Django Templates
   ↓
Django Views
   ↓
Business / Service Logic
   ↓
Django Models / MongoDB Data Layer
   ↓
MongoDB Atlas
```

The primary application does not depend on a separate SPA frontend.

---

# 🛠️ Technology Stack

### Backend

* Python
* Django
* Django Authentication
* Django Forms / ModelForms
* Django MongoDB Backend

### Frontend

* Django Templates
* HTML
* CSS
* Bootstrap
* Vanilla JavaScript

### Database

* MongoDB Atlas

### Additional Technologies

* Chart.js
* PDF generation libraries
* OpenPyXL

Django REST Framework may be explored separately where justified, but Django Templates remain the primary frontend architecture.

---

# 🗄️ Database

MongoDB Atlas is the primary application database.

The database architecture considers MongoDB's document-oriented structure and may use either:

* Embedded documents
* References between collections

depending on access patterns and business requirements.

Major data domains include:

```text
Identity
├── Users
├── Roles
└── Permissions

School
├── School Settings
├── Academic Years
├── Grades
└── Classes

Students
├── Students
├── Guardians
└── Enrollment Information

Fees
├── Fee Categories
├── Fee Structures
└── Fee Structure Items

Accounts Receivable
├── Student Invoices
├── Invoice Items
├── Payments
├── Payment Allocations
├── Receipts
├── Installment Plans
└── Installments

Financial Assistance
├── Discounts
├── Scholarships
└── Financial Assistance Requests

Refunds
└── Refund Transactions

Accounts Payable / Expenses
├── Suppliers
├── Supplier Bills
├── Supplier Payments
├── Expenses
└── Expense Categories

Employees
└── Employee Financial Information

System Operations
├── Notifications
├── Approval Requests
├── Documents
└── Audit Logs
```

Database credentials and connection strings should be stored using environment variables and must not be hardcoded in source code.

---

# 📋 Project Priorities

## MUST HAVE — Core Release

* Authentication
* Roles and permissions
* School settings
* Academic years
* Grades and classes
* Students
* Guardians
* Fee categories
* Fee structures
* Student invoices
* Full payments
* Partial payments
* Receipts
* Outstanding balances
* Installment plans
* Discounts
* Scholarships
* Expenses
* Suppliers
* Student statements
* Dashboard
* Basic reporting
* Audit records

## SHOULD HAVE — Professional Release

* Refund workflows
* Approval workflows
* Financial assistance
* Supplier bills
* Supplier payments
* Overdue categorization
* Notifications
* Payment reminders
* PDF export
* Excel export
* Advanced filtering
* Employee financial records
* Optional parent/student portal

## COULD HAVE — Advanced Release

* Multi-currency
* Email automation
* SMS integration
* WhatsApp integration
* Online payments
* Financial forecasting
* Bulk student import
* Advanced financial analytics
* Automated scheduled reminders
* Year-end financial closing

---

# 🚫 Out of Scope for Initial Release

The following features are not part of the initial release:

* Complete academic learning management
* Student grades and examination results
* Teacher lesson planning
* Full HR recruitment system
* Full payroll calculation engine
* Biometric attendance
* Library management
* Advanced transportation route management
* Online learning
* AI chatbot
* Native Android/iOS applications
* Government accounting integration
* Automatic bank reconciliation
* WhatsApp API integration
* SMS gateway integration

These features may be considered for future versions.

---

# 🎯 Project Success Criteria

The project is considered functionally successful when the core financial workflow can be completed:

```text
Academic Configuration
        ↓
Student Registration
        ↓
Fee Structure Assignment
        ↓
Invoice Generation
        ↓
Payment / Partial Payment
        ↓
Receipt Generation
        ↓
Balance Recalculation
        ↓
Installment / Overdue Tracking
        ↓
Student Account Statement
        ↓
Financial Dashboard & Reports
```

while supporting:

```text
Expenses
+
Suppliers
+
Scholarships
+
Discounts
+
Refunds
+
Auditability
```

through a secure Django Template-based application using MongoDB Atlas.

---

# 📌 Core Product Principle

> **A school accountant should be able to understand a student's complete financial situation in seconds and complete common financial operations with the minimum number of steps while maintaining accuracy, security, and full transaction history.**

This principle guides the database design, user interface, workflows, permissions, and reporting architecture.

---

# 🚀 Future Enhancements

Future versions may include:

* Online parent payments
* Stripe or other payment gateways
* Automated email reminders
* WhatsApp notifications
* SMS reminders
* Advanced financial forecasting
* AI-assisted financial analytics
* Budget planning
* Multiple school branches
* Multi-currency support
* Automatic bank reconciliation
* Parent mobile application
* Student mobile application
* Advanced payroll
* Accounting software integrations

---

# 📄 Project Documentation

The complete Business Requirements Document (BRD) defines the business objectives, scope, functional requirements, non-functional requirements, business rules, workflows, technical constraints, risks, priorities, and success criteria for EduFinance.

---

## 👩‍💻 Project Information

**Project:** EduFinance
**Project Number:** 10
**Type:** Full-Stack Django Web Application
**Context:** Lebanese School Financial Management
**Backend:** Django
**Frontend:** Django Templates
**Database:** MongoDB Atlas
**Status:** Planning / Development

---

## ⭐ Key Features at a Glance

| Feature            | Description                                 |
| ------------------ | ------------------------------------------- |
| 🔐 Authentication  | Secure login and role-based access          |
| 👥 User Management | Users, roles, and permissions               |
| 🎓 Students        | Student and guardian management             |
| 💰 Fees            | Configurable school fee structures          |
| 🧾 Invoices        | Individual and bulk invoice generation      |
| 💳 Payments        | Full and partial payment tracking           |
| 🧾 Receipts        | Automatic receipt generation                |
| 📅 Installments    | Scheduled installment management            |
| 🎓 Scholarships    | Scholarship management                      |
| 🏷️ Discounts      | Configurable discounts                      |
| 💸 Refunds         | Controlled refund workflow                  |
| 🏢 Expenses        | School expense management                   |
| 🤝 Suppliers       | Supplier and supplier payment tracking      |
| 📊 Dashboard       | Financial KPIs and analytics                |
| 📈 Reports         | Financial and collection reports            |
| 🔔 Notifications   | Internal financial notifications            |
| ✅ Approvals        | Approval workflows for sensitive operations |
| 📝 Audit Logs      | Financial activity traceability             |
| 📎 Documents       | Financial document attachments              |
| 📤 Exports         | PDF and Excel exports                       |
| 🔎 Search          | Global search and filtering                 |

---

## 🔒 Important Security Note

Do **not** commit sensitive information such as:

* MongoDB connection strings
* Database usernames/passwords
* Django `SECRET_KEY`
* API keys
* Email credentials
* Authentication tokens
* Production environment variables

Use environment variables and a `.env` file locally, and add `.env` to `.gitignore`.

---

## 📜 License

This project is developed as the **EduFinance School Financial Management System** project.

Done By: Hidaya Abou Al Oyoun Assud, Baker El Achkar, Youssef Al-Issa
