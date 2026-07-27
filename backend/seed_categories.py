from app.core.database import SessionLocal
from app.models.norm import NormCategory

db = SessionLocal()
categories = ["Qualité", "Sécurité", "Environnement", "Informatique"]
for cat_name in categories:
    if not db.query(NormCategory).filter(NormCategory.name == cat_name).first():
        db.add(NormCategory(name=cat_name))
db.commit()
print("Categories seeded")
