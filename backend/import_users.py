import sys
import os
import importlib

# S'assurer que le dossier backend est dans le sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Parcourir et importer tous les modèles SQLAlchemy pour initialiser les relations
app_dir = os.path.join(current_dir, "app")
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(".py") and not f.startswith("__"):
            rel = os.path.relpath(os.path.join(root, f), current_dir)
            mod_name = os.path.splitext(rel)[0].replace(os.sep, ".")
            if "model" in mod_name:
                try:
                    importlib.import_module(mod_name)
                except Exception:
                    pass

from sqlalchemy.orm import Session, configure_mappers
configure_mappers()

from app.core.database.session import SessionLocal
from app.modules.users.models.user import User
from app.modules.users.models.department import Department
from app.modules.users.models.role import Role
from app.core.security.auth import hash_password

# Données TSV brutes
TSV_DATA = r"""Prénom	Nom	Email	Matricule	Poste	Département	Statut

Seynabou	DIENG	seynabou.dieng@coselec.sn	17	Assistante Direction	Direction Générale	CDI

Mamadou	DIONGUE	mamadou.diongue@coselec.sn	30	Chef De Chantier	Technique & Travaux	CDI

El Hadji O.	SARR	el-hadji-o.sarr@coselec.sn	35	Technico-Commercial	Commercial	CDI

Edouard C.	DIAZ	edouard-c.diaz@coselec.sn	48	Responsable Pole Comercial	Commercial	CDI

Abdourahmane	MBENGUE	abdourahmane.mbengue@coselec.sn	96	Chef Atelier	Technique & Travaux	CDI

Souleymane	FATY	souleymane.faty@coselec.sn	112	Chef De Chantier	Technique & Travaux	CDI

Madiouf	DEMBELE	madiouf.dembele@coselec.sn	147	Electricien-Monteur	Technique & Travaux	CDI

Mbaye Seye	THIAM	mbaye-seye.thiam@coselec.sn	159	Tolier-Soudeur	Technique & Travaux	CDI

Sidy	DIEDHIOU	sidy.diedhiou@coselec.sn	226	Peintre	Technique & Travaux	CDI

Francois	MANCABOU	francois.mancabou@coselec.sn	229	Agent De Securite	Sécurité	CDI

Edouard	MALOU	edouard.malou@coselec.sn	230	Agent De Securite	Sécurité	CDI

Mouhamadou B.	FALL	mouhamadou-b.fall@coselec.sn	235	Chef De Chantier	Technique & Travaux	CDI

El H. Mamour	FALL	el-h-mamour.fall@coselec.sn	246	Chef De Chantier	Technique & Travaux	CDI

Charles Degaulle	KANOUTE	charles-degaulle.kanoute@coselec.sn	407	Chauffeur-Grutier	Technique & Travaux	CDI

Papa Moussa	DIEME	papa-moussa.dieme@coselec.sn	413	Electricien-Monteur	Technique & Travaux	CDI

Awa	BOYE	awa.boye@coselec.sn	417	Comptable	Finance & Comptabilité	CDI

Vieux	MANE	vieux.mane@coselec.sn	426	Chef De Chantier	Technique & Travaux	CDI

Mbaye	NDIAYE	mbaye.ndiaye@coselec.sn	434	Chef De Chantier	Technique & Travaux	CDI

Houdi	DIALLO	houdi.diallo@coselec.sn	435	Electricien-Monteur	Technique & Travaux	CDI

Momar Talla	GUEYE	momar-talla.gueye@coselec.sn	436	Electricien-Monteur	Technique & Travaux	CDI

Souleymane Solo	BADJI	souleymane-solo.badji@coselec.sn	438	Electricien-Monteur	Technique & Travaux	CDI

Amadou Dioulde	DIAMANKA	amadou-dioulde.diamanka@coselec.sn	442	Electricien-Monteur	Technique & Travaux	CDI

Mamady	DIEDHIOU	mamady.diedhiou@coselec.sn	443	Electricien-Monteur	Technique & Travaux	CDI

Souleymane	CISS	souleymane.ciss@coselec.sn	444	Electricien-Monteur	Technique & Travaux	CDI

Abdou Aziz	DIEME	abdou-aziz.dieme@coselec.sn	448	Technico-Commercial	Commercial	CDI

Mame Boucounta	SENE	mame-boucounta.sene@coselec.sn	450	Electricien Auto	Technique & Travaux	CDI

Mareme Soda	FALL	mareme-soda.fall@coselec.sn	457	Directrice Generale Adjointe	Direction Générale	CDI

Soce	FALL	soce.fall@coselec.sn	490	Agent De Securite	Sécurité	CDI

Abdoul Karim	SANE	abdoul-karim.sane@coselec.sn	504	Agent De Securite	Sécurité	CDI

Amadou	DIALLO	amadou.diallo@coselec.sn	595	Chauffeur-Grutier	Technique & Travaux	CDI

Alassane	MBAYE	alassane.mbaye@coselec.sn	596	Electricien-Monteur	Technique & Travaux	CDI

Adama	DIALLO	adama.diallo@coselec.sn	598	Electricien-Monteur	Technique & Travaux	CDI

Amath	DIOP	amath.diop@coselec.sn	600	Electricien-Monteur	Technique & Travaux	CDI

Lassana	DIATTA	lassana.diatta@coselec.sn	602	Electricien-Monteur	Technique & Travaux	CDI

Ousmane	BA	ousmane.ba@coselec.sn	606	Electricien-Monteur	Technique & Travaux	CDI

Cheikh	SARR	cheikh.sarr@coselec.sn	608	Electricien-Monteur	Technique & Travaux	CDI

Mame S Demba	NDIAYE	mame-s-demba.ndiaye@coselec.sn	611	Tolier-Soudeur	Technique & Travaux	CDI

Cheikh T Sy	SANKARE	cheikh-t-sy.sankare@coselec.sn	612	Electricien-Monteur	Technique & Travaux	CDI

Badara	THIAW	badara.thiaw@coselec.sn	613	Electricien-Monteur	Technique & Travaux	CDI

Malick	DIOP	malick.diop@coselec.sn	627	Electricien-Monteur	Technique & Travaux	CDI

Chams-Dine	YERIMA	chams-dine.yerima@coselec.sn	635	Chef De Service	Bureau d'Études	CDI

Mame Same Seni	NDOYE	mame-same-seni.ndoye@coselec.sn	649	Comptable	Finance & Comptabilité	CDI

Abdou	FALL	abdou.fall@coselec.sn	651	Reponsable Appro/Logistique	Logistique	CDI

Cheikh Tidiane	SECK	cheikh-tidiane.seck@coselec.sn	655	Technicien Be	Bureau d'Études	CDI

Eugene Dibocor	SARR	eugene-dibocor.sarr@coselec.sn	658	Agent De Securite	Sécurité	CDI

Ibrahima Diarra	NIANG	ibrahima-diarra.niang@coselec.sn	660	Electricien-Monteur	Technique & Travaux	CDI

Massamba	SOW	massamba.sow@coselec.sn	679	Technicien Be	Bureau d'Études	CDI

Idrissa	BA	idrissa.ba@coselec.sn	680	Directeur Travaux	Technique & Travaux	CDI

Cherif Deyibou	SOW	cherif-deyibou.sow@coselec.sn	681	Responsable It	Informatique	CDI

Amadou Sadio	BARRY	amadou-sadio.barry@coselec.sn	682	Chauffeur-Grutier	Technique & Travaux	CDI

Mamadou	TALL	mamadou.tall@coselec.sn	683	Technicien Be	Bureau d'Études	CDI

Ndeye Anta Mar	THIAM	ndeye-anta-mar.thiam@coselec.sn	684	Technicienne Be	Bureau d'Études	CDI

Elisabeth Cendrine	DIOUF	elisabeth-cendrine.diouf@coselec.sn	685	Assistante Qhse	QHSE	CDI

Louis Thomas	CISS	louis-thomas.ciss@coselec.sn	686	Assistant Qhse	QHSE	CDI

Gregoire Babou	NGOM	gregoire-babou.ngom@coselec.sn	688	Agent De Securite	Sécurité	CDI

Mamadou Come	MBENGUE	mamadou-come.mbengue@coselec.sn	689	Agent De Securite	Sécurité	CDI

Moussa	LY	moussa.ly@coselec.sn	690	Agent De Securite	Sécurité	CDI

Amadou Tidiane	BALDE	amadou-tidiane.balde@coselec.sn	691	Responsable Qhse	QHSE	CDI

Djibril	NDIAYE	djibril.ndiaye@coselec.sn	692	Agent De Securite	Sécurité	CDI

Mor	KASSE	mor.kasse@coselec.sn	029	Directeur General	Direction Générale	CDI

Moustapha	BA	moustapha.ba@coselec.sn	016	DFC	Finance & Comptabilité	CDI


a partir de ces infos je veux que tu me fournisses un script à donenr à mon instance ec2 pour qu'elle ajoute toutes ces personnes à ma base de données :p

<ADDITIONAL_METADATA>
The current local time is: 2026-09-09T14:19:01Z.

The user's current state is as follows:
Active Document: c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\services\session.ts (LANGUAGE_TYPESCRIPT)
Cursor is on line: 59
Other open documents:
- c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\services\session.ts (LANGUAGE_TYPESCRIPT)
- c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\components\users\UserList.vue (LANGUAGE_VUE)
- c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\components\Sidebar.vue (LANGUAGE_VUE)
- c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\router\index.ts (LANGUAGE_TYPESCRIPT)
- c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\components\requests\FuelRequestForm.vue (LANGUAGE_VUE)
</ADDITIONAL_METADATA>"""

def main():
    db: Session = SessionLocal()
    try:
        # Get or create the default role 'Employé'
        default_role = db.query(Role).filter(Role.name == "Employé").first()
        if not default_role:
            default_role = db.query(Role).first()
            if not default_role:
                default_role = Role(name="Employé", description="Rôle standard employé")
                db.add(default_role)
                db.commit()
                db.refresh(default_role)

        default_password = "TempPassword2025!"
        hashed_pw = hash_password(default_password)

        lines = [line.strip() for line in TSV_DATA.strip().split("\n") if line.strip()]
        if not lines:
            print("Aucune donnée trouvée.")
            return

        header = lines[0].split("\t")
        data_rows = lines[1:]

        added_count = 0
        skipped_count = 0

        for row in data_rows:
            fields = row.split("\t")
            if len(fields) < 3:
                continue

            first_name = fields[0].strip() if len(fields) > 0 else ""
            last_name = fields[1].strip() if len(fields) > 1 else ""
            email = fields[2].strip().lower() if len(fields) > 2 else ""
            matricule = fields[3].strip() if len(fields) > 3 and fields[3].strip() else None
            position = fields[4].strip() if len(fields) > 4 and fields[4].strip() else None
            department_name = fields[5].strip() if len(fields) > 5 and fields[5].strip() else None
            status = fields[6].strip() if len(fields) > 6 and fields[6].strip() else "CDI"

            full_name = f"{first_name} {last_name}".strip()

            if not email:
                continue

            # Vérifier si l'utilisateur existe déjà par email ou matricule
            existing_user = db.query(User).filter(
                (User.email == email) | ((User.matricule == matricule) if matricule else False)
            ).first()
            if existing_user:
                print(f"User {email} (matricule {matricule}) already exists, skipping.")
                skipped_count += 1
                continue

            # Trouver ou créer le département
            department = None
            if department_name:
                dept_code = department_name.upper()[:3].replace(" ", "")
                # Chercher par nom ou par code
                department = db.query(Department).filter(
                    (Department.name.ilike(department_name)) | (Department.code == dept_code)
                ).first()
                if not department:
                    # Garantir un code unique s'il y a collision
                    code_attempt = dept_code
                    counter = 1
                    while db.query(Department).filter(Department.code == code_attempt).first():
                        code_attempt = f"{dept_code[:2]}{counter}"
                        counter += 1
                    department = Department(name=department_name, code=code_attempt)
                    db.add(department)
                    db.commit()
                    db.refresh(department)

            # Créer l'utilisateur
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                name=full_name,
                email=email,
                matricule=matricule,
                position=position,
                status=status,
                hashed_password=hashed_pw,
                department_id=department.id if department else None,
                is_active=True,
                requires_password_change=True
            )

            # Associer le rôle
            new_user.roles.append(default_role)

            db.add(new_user)
            added_count += 1

        db.commit()
        print(f"\n--- Import Finished ---")
        print(f"Added {added_count} new users.")
        print(f"Skipped {skipped_count} existing users.")
        print(f"Default password set to: {default_password}")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting import...")
    main()
