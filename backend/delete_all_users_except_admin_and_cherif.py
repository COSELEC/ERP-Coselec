import sys
import os
import argparse
from sqlalchemy import create_engine, text

def run_cleanup(db_url, commit=False):
    print("=" * 60)
    print("NETTOYAGE DES UTILISATEURS (SAUF ADMIN BOOTSTRAP & CHERIF SOW)")
    print(f"Cible : {db_url.split('@')[-1] if '@' in db_url else 'Base locale'}")
    print("=" * 60)

    try:
        engine = create_engine(db_url)
    except Exception as e:
        print(f"[ERREUR] Impossible de se connecter à la base de données : {e}")
        sys.exit(1)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Identifier les utilisateurs à préserver
            users = conn.execute(text("SELECT id, name, email FROM users ORDER BY id")).fetchall()
            
            preserved = []
            to_delete = []

            for u in users:
                uid, name, email = u[0], u[1] or "", (u[2] or "").strip().lower()
                # Admin bootstrap: adam@adam.com ou nom contenant Bootstrap
                # Cherif SOW: sinfo@coselec.sn
                if email == "sinfo@coselec.sn" or email == "adam@adam.com" or "bootstrap" in name.lower():
                    preserved.append(u)
                else:
                    to_delete.append(u)

            print(f"\nUtilisateurs conservés ({len(preserved)}):")
            for u in preserved:
                print(f"  [CONSERVÉ] ID {u[0]}: {u[1]} <{u[2]}>")

            print(f"\nUtilisateurs à supprimer ({len(to_delete)}):")
            for u in to_delete:
                print(f"  [SUPPRESSION] ID {u[0]}: {u[1]} <{u[2]}>")

            if not to_delete:
                print("\nAucun utilisateur à supprimer.")
                trans.rollback()
                return

            del_ids = tuple(u[0] for u in to_delete)
            admin_id = preserved[0][0] if preserved else 1

            print(f"\nID de l'admin de référence pour réassignation: {admin_id}")

            # 2. Nettoyer les dépendances étrangères
            print("\nNettoyage des références étrangères...")

            # Manager ID dans users
            res = conn.execute(text("UPDATE users SET manager_id = NULL WHERE manager_id IN :ids"), {"ids": del_ids})
            print(f"  - users.manager_id réinitialisés: {res.rowcount}")

            # Notifications
            res = conn.execute(text("DELETE FROM notifications WHERE user_id IN :ids"), {"ids": del_ids})
            print(f"  - notifications supprimées: {res.rowcount}")

            # Chatroom members
            res = conn.execute(text("DELETE FROM chatroom_members WHERE user_id IN :ids"), {"ids": del_ids})
            print(f"  - chatroom_members supprimés: {res.rowcount}")

            # Roles
            res = conn.execute(text("DELETE FROM user_roles WHERE user_id IN :ids"), {"ids": del_ids})
            print(f"  - user_roles supprimés: {res.rowcount}")

            # Attendances
            res = conn.execute(text("DELETE FROM attendances WHERE user_id IN :ids"), {"ids": del_ids})
            print(f"  - attendances supprimées: {res.rowcount}")

            # Audit logs (rendre orphelins ou réassigner)
            res1 = conn.execute(text("UPDATE audit_logs SET actor_id = NULL WHERE actor_id IN :ids"), {"ids": del_ids})
            res2 = conn.execute(text("UPDATE audit_logs SET target_user_id = NULL WHERE target_user_id IN :ids"), {"ids": del_ids})
            print(f"  - audit_logs mis à jour (actor: {res1.rowcount}, target: {res2.rowcount})")

            # Requests (réassigner à l'admin pour ne pas casser l'historique)
            res1 = conn.execute(text("UPDATE requests SET requester_id = :admin_id WHERE requester_id IN :ids"), {"admin_id": admin_id, "ids": del_ids})
            res2 = conn.execute(text("UPDATE requests SET validator_id = NULL WHERE validator_id IN :ids"), {"ids": del_ids})
            res3 = conn.execute(text("UPDATE requests SET manager_validator_id = NULL WHERE manager_validator_id IN :ids"), {"ids": del_ids})
            res4 = conn.execute(text("UPDATE requests SET finance_validator_id = NULL WHERE finance_validator_id IN :ids"), {"ids": del_ids})
            print(f"  - requests réassignées (requester: {res1.rowcount}, validator: {res2.rowcount})")

            # Request history
            res = conn.execute(text("UPDATE request_history SET changed_by_id = :admin_id WHERE changed_by_id IN :ids"), {"admin_id": admin_id, "ids": del_ids})
            print(f"  - request_history réassigné: {res.rowcount}")

            # Tasks
            res1 = conn.execute(text("UPDATE tasks SET author_id = :admin_id WHERE author_id IN :ids"), {"admin_id": admin_id, "ids": del_ids})
            res2 = conn.execute(text("UPDATE tasks SET assignee_id = NULL WHERE assignee_id IN :ids"), {"ids": del_ids})
            print(f"  - tasks mises à jour (author: {res1.rowcount}, assignee: {res2.rowcount})")

            # Autres tables potentielles (au cas où)
            for tbl, col, action in [
                ("contracts", "user_id", "DELETE"),
                ("employee_documents", "user_id", "DELETE"),
                ("org_assignments", "employee_id", "DELETE"),
                ("project_assignments", "user_id", "DELETE"),
                ("daily_reports", "user_id", "DELETE"),
                ("weekly_reports", "user_id", "DELETE"),
                ("caisse_vouchers", "demandeur_id", "UPDATE_ADMIN"),
                ("caisse_vouchers", "validator_cg_id", "UPDATE_NULL"),
                ("caisse_vouchers", "validator_dg_id", "UPDATE_NULL"),
                ("caisse_vouchers", "validator_dga_id", "UPDATE_NULL"),
                ("projects", "chef_projet_id", "UPDATE_NULL"),
                ("purchase_requests", "requester_id", "UPDATE_ADMIN"),
            ]:
                try:
                    if action == "DELETE":
                        cres = conn.execute(text(f"DELETE FROM {tbl} WHERE {col} IN :ids"), {"ids": del_ids})
                    elif action == "UPDATE_NULL":
                        cres = conn.execute(text(f"UPDATE {tbl} SET {col} = NULL WHERE {col} IN :ids"), {"ids": del_ids})
                    elif action == "UPDATE_ADMIN":
                        cres = conn.execute(text(f"UPDATE {tbl} SET {col} = :admin_id WHERE {col} IN :ids"), {"admin_id": admin_id, "ids": del_ids})
                    if cres.rowcount > 0:
                        print(f"  - {tbl}.{col} nettoyé ({action}): {cres.rowcount}")
                except Exception:
                    pass

            # 3. Suppression finale des utilisateurs
            del_res = conn.execute(text("DELETE FROM users WHERE id IN :ids"), {"ids": del_ids})
            print(f"\n=> {del_res.rowcount} utilisateurs supprimés de la table 'users'.")

            # 4. Vérification finale
            remaining = conn.execute(text("SELECT id, name, email FROM users ORDER BY id")).fetchall()
            print(f"\nUtilisateurs restants en base ({len(remaining)}):")
            for u in remaining:
                print(f"  - ID {u[0]}: {u[1]} <{u[2]}>")

            if commit:
                trans.commit()
                print("\n[SUCCÈS] Les modifications ont été appliquées avec succès en base de données.")
            else:
                trans.rollback()
                print("\n[SIMULATION] Rollback effectué. Aucune modification permanente appliquée.")

        except Exception as e:
            trans.rollback()
            print(f"\n[ERREUR] Une erreur est survenue, rollback effectué: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de nettoyage des utilisateurs (sauf Admin & Cherif)")
    parser.add_argument("--db-url", type=str, help="L'URL de connexion à la base de données PostgreSQL (ex: postgresql://user:pass@rds-host:5432/dbname)", required=False)
    parser.add_argument("--commit", action="store_true", help="Applique réellement les modifications en base")
    
    args = parser.parse_args()
    
    db_url = args.db_url or os.getenv("DATABASE_URL")
    
    if not db_url:
        print("[ERREUR] Aucune URL de base de données fournie.")
        print("Veuillez utiliser l'argument --db-url ou définir la variable d'environnement DATABASE_URL.")
        print("Exemple : python delete_users.py --db-url postgresql://user:pass@rds-host:5432/dbname")
        sys.exit(1)
        
    # Si on a pas SQLAlchemy d'installé sur l'EC2, on pourrait avoir besoin de psycopg2
    # Mais le projet semble utiliser SQLAlchemy, donc on s'assure juste d'avoir la bonne chaîne
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    run_cleanup(db_url=db_url, commit=args.commit)
