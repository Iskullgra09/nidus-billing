"""
Nidus Billing demo seed — multi-org sandbox for local / Docker.

Uses DATABASE_ADMIN_URL (bypasses RLS). Idempotent. Password: password123

  cd backend && uv run python seed.py
  docker compose exec api python seed.py
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.rls import clear_rls_context
from app.core.security import hash_password
from app.models import Member, Organization, User
from app.models.billing.customer import Customer
from app.models.billing.enums import InvoiceStatus, PaymentCondition, PaymentMethod
from app.models.billing.invoice import Invoice, InvoiceLine
from app.models.billing.item import Item
from app.models.billing.payment import InvoicePayment
from app.models.billing.supplier import Supplier
from app.models.identity.invitation import Invitation
from app.models.identity.role import Role
from app.models.identity.scopes import DEFAULT_ROLES_CONFIG, DefaultRole, NidusScope
from app.services.billing.invoice_service import InvoiceService

DEMO_PASSWORD = "password123"
HASHED_PASSWORD = hash_password(DEMO_PASSWORD)

ORGS: List[Dict[str, str]] = [
    {"name": "Acme Corp", "slug": "acme-corp"},
    {"name": "Nidus Labs", "slug": "nidus-labs"},
    {"name": "Beta Partners", "slug": "beta-partners"},
]

USERS: Dict[str, Dict[str, Any]] = {
    "owner@acme.dev": {"full_name": "Acme Owner"},
    "admin@acme.dev": {"full_name": "Acme Admin"},
    "member@acme.dev": {"full_name": "Acme Member"},
    "viewer@acme.dev": {"full_name": "Acme Viewer"},
    "billing@acme.dev": {"full_name": "Acme Billing Manager"},
    "owner@nidus.dev": {"full_name": "Nidus Owner"},
    "admin@nidus.dev": {"full_name": "Nidus Admin"},
    "member@nidus.dev": {"full_name": "Nidus Member"},
    "owner@beta.dev": {"full_name": "Beta Owner"},
    "viewer@beta.dev": {"full_name": "Beta Viewer"},
    "multi@nidus.dev": {"full_name": "Multi Org User"},
}

MEMBERSHIPS: List[tuple[str, str, str]] = [
    ("owner@acme.dev", "acme-corp", DefaultRole.OWNER),
    ("admin@acme.dev", "acme-corp", DefaultRole.ADMIN),
    ("member@acme.dev", "acme-corp", DefaultRole.MEMBER),
    ("viewer@acme.dev", "acme-corp", DefaultRole.VIEWER),
    ("multi@nidus.dev", "acme-corp", DefaultRole.OWNER),
    ("owner@nidus.dev", "nidus-labs", DefaultRole.OWNER),
    ("admin@nidus.dev", "nidus-labs", DefaultRole.ADMIN),
    ("member@nidus.dev", "nidus-labs", DefaultRole.MEMBER),
    ("multi@nidus.dev", "nidus-labs", DefaultRole.MEMBER),
    ("owner@beta.dev", "beta-partners", DefaultRole.OWNER),
    ("viewer@beta.dev", "beta-partners", DefaultRole.VIEWER),
]

PENDING_INVITES: List[tuple[str, str, str]] = [
    ("invitee@acme.dev", "acme-corp", DefaultRole.MEMBER),
    ("contractor@nidus.dev", "nidus-labs", DefaultRole.VIEWER),
    ("partner@beta.dev", "beta-partners", DefaultRole.ADMIN),
]

CUSTOM_ROLE = {
    "org_slug": "acme-corp",
    "name": "Billing Manager",
    "description": "Demo role focused on AR invoices and catalog (no members/roles).",
    "scopes": [
        NidusScope.ORG_READ.value,
        NidusScope.AUDIT_READ.value,
        NidusScope.CUSTOMER_READ.value,
        NidusScope.CUSTOMER_WRITE.value,
        NidusScope.SUPPLIER_READ.value,
        NidusScope.ITEM_READ.value,
        NidusScope.ITEM_WRITE.value,
        NidusScope.INVOICE_READ.value,
        NidusScope.INVOICE_WRITE.value,
    ],
}

ACME_CUSTOMERS: List[Dict[str, Any]] = [
    {
        "name": "Ferretería Central",
        "email": "compras@ferreteria.example",
        "phone": "+50622223333",
        "tax_id": "SEED-C-001",
    },
    {
        "name": "Café Aurora",
        "email": "admin@cafeaurora.example",
        "phone": "+50688881111",
        "tax_id": "SEED-C-002",
    },
    {
        "name": "Clínica Norte",
        "email": "facturacion@clinicanorte.example",
        "tax_id": "SEED-C-003",
    },
]

ACME_SUPPLIERS: List[Dict[str, Any]] = [
    {
        "name": "Distribuidora Pacífico",
        "email": "ventas@pacifico.example",
        "tax_id": "SEED-S-001",
    },
    {
        "name": "Tech Import CR",
        "email": "orders@techimport.example",
        "tax_id": "SEED-S-002",
    },
]

ACME_ITEMS: List[Dict[str, Any]] = [
    {
        "sku": "SRV-CONSULT",
        "name": "Consulting hour",
        "unit": "hour",
        "unit_price": Decimal("75000.0000"),
        "tax_rate": Decimal("13"),
        "is_service": True,
    },
    {
        "sku": "SRV-SUPPORT",
        "name": "Support retainer",
        "unit": "month",
        "unit_price": Decimal("250000.0000"),
        "tax_rate": Decimal("13"),
        "is_service": True,
    },
    {
        "sku": "PRD-WIDGET",
        "name": "Widget Pro",
        "unit": "unit",
        "unit_price": Decimal("45000.0000"),
        "tax_rate": Decimal("13"),
        "is_service": False,
    },
    {
        "sku": "PRD-CABLE",
        "name": "USB-C cable",
        "unit": "unit",
        "unit_price": Decimal("8500.0000"),
        "tax_rate": Decimal("13"),
        "is_service": False,
    },
]

NIDUS_ITEMS: List[Dict[str, Any]] = [
    {
        "sku": "LAB-HOURS",
        "name": "Lab engineering hour",
        "unit": "hour",
        "unit_price": Decimal("90000.0000"),
        "tax_rate": Decimal("13"),
        "is_service": True,
    },
]


def _admin_session_maker() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(str(settings.DATABASE_ADMIN_URL), pool_pre_ping=True)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _get_or_create_org(session: AsyncSession, name: str, slug: str) -> Organization:
    OrgModel = cast(Any, Organization)
    existing = (
        await session.execute(select(Organization).where(OrgModel.slug == slug, OrgModel.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if existing:
        return existing

    org = Organization(name=name, slug=slug, is_active=True)
    session.add(org)
    await session.flush()
    return org


async def _ensure_default_roles(session: AsyncSession, org_id: UUID) -> Dict[str, Role]:
    RoleModel = cast(Any, Role)
    roles: Dict[str, Role] = {}

    for role_name, config in DEFAULT_ROLES_CONFIG.items():
        found = (
            await session.execute(
                select(Role).where(
                    RoleModel.organization_id == org_id,
                    RoleModel.name == role_name.value,
                    RoleModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

        if found:
            found.scopes = list(config["scopes"])
            found.description = config["description"]
            roles[role_name.value] = found
            continue

        role = Role(
            name=role_name.value,
            description=config["description"],
            scopes=list(config["scopes"]),
            organization_id=org_id,
        )
        session.add(role)
        await session.flush()
        roles[role_name.value] = role

    return roles


async def _get_or_create_user(session: AsyncSession, email: str, full_name: str) -> User:
    UserModel = cast(Any, User)
    existing = (
        await session.execute(select(User).where(UserModel.email == email, UserModel.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if existing:
        existing.full_name = full_name
        existing.hashed_password = HASHED_PASSWORD
        existing.is_active = True
        return existing

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=HASHED_PASSWORD,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    return user


async def _ensure_membership(
    session: AsyncSession,
    *,
    user_id: UUID,
    org_id: UUID,
    role_id: UUID,
) -> None:
    MemberModel = cast(Any, Member)
    existing = (
        await session.execute(
            select(Member).where(
                MemberModel.user_id == user_id,
                MemberModel.organization_id == org_id,
                MemberModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.role_id = role_id
        return

    session.add(Member(user_id=user_id, organization_id=org_id, role_id=role_id))


async def _ensure_custom_role(session: AsyncSession, org_id: UUID) -> Role:
    RoleModel = cast(Any, Role)
    name = CUSTOM_ROLE["name"]
    found = (
        await session.execute(
            select(Role).where(
                RoleModel.organization_id == org_id,
                RoleModel.name == name,
                RoleModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if found:
        found.description = CUSTOM_ROLE["description"]
        found.scopes = list(CUSTOM_ROLE["scopes"])
        return found

    role = Role(
        name=name,
        description=CUSTOM_ROLE["description"],
        scopes=list(CUSTOM_ROLE["scopes"]),
        organization_id=org_id,
    )
    session.add(role)
    await session.flush()
    return role


async def _ensure_pending_invite(
    session: AsyncSession,
    *,
    email: str,
    org_id: UUID,
    role_id: UUID,
) -> None:
    InvitationModel = cast(Any, Invitation)
    existing = (
        await session.execute(
            select(Invitation).where(
                InvitationModel.email == email,
                InvitationModel.organization_id == org_id,
                InvitationModel.is_accepted.is_(False),
                InvitationModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.role_id = role_id
        existing.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        return

    session.add(
        Invitation(
            email=email,
            organization_id=org_id,
            role_id=role_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            is_accepted=False,
        )
    )


async def _get_or_create_customer(session: AsyncSession, org_id: UUID, data: Dict[str, Any]) -> Customer:
    CustomerModel = cast(Any, Customer)
    existing = (
        await session.execute(
            select(Customer).where(
                CustomerModel.organization_id == org_id,
                CustomerModel.tax_id == data["tax_id"],
                CustomerModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.name = data["name"]
        existing.email = data.get("email")
        existing.phone = data.get("phone")
        existing.is_active = True
        return existing

    customer = Customer(
        organization_id=org_id,
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
        tax_id=data["tax_id"],
        is_active=True,
    )
    session.add(customer)
    await session.flush()
    return customer


async def _get_or_create_supplier(session: AsyncSession, org_id: UUID, data: Dict[str, Any]) -> Supplier:
    SupplierModel = cast(Any, Supplier)
    existing = (
        await session.execute(
            select(Supplier).where(
                SupplierModel.organization_id == org_id,
                SupplierModel.tax_id == data["tax_id"],
                SupplierModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.name = data["name"]
        existing.email = data.get("email")
        existing.is_active = True
        return existing

    supplier = Supplier(
        organization_id=org_id,
        name=data["name"],
        email=data.get("email"),
        tax_id=data["tax_id"],
        is_active=True,
    )
    session.add(supplier)
    await session.flush()
    return supplier


async def _get_or_create_item(session: AsyncSession, org_id: UUID, data: Dict[str, Any]) -> Item:
    ItemModel = cast(Any, Item)
    existing = (
        await session.execute(
            select(Item).where(
                ItemModel.organization_id == org_id,
                ItemModel.sku == data["sku"],
                ItemModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.name = data["name"]
        existing.unit = data["unit"]
        existing.unit_price = data["unit_price"]
        existing.tax_rate = data.get("tax_rate")
        existing.is_service = data.get("is_service", False)
        existing.is_active = True
        return existing

    item = Item(
        organization_id=org_id,
        sku=data["sku"],
        name=data["name"],
        unit=data["unit"],
        unit_price=data["unit_price"],
        tax_rate=data.get("tax_rate"),
        is_service=data.get("is_service", False),
        is_active=True,
    )
    session.add(item)
    await session.flush()
    return item


async def _find_invoice_by_reference(
    session: AsyncSession,
    org_id: UUID,
    reference_number: str,
) -> Optional[Invoice]:
    InvoiceModel = cast(Any, Invoice)
    return (
        await session.execute(
            select(Invoice).where(
                InvoiceModel.organization_id == org_id,
                InvoiceModel.reference_number == reference_number,
                InvoiceModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()


async def _ensure_invoice(
    session: AsyncSession,
    *,
    org_id: UUID,
    customer_id: UUID,
    reference_number: str,
    payment_condition: str,
    status: str,
    lines: List[Dict[str, Any]],
    notes: Optional[str] = None,
    due_date: Optional[date] = None,
    issue: bool = False,
    payments: Optional[List[Dict[str, Any]]] = None,
    void: bool = False,
) -> Invoice:
    existing = await _find_invoice_by_reference(session, org_id, reference_number)
    if existing:
        return existing

    invoice = Invoice(
        organization_id=org_id,
        customer_id=customer_id,
        payment_condition=payment_condition,
        status=InvoiceStatus.DRAFT.value,
        currency="CRC",
        reference_number=reference_number,
        notes=notes,
        due_date=due_date,
    )
    session.add(invoice)
    await session.flush()

    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for index, raw in enumerate(lines, start=1):
        quantity = Decimal(str(raw["quantity"]))
        unit_price = Decimal(str(raw["unit_price"]))
        tax_rate = Decimal(str(raw["tax_rate"])) if raw.get("tax_rate") is not None else None
        line_sub, line_tax, line_total = InvoiceService._line_amounts(quantity, unit_price, tax_rate)
        item: Optional[Item] = raw.get("item")
        session.add(
            InvoiceLine(
                organization_id=org_id,
                invoice_id=invoice.id,
                line_number=index,
                item_id=item.id if item else None,
                description=raw["description"],
                sku=item.sku if item else raw.get("sku"),
                unit=raw.get("unit") or (item.unit if item else "unit"),
                quantity=quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                line_subtotal=line_sub,
                line_tax=line_tax,
                line_total=line_total,
            )
        )
        subtotal += line_sub
        tax_total += line_tax

    invoice.subtotal = InvoiceService._money(subtotal)
    invoice.tax_total = InvoiceService._money(tax_total)
    invoice.total = InvoiceService._money(subtotal + tax_total)
    invoice.amount_paid = Decimal("0")
    invoice.balance_due = invoice.total

    if issue or void:
        invoice.document_number = await InvoiceService._allocate_document_number(session, org_id)
        invoice.issued_at = datetime.now(timezone.utc)
        invoice.status = InvoiceStatus.ISSUED.value

    for payment in payments or []:
        amount = InvoiceService._money(Decimal(str(payment["amount"])))
        session.add(
            InvoicePayment(
                organization_id=org_id,
                invoice_id=invoice.id,
                amount=amount,
                paid_at=payment.get("paid_at") or datetime.now(timezone.utc),
                method=payment.get("method", PaymentMethod.TRANSFER.value),
                notes=payment.get("notes"),
            )
        )
        invoice.amount_paid = InvoiceService._money(invoice.amount_paid + amount)

    if payments:
        InvoiceService._refresh_payment_status(invoice)

    if void:
        invoice.status = InvoiceStatus.VOID.value
        invoice.amount_paid = Decimal("0")
        invoice.balance_due = Decimal("0")

    # Keep draft totals when not issued
    if status == InvoiceStatus.DRAFT.value and not issue and not void:
        invoice.status = InvoiceStatus.DRAFT.value

    await session.flush()
    return invoice


async def _seed_billing_demo(session: AsyncSession, orgs: Dict[str, Organization]) -> None:
    acme_id = orgs["acme-corp"].id
    nidus_id = orgs["nidus-labs"].id

    customers = {
        spec["tax_id"]: await _get_or_create_customer(session, acme_id, spec) for spec in ACME_CUSTOMERS
    }
    for spec in ACME_SUPPLIERS:
        await _get_or_create_supplier(session, acme_id, spec)
    items = {spec["sku"]: await _get_or_create_item(session, acme_id, spec) for spec in ACME_ITEMS}

    for spec in NIDUS_ITEMS:
        await _get_or_create_item(session, nidus_id, spec)
    await _get_or_create_customer(
        session,
        nidus_id,
        {
            "name": "Nidus Client Demo",
            "email": "client@niduslabs.example",
            "tax_id": "SEED-N-001",
        },
    )

    widget = items["PRD-WIDGET"]
    consult = items["SRV-CONSULT"]
    support = items["SRV-SUPPORT"]
    cable = items["PRD-CABLE"]
    ferreteria = customers["SEED-C-001"]
    cafe = customers["SEED-C-002"]
    clinica = customers["SEED-C-003"]

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=ferreteria.id,
        reference_number="SEED-DRAFT-001",
        payment_condition=PaymentCondition.CONTADO.value,
        status=InvoiceStatus.DRAFT.value,
        notes="Demo draft — edit / issue / delete in UI",
        lines=[
            {
                "item": widget,
                "description": widget.name,
                "quantity": 2,
                "unit_price": widget.unit_price,
                "tax_rate": widget.tax_rate,
            },
            {
                "item": cable,
                "description": cable.name,
                "quantity": 5,
                "unit_price": cable.unit_price,
                "tax_rate": cable.tax_rate,
            },
        ],
    )

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=cafe.id,
        reference_number="SEED-ISSUED-001",
        payment_condition=PaymentCondition.CONTADO.value,
        status=InvoiceStatus.ISSUED.value,
        notes="Demo issued unpaid — register a payment",
        issue=True,
        lines=[
            {
                "item": support,
                "description": support.name,
                "quantity": 1,
                "unit_price": support.unit_price,
                "tax_rate": support.tax_rate,
            }
        ],
    )

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=clinica.id,
        reference_number="SEED-PARTIAL-001",
        payment_condition=PaymentCondition.CREDITO.value,
        status=InvoiceStatus.PARTIAL.value,
        notes="Demo partial — balance still due",
        due_date=date.today() + timedelta(days=15),
        issue=True,
        lines=[
            {
                "item": consult,
                "description": consult.name,
                "quantity": 10,
                "unit_price": consult.unit_price,
                "tax_rate": consult.tax_rate,
            }
        ],
        payments=[{"amount": Decimal("200000.0000"), "method": PaymentMethod.TRANSFER.value}],
    )

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=ferreteria.id,
        reference_number="SEED-PAID-001",
        payment_condition=PaymentCondition.CONTADO.value,
        status=InvoiceStatus.PAID.value,
        notes="Demo paid — PDF download",
        issue=True,
        lines=[
            {
                "item": cable,
                "description": cable.name,
                "quantity": 4,
                "unit_price": cable.unit_price,
                "tax_rate": cable.tax_rate,
            }
        ],
        payments=[{"amount": Decimal("38420.0000"), "method": PaymentMethod.CASH.value}],
    )

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=cafe.id,
        reference_number="SEED-OVERDUE-001",
        payment_condition=PaymentCondition.CREDITO.value,
        status=InvoiceStatus.ISSUED.value,
        notes="Demo overdue credit invoice",
        due_date=date.today() - timedelta(days=10),
        issue=True,
        lines=[
            {
                "item": widget,
                "description": widget.name,
                "quantity": 1,
                "unit_price": widget.unit_price,
                "tax_rate": widget.tax_rate,
            }
        ],
    )

    await _ensure_invoice(
        session,
        org_id=acme_id,
        customer_id=clinica.id,
        reference_number="SEED-VOID-001",
        payment_condition=PaymentCondition.CONTADO.value,
        status=InvoiceStatus.VOID.value,
        notes="Demo voided invoice",
        issue=True,
        void=True,
        lines=[
            {
                "description": "Cancelled one-off service",
                "quantity": 1,
                "unit_price": Decimal("10000.0000"),
                "tax_rate": Decimal("13"),
                "unit": "unit",
            }
        ],
    )


def _print_summary() -> None:
    print("")
    print("=" * 72)
    print("Nidus Billing demo seed ready")
    print(f"Password for all accounts: {DEMO_PASSWORD}")
    print("=" * 72)
    print("")
    print(f"{'Email':<28} {'Orgs / roles':<40}")
    print("-" * 72)
    by_email: Dict[str, List[str]] = {}
    for email, org_slug, role_name in MEMBERSHIPS:
        by_email.setdefault(email, []).append(f"{org_slug}:{role_name}")
    by_email.setdefault("billing@acme.dev", []).append("acme-corp:Billing Manager")
    for email in sorted(by_email):
        print(f"{email:<28} {', '.join(by_email[email])}")
    print("")
    print("Pending invitations:")
    for email, org_slug, role_name in PENDING_INVITES:
        print(f"  - {email} -> {org_slug} as {role_name}")
    print("")
    print("Acme billing demo (reference_number):")
    print("  SEED-DRAFT-001     draft to edit/issue/delete")
    print("  SEED-ISSUED-001    issued unpaid (pay)")
    print("  SEED-PARTIAL-001   partial payment")
    print("  SEED-PAID-001      paid + PDF")
    print("  SEED-OVERDUE-001   credit overdue")
    print("  SEED-VOID-001      void")
    print("")
    print("Suggested logins:")
    print("  owner@acme.dev     full Owner + audit on Acme")
    print("  billing@acme.dev   Billing Manager (invoices/catalog, no members)")
    print("  multi@nidus.dev    org picker (Acme Owner + Nidus Member)")
    print("  viewer@acme.dev    limited scopes (no members/roles/audit)")
    print("  admin@nidus.dev    Admin with audit:read on Nidus Labs")
    print("=" * 72)


async def seed_data() -> None:
    session_maker = _admin_session_maker()
    async with session_maker() as session:
        await clear_rls_context(session)

        orgs: Dict[str, Organization] = {}
        roles_by_org: Dict[str, Dict[str, Role]] = {}

        for spec in ORGS:
            org = await _get_or_create_org(session, spec["name"], spec["slug"])
            orgs[spec["slug"]] = org
            roles_by_org[spec["slug"]] = await _ensure_default_roles(session, org.id)

        billing_role = await _ensure_custom_role(session, orgs[CUSTOM_ROLE["org_slug"]].id)

        users: Dict[str, User] = {}
        for email, meta in USERS.items():
            users[email] = await _get_or_create_user(session, email, meta["full_name"])

        for email, org_slug, role_name in MEMBERSHIPS:
            await _ensure_membership(
                session,
                user_id=users[email].id,
                org_id=orgs[org_slug].id,
                role_id=roles_by_org[org_slug][role_name].id,
            )

        await _ensure_membership(
            session,
            user_id=users["billing@acme.dev"].id,
            org_id=orgs["acme-corp"].id,
            role_id=billing_role.id,
        )

        for email, org_slug, role_name in PENDING_INVITES:
            await _ensure_pending_invite(
                session,
                email=email,
                org_id=orgs[org_slug].id,
                role_id=roles_by_org[org_slug][role_name].id,
            )

        await _seed_billing_demo(session, orgs)
        await session.commit()

    _print_summary()


if __name__ == "__main__":
    asyncio.run(seed_data())
