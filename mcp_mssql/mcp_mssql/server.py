from __future__ import annotations

import datetime
from typing import Annotated, Any, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_mssql.config import get_connection_string, get_mcp_host, get_mcp_port
from mcp_mssql.sql_runner import SqlRunner


class Proc:
    QRY_INTEREST_METHODS = "dbo.QryInterestMethods"
    QRY_CUSTOMERS = "dbo.QryCustomers"
    QRY_CUSTOMER_WITH_LOANS = "dbo.QryCustomerWithLoans"
    QRY_LOAN_APPLICATIONS = "dbo.QryLoanApplications"
    QRY_LOANS = "dbo.QryLoans"
    QRY_LOAN_OVERVIEW = "dbo.QryLoanOverview"
    QRY_PAYMENT_SCHEDULE_BY_LOAN = "dbo.QryPaymentScheduleByLoan"
    QRY_PAYMENTS_BY_LOAN = "dbo.QryPaymentsByLoan"
    QRY_PAYMENTS_BY_DATE = "dbo.QryPaymentsByDate"
    QRY_UPCOMING_DUE = "dbo.QryUpcomingDue"
    QRY_DELINQUENCY_AGING = "dbo.QryDelinquencyAging"
    QRY_PRODUCT_PORTFOLIO_SUMMARY = "dbo.QryProductPortfolioSummary"
    QRY_COLLECTOR_QUEUE = "dbo.QryCollectorQueue"
    QRY_PREPAYMENT_HISTORY = "dbo.QryPrepaymentHistory"
    QRY_LOAN_BALANCE_ASOF = "dbo.QryLoanBalanceAsOf"


mcp = FastMCP("mssql-loan-query", host=get_mcp_host(), port=get_mcp_port())
db = SqlRunner(get_connection_string())


@mcp.tool()
def qry_interest_methods(
    interest_method_id: Annotated[
        Optional[int],
        Field(description="รหัสวิธีคิดดอกเบี้ย (optional). ตัวอย่าง: 1; ไม่ระบุ = คืนทั้งหมด"),
    ] = None,
) -> Any:
    """ดึงรายการวิธีคิดดอกเบี้ยทั้งหมด หรือระบุเพื่อดูรายละเอียดเฉพาะรายการ.

    Result: list ของ row [interest_method_id, name, description, formula_reference]
      - interest_method_id (int): รหัสวิธีคิดดอกเบี้ย
      - name (string): ชื่อวิธีคิดดอกเบี้ย
      - description (string): รายละเอียดวิธีคิดดอกเบี้ย
      - formula_reference (string): อ้างอิงสูตรหรือ logic ที่ใช้คำนวณ
    """
    return db.run_procedure(Proc.QRY_INTEREST_METHODS, {"interest_method_id": interest_method_id})


@mcp.tool()
def qry_customers(
    keyword: Annotated[
        Optional[str],
        Field(description='คำค้นบางส่วน (LIKE) สำหรับ name/citizen_id/phone/email. ตัวอย่าง: "som"'),
    ] = "",
    page: Annotated[int, Field(description="เลขหน้าแบบ 1-based (>=1). ตัวอย่าง: 1")] = 1,
    pageSize: Annotated[int, Field(description="ขนาดหน้า (จำนวนเรคอร์ดต่อหน้า). ค่าเริ่มต้น 20")] = 20,
) -> Any:
    """ค้นหาลูกค้าตามคีย์เวิร์ด (name/citizen_id/phone/email) พร้อมแบ่งหน้า.

    Result: list ของ row แบบแบ่งหน้า
      [customer_id, name, citizen_id, phone, email, address, total_count, page, page_size]
        - customer_id (int): รหัสลูกค้า
        - name (string): ชื่อลูกค้า
        - citizen_id (string): เลขบัตรประชาชน
        - phone (string): เบอร์โทร
        - email (string): อีเมลติดต่อ
        - address (string): ที่อยู่ลูกค้า
        - total_count (int): จำนวนเรคอร์ดทั้งหมดก่อนแบ่งหน้า
        - page (int): หน้าปัจจุบัน
        - page_size (int): จำนวนเรคอร์ดต่อหน้า
    """
    return db.run_procedure(
        Proc.QRY_CUSTOMERS,
        {"keyword": keyword or "", "page": page, "pagesize": pageSize},
    )


@mcp.tool()
def qry_customer_with_loans(
    customer_id: Annotated[int, Field(description="รหัสลูกค้า (required). ตัวอย่าง: 1")],
) -> Any:
    """ดึงข้อมูลลูกค้าหนึ่งคนพร้อมรายการสินเชื่อทั้งหมดที่เกี่ยวข้อง (2 result sets: Customer, Loans).

    Result:
      ResultSet[0] = ข้อมูลลูกค้า 1 row [customer_id, name, citizen_id, phone, email, address]
        - customer_id (int): รหัสลูกค้า
        - name (string): ชื่อลูกค้า
        - citizen_id (string): เลขบัตรประชาชน
        - phone (string): เบอร์โทร
        - email (string): อีเมลติดต่อ
        - address (string): ที่อยู่ลูกค้า

      ResultSet[1] = รายการสินเชื่อของลูกค้ารายนั้น (0..N rows)
        [loan_id, loan_no, status, principal_amount, term_months, start_date, end_date,
         product_code, product_id, product_name_th, product_name_en]
        - loan_id (int): รหัสสินเชื่อ
        - loan_no (string): เลขที่สัญญา/เลขที่สินเชื่อ (เช่น LO20250215-0005)
        - status (string): สถานะสินเชื่อ (เช่น ACTIVE, CLOSED)
        - principal_amount (decimal): วงเงิน/เงินต้นของสินเชื่อ
        - term_months (int): ระยะเวลาผ่อน (หน่วยเป็นเดือน)
        - start_date (date): วันที่เริ่มสัญญา
        - end_date (date): วันที่สิ้นสุดสัญญา
        - product_code (string): รหัสหรือโค้ดประเภทสินเชื่อ (เช่น DIM)
        - product_id (int): รหัสประเภท/ผลิตภัณฑ์สินเชื่อ
        - product_name_th (string): ชื่อสินเชื่อภาษาไทย (เช่น สินเชื่อมอเตอร์ไซค์)
        - product_name_en (string): ชื่อสินเชื่อภาษาอังกฤษ (เช่น Motorcycle)
    """
    return db.run_procedure(Proc.QRY_CUSTOMER_WITH_LOANS, {"customer_id": customer_id})


@mcp.tool()
def qry_loan_applications(
    status: Annotated[
        Optional[str], Field(description="ตัวกรองสถานะ เช่น Approved/Pending; ไม่ระบุ = ทั้งหมด")
    ] = None,
    date_from: Annotated[
        Optional[datetime.date], Field(description="จาก application_date (yyyy-MM-dd), optional")
    ] = None,
    date_to: Annotated[
        Optional[datetime.date], Field(description="ถึง application_date (yyyy-MM-dd), optional")
    ] = None,
) -> Any:
    """รายการคำขอสินเชื่อ โดยกรองตามสถานะและช่วงวันที่ยื่นคำขอ.

    Result: list ของ row
      [application_id, application_date, status, requested_amount, approved_amount,
       approved_date, customer_id, customer_name, loan_product_id, product_name, sub_type]
        - application_id (int): รหัสคำขอสินเชื่อ
        - application_date (date): วันที่ยื่นคำขอสินเชื่อ
        - status (string): สถานะคำขอ (เช่น Approved, Pending, Rejected)
        - requested_amount (decimal): วงเงินที่ลูกค้าขอ
        - approved_amount (decimal): วงเงินที่อนุมัติจริง
        - approved_date (date?): วันที่อนุมัติ (อาจเป็น null ถ้ายังไม่อนุมัติ)
        - customer_id (int): รหัสลูกค้า
        - customer_name (string): ชื่อลูกค้า
        - loan_product_id (int): รหัสผลิตภัณฑ์สินเชื่อที่ขอ
        - product_name (string): ชื่อผลิตภัณฑ์สินเชื่อ (เช่น สินเชื่อมอเตอร์ไซค์)
        - sub_type (string): ประเภท/กลุ่มย่อยของสินเชื่อ (เช่น Motorcycle)
    """
    return db.run_procedure(
        Proc.QRY_LOAN_APPLICATIONS,
        {"status": status, "date_from": date_from, "date_to": date_to},
    )


@mcp.tool()
def qry_loans(
    status: Annotated[
        Optional[str], Field(description="สถานะสัญญา เช่น ACTIVE/Closed; ไม่ระบุ = ทั้งหมด")
    ] = None,
    product_id: Annotated[
        Optional[int], Field(description="รหัสผลิตภัณฑ์สินเชื่อ; ไม่ระบุ = ทุกผลิตภัณฑ์")
    ] = None,
    start_from: Annotated[
        Optional[datetime.date], Field(description="เริ่มช่วง start_date (yyyy-MM-dd), optional")
    ] = None,
    start_to: Annotated[
        Optional[datetime.date], Field(description="สิ้นสุดช่วง start_date (yyyy-MM-dd), optional")
    ] = None,
) -> Any:
    """ค้นหาสัญญาเงินกู้ตามสถานะ/ผลิตภัณฑ์/ช่วงวันเริ่มสัญญา.

    Result: list ของสัญญาเงินกู้
      [loan_id, contract_number, status, loan_amount, loan_term, start_date, end_date,
       customer_id, customer_name, loan_product_id, product_name, sub_type, interest_method]
        - loan_id (int): รหัสสินเชื่อ
        - contract_number (string): เลขที่สัญญา เช่น LO20250208-0004
        - status (string): สถานะสัญญา เช่น ACTIVE, Closed
        - loan_amount (decimal): วงเงินกู้ / เงินต้น
        - loan_term (int): ระยะเวลาผ่อน (เดือน)
        - start_date (date): วันที่เริ่มสัญญา
        - end_date (date): วันที่สิ้นสุดสัญญา
        - customer_id (int): รหัสลูกค้า
        - customer_name (string): ชื่อลูกค้า
        - loan_product_id (int): รหัสผลิตภัณฑ์สินเชื่อ
        - product_name (string): ชื่อผลิตภัณฑ์สินเชื่อ เช่น สินเชื่อรถยนต์
        - sub_type (string): กลุ่มย่อย เช่น Car
        - interest_method (string): วิธีคิดดอกเบี้ย เช่น FLAT 15%
    """
    return db.run_procedure(
        Proc.QRY_LOANS,
        {
            "status": status,
            "product_id": product_id,
            "start_from": start_from,
            "start_to": start_to,
        },
    )


@mcp.tool()
def qry_loan_overview(
    loan_id: Annotated[int, Field(description="รหัสสัญญาเงินกู้ (required). ตัวอย่าง: 1")],
) -> Any:
    """ภาพรวมสัญญาเงินกู้รายสัญญา — ยอดตั้งชำระ (scheduled) เทียบกับยอดที่จ่ายและยอดคงเหลือโดยประมาณ.

    Result: 1 row
      [loan_id, interest_method_id, contract_number, loan_amount, loan_term,
       start_date, end_date, status,
       total_principal_scheduled, total_interest_scheduled, total_scheduled,
       total_principal_paid, total_interest_paid, total_penalty_paid,
       total_amount_paid, total_sched_outstanding, principal_balance_estimate]
        - loan_id (int): รหัสสัญญาเงินกู้
        - interest_method_id (int): รหัสวิธีคิดดอกเบี้ยของสัญญา
        - contract_number (string): เลขที่สัญญา เช่น LO20250105-0002
        - loan_amount (decimal): วงเงินกู้/เงินต้นตั้งต้น
        - loan_term (int): จำนวนงวด (เดือน)
        - start_date (date): วันเริ่มสัญญา
        - end_date (date): วันสิ้นสุดสัญญา
        - status (string): สถานะ เช่น ACTIVE, Closed
        - total_principal_scheduled (decimal): ยอดตั้งชำระเงินต้นรวม
        - total_interest_scheduled (decimal): ยอดตั้งชำระดอกเบี้ยรวม
        - total_scheduled (decimal): ยอดตั้งชำระรวมทั้งหมด (principal + interest)
        - total_principal_paid (decimal): เงินต้นที่จ่ายแล้วรวม
        - total_interest_paid (decimal): ดอกเบี้ยที่จ่ายแล้วรวม
        - total_penalty_paid (decimal): ค่าปรับที่จ่ายแล้วรวม
        - total_amount_paid (decimal): ยอดรวมที่จ่ายทั้งหมด
        - total_sched_outstanding (decimal): ยอดตั้งชำระที่ยังไม่ชำระ
        - principal_balance_estimate (decimal): เงินต้นคงเหลือโดยประมาณ (estimate)
    """
    return db.run_procedure(Proc.QRY_LOAN_OVERVIEW, {"loan_id": loan_id})


@mcp.tool()
def qry_payment_schedule_by_loan(
    loan_id: Annotated[int, Field(description="รหัสสัญญาเงินกู้ (required). ตัวอย่าง: 1")],
) -> Any:
    """แสดงตารางงวดชำระของสัญญา พร้อมจำนวนวันค้างชำระ (days late) และ aging bucket ต่อรายการ.

    Result: list ของงวดชำระ
      [schedule_id, loan_id, due_date, principal_due, interest_due, total_due, status,
       principal_paid, interest_paid, penalty_paid, amount_paid,
       outstanding_pi, days_late, aging_bucket, last_payment_date]
        - schedule_id (int): รหัสงวดชำระ
        - loan_id (int): รหัสสัญญาเงินกู้
        - due_date (date): กำหนดชำระของงวด
        - principal_due (decimal): เงินต้นที่ต้องชำระงวดนี้
        - interest_due (decimal): ดอกเบี้ยที่ต้องชำระงวดนี้
        - total_due (decimal): ยอดรวมที่ต้องชำระ (principal + interest)
        - status (string): สถานะของงวด เช่น Paid, Pending, Overdue
        - principal_paid (decimal): เงินต้นที่จ่ายแล้วของงวดนี้
        - interest_paid (decimal): ดอกเบี้ยที่จ่ายแล้วของงวดนี้
        - penalty_paid (decimal): ค่าปรับที่จ่ายแล้วของงวดนี้
        - amount_paid (decimal): รวมยอดที่จ่ายแล้วทั้งหมด
        - outstanding_pi (decimal): เงินต้น + ดอกเบี้ยที่ยังค้างอยู่ของงวดนี้
        - days_late (int): จำนวนวันค้างชำระ (0 = ไม่ค้าง)
        - aging_bucket (string): กลุ่มอายุหนี้ เช่น Current, 1-30, 31-60, 60+
        - last_payment_date (date?): วันที่มีการจ่ายล่าสุดของงวด (null = ยังไม่เคยจ่าย)
    """
    return db.run_procedure(Proc.QRY_PAYMENT_SCHEDULE_BY_LOAN, {"loan_id": loan_id})


@mcp.tool()
def qry_payments_by_loan(
    loan_id: Annotated[int, Field(description="รหัสสัญญาเงินกู้ (required). ตัวอย่าง: 1")],
) -> Any:
    """แสดงประวัติการชำระเงินทั้งหมดของสัญญาพร้อมข้อมูลงวดที่เกี่ยวข้อง.

    Result: list ของรายการชำระเงิน
      [payment_id, schedule_id, payment_date, amount_paid,
       principal_paid, interest_paid, penalty_paid,
       payment_method_id, payment_method,
       due_date, total_due, status]
        - payment_id (int): รหัสรายการชำระเงิน
        - schedule_id (int): รหัสงวดที่รายการนี้ผูกกับ
        - payment_date (date): วันที่ชำระ
        - amount_paid (decimal): ยอดรวมที่ชำระ
        - principal_paid (decimal): เงินต้นที่ชำระ
        - interest_paid (decimal): ดอกเบี้ยที่ชำระ
        - penalty_paid (decimal): ค่าปรับที่ชำระ
        - payment_method_id (int): รหัสช่องทางชำระ
        - payment_method (string): ชื่อช่องทาง เช่น TRANSFER
        - due_date (date): กำหนดชำระของงวดที่เกี่ยวข้อง
        - total_due (decimal): ยอดต้องชำระของงวด
        - status (string): สถานะการชำระของงวด (เช่น Paid, Pending)
    """
    return db.run_procedure(Proc.QRY_PAYMENTS_BY_LOAN, {"loan_id": loan_id})


@mcp.tool()
def qry_payments_by_date(
    date_from: Annotated[
        datetime.date, Field(description="จาก payment_date (yyyy-MM-dd), inclusive (required)")
    ],
    date_to: Annotated[
        datetime.date, Field(description="ถึง payment_date (yyyy-MM-dd), inclusive (required)")
    ],
    payment_method_id: Annotated[
        Optional[int],
        Field(description="รหัสวิธีชำระเงิน (optional). ตัวอย่าง: 2=TRANSFER; ไม่ระบุ=ทุกวิธี"),
    ] = None,
) -> Any:
    """รายงานการชำระเงินในช่วงวันที่ที่กำหนด และสามารถกรองตามวิธีชำระเงินได้.

    Result: list ของประวัติชำระเงินในช่วงวันที่
      [payment_id, schedule_id, payment_date, amount_paid,
       principal_paid, interest_paid, penalty_paid,
       payment_method_id, payment_method,
       loan_id, due_date, total_due, contract_number,
       customer_id, customer_name]
        - payment_id (int): รหัสรายการชำระเงิน
        - schedule_id (int): รหัสงวดที่รายการนี้ผูก (nullable ได้)
        - payment_date (date): วันที่ชำระเงิน
        - amount_paid (decimal): ยอดรวมที่ชำระ
        - principal_paid (decimal): เงินต้นที่ชำระในรายการ
        - interest_paid (decimal): ดอกเบี้ยที่ชำระ
        - penalty_paid (decimal): ค่าปรับที่ชำระ
        - payment_method_id (int): ช่องทางการชำระ (1:CASH, 2:TRANSFER, 3:CARD)
        - payment_method (string): ชื่อช่องทาง เช่น Cash, Transfer, Card
        - loan_id (int): รหัสสัญญาเงินกู้
        - due_date (date): กำหนดชำระของงวดที่เกี่ยวข้อง
        - total_due (decimal): ยอดต้องชำระของงวดนั้น (principal + interest)
        - contract_number (string): เลขที่สัญญาเงินกู้
        - customer_id (int): รหัสลูกค้า
        - customer_name (string): ชื่อลูกค้า
    """
    return db.run_procedure(
        Proc.QRY_PAYMENTS_BY_DATE,
        {"date_from": date_from, "date_to": date_to, "payment_method_id": payment_method_id},
    )


@mcp.tool()
def qry_upcoming_due(
    days_ahead: Annotated[
        int, Field(description="จำนวนวันข้างหน้า (default 7). ตัวอย่าง: 7/30/60")
    ] = 7,
) -> Any:
    """แสดงงวดที่กำลังจะถึงกำหนดชำระภายใน N วันข้างหน้า พร้อมยอดค้าง PI ต่อรายการ.

    Result: list ของงวดที่ใกล้ถึงกำหนด
      [schedule_id, loan_id, due_date, total_due,
       outstanding_pi, contract_number,
       customer_id, customer_name]
        - schedule_id (int): รหัสงวดชำระ
        - loan_id (int): รหัสสัญญาเงินกู้
        - due_date (date): วันที่งวดจะถึงกำหนดชำระ
        - total_due (decimal): ยอดที่ต้องชำระตามงวด (PI ทั้งหมด)
        - outstanding_pi (decimal): ยอดค้างชำระ (principal + interest) ณ ปัจจุบัน
        - contract_number (string): เลขที่สัญญา เช่น LO20250110-0001
        - customer_id (int): รหัสลูกค้า
        - customer_name (string): ชื่อลูกค้า
    """
    return db.run_procedure(Proc.QRY_UPCOMING_DUE, {"days_ahead": days_ahead})


@mcp.tool()
def qry_delinquency_aging() -> Any:
    """สรุปสถานะค้างชำระทั้งพอร์ต แบ่งตาม aging bucket (Current/1-30/31-60/61-90/90+).

    Params: (none) — คืนจำนวนงวดและยอดคงค้างรวมต่อ bucket.

    Result: list ของ bucket summary
      [aging_bucket, schedule_count, total_outstanding_pi]
        - aging_bucket (string): กลุ่มอายุหนี้ เช่น Current, 1-30, 31-60, 61-90, 90+
        - schedule_count (int): จำนวนงวดใน bucket นั้น
        - total_outstanding_pi (decimal): ยอดค้างชำระรวม (principal + interest) ใน bucket นั้น
    """
    return db.run_procedure(Proc.QRY_DELINQUENCY_AGING, None)


@mcp.tool()
def qry_product_portfolio_summary() -> Any:
    """สรุปพอร์ตตามผลิตภัณฑ์ (จำนวนสัญญา, ยอดปล่อยรวม, ยอด PI คงค้างประมาณการ).

    Params: (none). ใช้งานเพื่อดูภาพรวมแยกตาม product.

    Result: list ของข้อมูลสรุปพอร์ตตามผลิตภัณฑ์
      [loan_product_id, product_name, sub_type,
       loans_count, total_disbursed, total_pi_outstanding]
        - loan_product_id (int): รหัสผลิตภัณฑ์สินเชื่อ
        - product_name (string): ชื่อผลิตภัณฑ์สินเชื่อ (เช่น สินเชื่อมอเตอร์ไซค์)
        - sub_type (string): กลุ่มย่อยของผลิตภัณฑ์ (เช่น Motorcycle)
        - loans_count (int): จำนวนสัญญาที่อยู่ในผลิตภัณฑ์นี้
        - total_disbursed (decimal): ยอดปล่อยสินเชื่อรวม
        - total_pi_outstanding (decimal): ยอดคงค้าง PI โดยประมาณ (principal + interest)
    """
    return db.run_procedure(Proc.QRY_PRODUCT_PORTFOLIO_SUMMARY, None)


@mcp.tool()
def qry_collector_queue(
    min_days_late: Annotated[
        int, Field(description="วันค้างชำระขั้นต่ำ (default 1). ตัวอย่าง: 1/7/30/60")
    ] = 1,
) -> Any:
    """จัดคิวติดตามหนี้ โดยเลือกเฉพาะงวดที่ค้างชำระอย่างน้อย X วันขึ้นไป.

    Result: list ของงวดที่เข้าเกณฑ์ติดตามหนี้
      [schedule_id, loan_id, due_date, total_due,
       outstanding_pi, days_late,
       contract_number, customer_id, customer_name, phone]
        - schedule_id (int): รหัสงวดชำระ
        - loan_id (int): รหัสสัญญาเงินกู้
        - due_date (date): วันกำหนดชำระของงวด
        - total_due (decimal): ยอดต้องชำระตามงวด (PI รวม)
        - outstanding_pi (decimal): ยอดค้างชำระ (principal + interest)
        - days_late (int): จำนวนวันค้าง (>= min_days_late)
        - contract_number (string): เลขที่สัญญา เช่น LO20250105-0002
        - customer_id (int): รหัสลูกค้า
        - customer_name (string): ชื่อลูกค้า
        - phone (string): เบอร์โทรลูกค้า
    """
    return db.run_procedure(Proc.QRY_COLLECTOR_QUEUE, {"min_days_late": min_days_late})


@mcp.tool()
def qry_prepayment_history(
    loan_id: Annotated[
        Optional[int], Field(description="รหัสสัญญา (optional). ไม่ระบุ = ทั้งหมด")
    ] = None,
) -> Any:
    """แสดงรายการงวดที่มีการจ่ายเกินยอดกำหนด (amount_paid > total_due).

    Result: list ของงวดที่มีการจ่ายเกิน
      [schedule_id, loan_id, due_date, total_due,
       amount_paid, principal_paid, interest_paid, penalty_paid,
       last_payment_date, overpay_amount]
        - schedule_id (int): รหัสงวด
        - loan_id (int): รหัสสัญญาเงินกู้
        - due_date (date): กำหนดชำระของงวด
        - total_due (decimal): ยอดที่ต้องชำระตามกำหนด
        - amount_paid (decimal): ยอดที่จ่ายจริง (มากกว่า total_due)
        - principal_paid (decimal): เงินต้นที่ชำระ
        - interest_paid (decimal): ดอกเบี้ยที่ชำระ
        - penalty_paid (decimal): ค่าปรับที่จ่าย
        - last_payment_date (date): วันที่มีการชำระครั้งล่าสุดของงวดนี้
        - overpay_amount (decimal): ยอดที่จ่ายเกิน (amount_paid - total_due)
    """
    return db.run_procedure(Proc.QRY_PREPAYMENT_HISTORY, {"loan_id": loan_id})


@mcp.tool()
def qry_loan_balance_asof(
    loan_id: Annotated[int, Field(description="รหัสสัญญา (required). ตัวอย่าง: 1")],
    as_of: Annotated[
        datetime.date,
        Field(description="วันที่อ้างอิงรูปแบบ yyyy-MM-dd (required). ตัวอย่าง: 2025-06-30"),
    ],
) -> Any:
    """ภาพรวมยอดคงเหลือเงินต้นของสัญญา ณ วันที่กำหนด (as-of) พร้อมสเตตัสสัญญาถึงวันดังกล่าว.

    Result: 1 row
      [loan_id, contract_number, loan_amount,
       principal_paid_asof, principal_balance_asof,
       start_date, end_date, status, as_of_date]
        - loan_id (int): รหัสสัญญาเงินกู้
        - contract_number (string): เลขที่สัญญา เช่น LO20250105-0002
        - loan_amount (decimal): วงเงินกู้ตั้งต้น
        - principal_paid_asof (decimal): เงินต้นที่จ่ายสะสมจนถึงวันที่ as-of
        - principal_balance_asof (decimal): เงินต้นคงเหลือตามการคำนวณ ณ as-of
        - start_date (date): วันที่เริ่มสัญญา
        - end_date (date): วันที่สิ้นสุดสัญญาตามแผน
        - status (string): สถานะสัญญา ณ ปัจจุบัน เช่น ACTIVE, Closed
        - as_of_date (date?): วันที่อ้างอิงที่ใช้คำนวณ (โดยทั่วไปตรงกับพารามิเตอร์ as_of; อาจเป็น null ในบางกรณี)
    """
    return db.run_procedure(Proc.QRY_LOAN_BALANCE_ASOF, {"loan_id": loan_id, "as_of": as_of})


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
