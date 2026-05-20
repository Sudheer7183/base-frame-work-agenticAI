"""
Workers' Compensation Audit — RBAC Dependencies
================================================
Fixed to work with the platform's TokenData Pydantic model returned
by get_current_user, rather than expecting a raw dict.
"""

from dataclasses import dataclass, field
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
# TokenData is the Pydantic model get_current_user returns.
# Import it so we can read its fields as attributes (not .get()).
try:
    from app.core.security import TokenData
except ImportError:
    TokenData = None   # fallback — handled gracefully below


# ─────────────────────────────────────────────
# Role constants — must match Keycloak exactly
# ─────────────────────────────────────────────

WC_SUPER_ADMIN = "Wc_super_admin"
WC_ADMIN       = "wc_admin"
WC_PROVIDERS   = "wc_providers"
WC_AGENTS      = "wc_agents"

# Hierarchy — each key grants access to all roles in its value set
_ROLE_HIERARCHY = {
    # Only super_admin can satisfy a super_admin requirement
    WC_SUPER_ADMIN: {WC_SUPER_ADMIN},

    # admin or super_admin can satisfy an admin requirement
    WC_ADMIN:       {WC_SUPER_ADMIN, WC_ADMIN},

    # providers, admin, or super_admin can satisfy a providers requirement
    WC_PROVIDERS:   {WC_SUPER_ADMIN, WC_ADMIN, WC_PROVIDERS},

    # any role satisfies an agents requirement (lowest privilege gate)
    WC_AGENTS:      {WC_SUPER_ADMIN, WC_ADMIN, WC_PROVIDERS, WC_AGENTS},
}


# ─────────────────────────────────────────────
# WCUser — typed principal passed to endpoints
# ─────────────────────────────────────────────

@dataclass
class WCUser:
    user_id:   str
    username:  str
    email:     str
    full_name: str
    roles:     set = field(default_factory=set)

    @property
    def is_super_admin(self) -> bool:
        return WC_SUPER_ADMIN in self.roles

    @property
    def is_admin(self) -> bool:
        return WC_ADMIN in self.roles

    @property
    def is_provider(self) -> bool:
        return WC_PROVIDERS in self.roles

    @property
    def is_agent(self) -> bool:
        return WC_AGENTS in self.roles

    @property
    def display_name(self) -> str:
        return self.full_name or self.username or self.user_id


# ─────────────────────────────────────────────
# Core fix: handle TokenData model vs raw dict
# ─────────────────────────────────────────────

def _safe_get(token_obj, key: str, default=None):
    """
    Safely read a field from either a Pydantic TokenData model
    or a plain dict — whichever get_current_user happens to return.

    This is the root cause of the AttributeError:
        'TokenData' object has no attribute 'get'
    Pydantic models expose fields as attributes, not via .get().
    """
    if isinstance(token_obj, dict):
        return token_obj.get(key, default)
    # Pydantic model — use getattr
    return getattr(token_obj, key, default)


def _extract_realm_roles(token_obj) -> set:
    """
    Extract realm roles from either:
      - A raw Keycloak JWT dict:  token["realm_access"]["roles"]
      - A TokenData Pydantic model that may store roles directly
        as token_obj.roles, token_obj.realm_roles, or inside
        a nested realm_access attribute/dict field.
    """
    # ── Case 1: raw JWT dict (some configurations pass the full payload) ──
    if isinstance(token_obj, dict):
        realm_access = token_obj.get("realm_access", {})
        return set(realm_access.get("roles", []))

    # ── Case 2: TokenData Pydantic model ─────────────────────────────────
    # Try the most common field names the platform uses.
    # Check your app/core/security.py for the exact field name.

    # Option A: roles stored directly as a list on the model
    for attr in ("roles", "realm_roles", "user_roles"):
        val = getattr(token_obj, attr, None)
        if val is not None:
            return set(val) if not isinstance(val, set) else val

    # Option B: realm_access stored as a dict attribute
    realm_access = getattr(token_obj, "realm_access", None)
    if isinstance(realm_access, dict):
        return set(realm_access.get("roles", []))

    # Option C: fallback — model has no role field we recognise
    return set()


def _build_wc_user(token_obj) -> WCUser:
    """Build a WCUser from TokenData or a raw JWT dict."""
    roles = _extract_realm_roles(token_obj)
    return WCUser(
        user_id   = _safe_get(token_obj, "sub",                ""),
        username  = _safe_get(token_obj, "preferred_username", "")
                    or _safe_get(token_obj, "username", ""),
        email     = _safe_get(token_obj, "email",              ""),
        full_name = _safe_get(token_obj, "name",               "")
                    or _safe_get(token_obj, "full_name",        ""),
        roles     = roles,
    )


def _require_role(minimum_role: str):
    async def _dependency(token_obj=Depends(get_current_user)) -> WCUser:
        wc_user = _build_wc_user(token_obj)
        allowed = _ROLE_HIERARCHY.get(minimum_role, set())

        if not (wc_user.roles & allowed):
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail      = (
                    f"Insufficient permissions. "
                    f"Required: '{minimum_role}'. "
                    f"Your roles: {sorted(wc_user.roles) or ['none']}."
                ),
            )
        return wc_user

    return _dependency


# ── Public dependency functions ────────────────────────────────────────────────
require_wc_super_admin = _require_role(WC_SUPER_ADMIN)
require_wc_admin       = _require_role(WC_ADMIN)
require_wc_provider    = _require_role(WC_PROVIDERS)
require_wc_agent       = _require_role(WC_AGENTS)