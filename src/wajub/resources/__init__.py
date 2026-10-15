"""API resource classes."""

from wajub.resources.accounts import AccountsResource
from wajub.resources.balance import BalanceResource
from wajub.resources.beneficiaries import BeneficiariesResource
from wajub.resources.crud import CrudResource
from wajub.resources.customers import CustomersResource
from wajub.resources.disputes import DisputesResource
from wajub.resources.events import EventsResource
from wajub.resources.global_resource import GlobalResource
from wajub.resources.identity import IdentityResource
from wajub.resources.invoices import InvoicesResource
from wajub.resources.links import LinksResource
from wajub.resources.listen import ListenResource
from wajub.resources.pagination import PagedResult, create_paged_list
from wajub.resources.payments import PaymentsResource
from wajub.resources.refunds import RefundsResource
from wajub.resources.shield import ShieldResource
from wajub.resources.tax import TaxResource
from wajub.resources.transfers import TransfersResource
from wajub.resources.webhook_endpoints import WebhookEndpointsResource

__all__ = [
    "AccountsResource",
    "BalanceResource",
    "BeneficiariesResource",
    "CrudResource",
    "CustomersResource",
    "DisputesResource",
    "EventsResource",
    "GlobalResource",
    "IdentityResource",
    "InvoicesResource",
    "LinksResource",
    "ListenResource",
    "PagedResult",
    "PaymentsResource",
    "RefundsResource",
    "ShieldResource",
    "TaxResource",
    "TransfersResource",
    "WebhookEndpointsResource",
    "create_paged_list",
]
