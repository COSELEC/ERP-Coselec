"""
Script de migration des départements - ERP COSELEC
=======================================================
Ce script :
  1. Déconnecte les utilisateurs et demandes des anciens départements (met department_id à NULL)
  2. Supprime tous les anciens départements
  3. Insère les nouveaux départements COSELEC

UTILISATION sur l'EC2 (depuis le dossier /home/ubuntu/ERP-Coselec/backend) :
  python migrate_departments.py

Prérequis : les variables d'environnement DATABASE_URL doivent être définies
  (soit via .env dans le dossier courant, soit exportées dans le shell)
"""

import os
import sys

# Charger le .env si présent dans le dossier courant
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))  # fallback racine
except ImportError:
    pass  # python-dotenv non installé, on continue avec les variables d'environnement système

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERREUR : La variable DATABASE_URL n'est pas définie.")
    print("   Assurez-vous que le fichier .env est présent ou exportez DATABASE_URL.")
    sys.exit(1)

# Nouveaux départements à créer
NOUVEAUX_DEPARTEMENTS = [
    {"name": "Direction Générale",          "code": "DIR-GEN"},
    {"name": "Direction Finance et Contrôle","code": "DIR-FIN"},
    {"name": "Pole Commercial",             "code": "POL-COM"},
    {"name": "Logistique/Appro",            "code": "LOG-APP"},
    {"name": "Direction Travaux",           "code": "DIR-TRV"},
    {"name": "Bureau d'Etudes",             "code": "BUR-ETU"},
]

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # ──────────────────────────────────────────────────
    # 1. Afficher les départements actuels
    # ──────────────────────────────────────────────────
    existing = conn.execute(text("SELECT id, name, code FROM departments ORDER BY id")).fetchall()
    print(f"\n{'='*55}")
    print(f"  Départements actuellement en base ({len(existing)} trouvés) :")
    print(f"{'='*55}")
    for row in existing:
        print(f"  [ID {row[0]:>3}] {row[1]:<30} ({row[2]})")

    if not existing:
        print("  (aucun département existant)")

    # ──────────────────────────────────────────────────
    # 2. Déconnecter les utilisateurs des anciens départements
    #    (department_id nullable=True → on met à NULL sans risque)
    # ──────────────────────────────────────────────────
    users_updated = conn.execute(
        text("UPDATE users SET department_id = NULL WHERE department_id IS NOT NULL")
    ).rowcount
    print(f"\n🔗 {users_updated} utilisateur(s) déconnecté(s) de leur ancien département.")

    # ──────────────────────────────────────────────────
    # 3. Déconnecter les demandes des anciens départements
    # ──────────────────────────────────────────────────
    requests_updated = conn.execute(
        text("UPDATE requests SET department_id = NULL WHERE department_id IS NOT NULL")
    ).rowcount
    print(f"🔗 {requests_updated} demande(s) déconnectée(s) de leur ancien département.")

    # ──────────────────────────────────────────────────
    # 4. Supprimer tous les anciens départements
    # ──────────────────────────────────────────────────
    deleted = conn.execute(text("DELETE FROM departments")).rowcount
    print(f"🗑️  {deleted} ancien(s) département(s) supprimé(s).")

    # ──────────────────────────────────────────────────
    # 5. Insérer les nouveaux départements
    # ──────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  Insertion des {len(NOUVEAUX_DEPARTEMENTS)} nouveaux départements :")
    print(f"{'='*55}")

    for dept in NOUVEAUX_DEPARTEMENTS:
        # Vérifier si un dept avec le même code existe déjà (sécurité idempotence)
        existing_check = conn.execute(
            text("SELECT id FROM departments WHERE code = :code"),
            {"code": dept["code"]}
        ).fetchone()

        if existing_check:
            print(f"  ⚠️  IGNORÉ (déjà présent) : {dept['name']} ({dept['code']})")
            continue

        conn.execute(
            text("INSERT INTO departments (name, code) VALUES (:name, :code)"),
            {"name": dept["name"], "code": dept["code"]}
        )
        print(f"  ✅ Ajouté : {dept['name']:<30} ({dept['code']})")

    # ──────────────────────────────────────────────────
    # 6. Vérification finale
    # ──────────────────────────────────────────────────
    final = conn.execute(text("SELECT id, name, code FROM departments ORDER BY id")).fetchall()
    print(f"\n{'='*55}")
    print(f"  ✅ Résultat final ({len(final)} départements en base) :")
    print(f"{'='*55}")
    for row in final:
        print(f"  [ID {row[0]:>3}] {row[1]:<30} ({row[2]})")

print(f"\n🎉 Migration terminée avec succès !\n")
