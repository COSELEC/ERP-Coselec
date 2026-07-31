import sys
import os
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def seed_hierarchy():
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id, name FROM departments"))
        departments = [dict(id=row[0], name=row[1]) for row in res.fetchall()]
        
        res = conn.execute(text("SELECT id FROM employees ORDER BY id ASC"))
        employees = [row[0] for row in res.fetchall()]
        
        if not employees:
            print("Aucun employé trouvé. Exécutez d'abord seed.py")
            return
            
        print(f"Assignation de la hiérarchie pour {len(employees)} employés...")
        
        # 1. Le PDG (CEO)
        ceo_id = employees[0]
        ceo_dept = departments[0]['id'] if departments else None
        
        conn.execute(text("UPDATE employees SET manager_id = NULL, position = 'Directeur Général (CEO)', department_id = :dept WHERE id = :id"), {"dept": ceo_dept, "id": ceo_id})
        
        if len(employees) > 1:
            # 2. Les Directeurs de Départements
            num_directors = min(len(departments), len(employees) - 1)
            if num_directors == 0: num_directors = 3
                
            directors = employees[1:1+num_directors]
            
            for i, d_id in enumerate(directors):
                dept = departments[i] if i < len(departments) else None
                dept_id = dept['id'] if dept else None
                pos = f"Directeur {dept['name']}" if dept else "Directeur Adjoint"
                conn.execute(text("UPDATE employees SET manager_id = :mgr, position = :pos, department_id = :dept WHERE id = :id"), {"mgr": ceo_id, "pos": pos, "dept": dept_id, "id": d_id})

            # 3. Les autres employés rattachés aux directeurs
            managers = directors.copy()
            remaining = employees[1+num_directors:]
            
            team_leads = remaining[:max(1, len(remaining)//4)]
            for tl_id in team_leads:
                parent_id = random.choice(directors)
                parent_dept = conn.execute(text("SELECT department_id FROM employees WHERE id = :id"), {"id": parent_id}).scalar()
                
                conn.execute(text("UPDATE employees SET manager_id = :mgr, position = 'Chef d''équipe', department_id = :dept WHERE id = :id"), {"mgr": parent_id, "dept": parent_dept, "id": tl_id})
                managers.append(tl_id)
                
            workers = remaining[len(team_leads):]
            for worker_id in workers:
                parent_id = random.choice(managers)
                parent_dept = conn.execute(text("SELECT department_id FROM employees WHERE id = :id"), {"id": parent_id}).scalar()
                conn.execute(text("UPDATE employees SET manager_id = :mgr, department_id = :dept WHERE id = :id"), {"mgr": parent_id, "dept": parent_dept, "id": worker_id})
                
        print("Hiérarchie appliquée avec succès en SQL !")

if __name__ == "__main__":
    seed_hierarchy()
            

