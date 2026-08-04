from __future__ import annotations

import os
from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.modules.users.models.permission import Permission
from app.modules.users.models.role import Role
from app.modules.users.models.user import User


RBAC_PERMISSIONS: dict[str, tuple[str, str]] = {
    "employees.read": ("Employes - lecture", "Consulter les employes"),
    "employees.create": ("Employes - creation", "Creer des employes"),
    "employees.update": ("Employes - mise a jour", "Modifier des employes"),
    "employees.delete": ("Employes - suppression", "Supprimer des employes"),

    "notifications.read": ("Notifications - lecture", "Consulter ses notifications"),
    "notifications.update": ("Notifications - mise a jour", "Marquer les notifications"),
    "hr.read": ("Planning RH - lecture", "Consulter le planning RH"),
    "hr.update": ("Planning RH - mise a jour", "Modifier le planning RH"),
    "contracts.read": ("Contrats - lecture", "Consulter les contrats"),
    "contracts.create": ("Contrats - creation", "Creer des contrats"),
    "contracts.update": ("Contrats - mise a jour", "Modifier des contrats"),
    "contracts.delete": ("Contrats - suppression", "Supprimer des contrats"),
    "documents.read": ("Documents - lecture", "Consulter les documents RH"),
    "documents.create": ("Documents - creation", "Ajouter des documents RH"),
    "documents.delete": ("Documents - suppression", "Supprimer des documents RH"),
    "stock.read": ("Stock - lecture", "Consulter le stock"),
    "stock.create": ("Stock - creation", "Creer des donnees stock"),
    "stock.update": ("Stock - mise a jour", "Modifier des donnees stock"),
    "stock.delete": ("Stock - suppression", "Supprimer des donnees stock"),
    "dashboard.read": ("Dashboard - lecture", "Consulter les indicateurs"),
    "projects.read" : ("Projets - lecture", "Consulter les projets"),
    "projects.create" : ("Projets - creation", "Creer des projets"),
    "projects.update": ("Projets - mise a jour", "Modifier les projets"),
    "projects.delete" : ("Projets - suppression", "Supprimer les projets"),
    "tasks.create" : ("Tâches - creation", "Creer les taches"),
    "tasks.update" : ("Tâches - mise a jour", "Mettre a jour les taches"),
    "tasks.delete" : ("Tâches - suppression", "Supprimer les tâches"),
    "tasks.read" : ("Tâches - lecture", "Lire les tâches"),
    "fuel_requests.read": ("Fuel - lecture", "Consulter les requêtes de carburant"),
    "fuel_requests.create": ("Fuel - creation", "Créer des requêtes de carburant"),
    "fuel_requests.update": ("Fuel - mise a jour", "Modifier des requêtes de carburant"),
    "fuel_requests.delete": ("Fuel - suppression", "Supprimer des requêtes de carburant"),
    "fuel_requests.validate_finance": ("Fuel - valider finance", "Valider financièrement les requêtes de carburant"),
    "requests.validate_hr": ("Demandes - valider RH", "Valider les demandes RH unifiées"),
    "requests.validate_it": ("Demandes - valider IT", "Valider les demandes IT"),
    "requests.validate_facility": ("Demandes - valider Facility", "Valider les demandes Moyens Généraux"),
    "requests.validate_finance": ("Demandes - valider Finance", "Valider financièrement les demandes unifiées"),
}


RBAC_ROLES: dict[str, dict[str, Iterable[str]]] = {
    "Admin": {
        "description": "Acces total a la plateforme",
        "permissions": RBAC_PERMISSIONS.keys(),
    },
    "Employe": {
        "description": "Acces standard collaborateur",
        "permissions": {
            "fuel_requests.read",
            "fuel_requests.create",
            "notifications.read",
            "notifications.update",
            "stock.read",
        },
    },
    "RH": {
        "description": "Gestion RH et planning",
        "permissions": {
            "employees.read",
            "employees.create",
            "employees.update",
            "hr.read",
            "hr.update",
            "contracts.read",
            "contracts.create",
            "contracts.update",
            "documents.read",
            "documents.create",
            "documents.delete",
            "requests.validate_hr",
            "notifications.read",
            "notifications.update",
        },
    },
    "IT": {
        "description": "Support Informatique et Administration",
        "permissions": {
            "requests.validate_it",
            "notifications.read",
            "notifications.update",
        },
    },
    "Commercial": {
        "description": "Role commercial (base)",
        "permissions": {
            "notifications.read",
            "notifications.update",
        },
    },
    "Direction": {
        "description": "Vision consolidee et pilotage",
        "permissions": {
            "dashboard.read",
            "stock.read",
            "employees.read",
            "fuel_requests.read",
            "notifications.read",
        },
    },
    "Responsable Projet": {
        "description": "Suivi projet et demandes associees",
        "permissions": {
            "projects.read",
            "projects.create",
            "projects.update",
            "projects.delete",
            "tasks.read",
            "tasks.create",
            "tasks.update",
            "tasks.delete",
            "stock.read",
            "notifications.read",
            "notifications.update",
        },
    },
    "Stock / Logistique": {
        "description": "Operations de stock et logistique",
        "permissions": {
            "stock.read",
            "stock.create",
            "stock.update",
            "stock.delete",
            "fuel_requests.read",
            "fuel_requests.update",
            "dashboard.read",
            "notifications.read",
            "notifications.update",
        },
    },
    "Maintenance": {
        "description": "Maintenance et interventions",
        "permissions": {
            "stock.read",
            "requests.validate_facility",
            "notifications.read",
            "notifications.update",
        },
    },
    "Qualite": {
        "description": "Suivi qualite et conformite",
        "permissions": {
            "notifications.read",
            "notifications.update",
            "dashboard.read",
            "documents.read",
            "documents.create",
            "documents.update",
            "documents.delete",
        },
    },
    "Finance": {
        "description": "Suivi financier et budgetaire",
        "permissions": {
            "dashboard.read",
            "stock.read",
            "notifications.read",
            "fuel_requests.read",
            "fuel_requests.create",
            "fuel_requests.update",
            "fuel_requests.delete",
            "fuel_requests.validate_finance",
            "requests.validate_finance",
        },
    },
    "IT Admin": {
        "description": "Administration IT et support technique",
        "permissions": {
            "requests.validate_it",
            "stock.read",
            "stock.update",
            "notifications.read",
            "notifications.update",
        },
    },
    "Facility Manager": {
        "description": "Gestion Moyens Généraux et interventions",
        "permissions": {
            "requests.validate_facility",
            "stock.read",
            "stock.update",
            "fuel_requests.read",
            "fuel_requests.update",
            "notifications.read",
            "notifications.update",
            "dashboard.read",
        },
    },
    "Achat": {
        "description": "Gestion des achats et fournisseurs",
        "permissions": {
            "stock.read",
            "requests.validate_finance",
            "notifications.read",
            "notifications.update",
        },
    },
}


ADMIN_BOOTSTRAP_EMAIL = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "adam@adam.com").strip().lower()


def _get_or_create_permission(db: Session, code: str, name: str, description: str) -> Permission:
    permission = db.query(Permission).filter(Permission.code == code).first()

    if permission:
        changed = False
        if permission.name != name:
            permission.name = name
            changed = True
        if permission.description != description:
            permission.description = description
            changed = True
        if changed:
            db.add(permission)
        return permission

    permission = Permission(code=code, name=name, description=description)
    db.add(permission)
    return permission


def _get_or_create_role(db: Session, role_name: str, description: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()

    if role:
        if role.description != description:
            role.description = description
            db.add(role)
        return role

    role = Role(name=role_name, description=description)
    db.add(role)
    return role


def ensure_rbac_setup(db: Session) -> None:
    permission_map: dict[str, Permission] = {}

    for code, (name, description) in RBAC_PERMISSIONS.items():
        permission_map[code] = _get_or_create_permission(db, code, name, description)

    db.flush()

    for role_name, spec in RBAC_ROLES.items():
        role = _get_or_create_role(db, role_name, str(spec["description"]))
        desired_codes = set(spec["permissions"])

        role.permissions = [permission_map[code] for code in desired_codes if code in permission_map]
        db.add(role)

    db.commit()


def assign_role_to_user(db: Session, user: User, role_name: str) -> bool:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return False

    if any(existing_role.id == role.id for existing_role in user.roles):
        return True

    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return True


def assign_default_role(db: Session, user: User) -> None:
    assigned = assign_role_to_user(db, user, "Employe")
    if not assigned:
        ensure_rbac_setup(db)
        assign_role_to_user(db, user, "Employe")


ADMIN_BOOTSTRAP_PASSWORD = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "").strip()


def ensure_admin_role_for_email(db: Session, email: str | None = None) -> None:
    import logging
    import secrets

    logger = logging.getLogger(__name__)

    target_email = (email or ADMIN_BOOTSTRAP_EMAIL).strip().lower()
    if not target_email:
        return

    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        from app.core.security.auth import hash_password

        # Use env-provided password or generate a secure random one
        password = ADMIN_BOOTSTRAP_PASSWORD or secrets.token_urlsafe(16)
        if not ADMIN_BOOTSTRAP_PASSWORD:
            logger.warning(
                "ADMIN_BOOTSTRAP_PASSWORD not set. Generated temporary password "
                "for %s: %s  — change it immediately!", target_email, password,
            )

        user = User(
            name="Admin Bootstrap",
            email=target_email,
            hashed_password=hash_password(password),
            is_active=True,
            requires_password_change=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    ensure_rbac_setup(db)
    assign_role_to_user(db, user, "Admin")

