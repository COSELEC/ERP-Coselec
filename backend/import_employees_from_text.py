import sys
import os
import argparse
import unicodedata

# RAW DATA EXTRACTED FROM THE IMAGE
RAW_DATA = """
001 SEYNABOU DIENG 017 ASSISTANTE DIRECTION
002 MAMADOU DIONGUE 030 CHEF DE CHANTIER
003 EL HADJI O. SARR 035 TECHNICO-COMMERCIAL
004 EDOUARD C. DIAZ 048 RESPONSABLE POLE COMERCIAL
005 ABDOURAHMANE MBENGUE 096 CHEF ATELIER
006 SOULEYMANE FATY 112 CHEF DE CHANTIER
007 MADIOUF DEMBELE 147 ELECTRICIEN-MONTEUR
008 MBAYE SEYE THIAM 159 TOLIER-SOUDEUR
009 SIDY DIEDHIOU 226 PEINTRE
010 FRANCOIS MANCABOU 229 AGENT DE SECURITE
011 EDOUARD MALOU 230 AGENT DE SECURITE
012 MOUHAMADOU B.FALL 235 CHEF DE CHANTIER
013 EL H. MAMOUR FALL 246 CHEF DE CHANTIER
014 CHARLES DEGAULLE KANOUTE 407 CHAUFFEUR-GRUTIER
015 PAPA MOUSSA DIEME 413 ELECTRICIEN-MONTEUR
016 AWA BOYE 417 COMPTABLE
017 VIEUX MANE 426 CHEF DE CHANTIER
018 MBAYE NDIAYE 434 CHEF DE CHANTIER
019 HOUDI DIALLO 435 ELECTRICIEN-MONTEUR
020 MOMAR TALLA GUEYE 436 ELECTRICIEN-MONTEUR
021 SOULEYMANE SOLO BADJI 438 ELECTRICIEN-MONTEUR
022 AMADOU DIOULDE DIAMANKA 442 ELECTRICIEN-MONTEUR
023 MAMADY DIEDHIOU 443 ELECTRICIEN-MONTEUR
024 SOULEYMANE CISS 444 ELECTRICIEN-MONTEUR
025 ABDOU AZIZ DIEME 448 TECHNICO-COMMERCIAL
026 MAME BOUCOUNTA SENE 450 ELECTRICIEN AUTO
027 MAREME SODA FALL 457 DIRECTRICE GENERALE ADJOINTE
028 SOCE FALL 490 AGENT DE SECURITE
029 ABDOUL KARIM SANE 504 AGENT DE SECURITE
030 AMADOU DIALLO 595 CHAUFFEUR-GRUTIER
031 ALASSANE MBAYE 596 ELECTRICIEN-MONTEUR
032 ADAMA DIALLO 598 ELECTRICIEN-MONTEUR
033 AMATH DIOP 600 ELECTRICIEN-MONTEUR
034 LASSANA DIATTA 602 ELECTRICIEN-MONTEUR
035 OUSMANE BA 606 ELECTRICIEN-MONTEUR
036 CHEIKH SARR 608 ELECTRICIEN-MONTEUR
037 MAME S DEMBA NDIAYE 611 TOLIER-SOUDEUR
038 CHEIKH T SY SANKARE 612 ELECTRICIEN-MONTEUR
039 BADARA THIAW 613 ELECTRICIEN-MONTEUR
040 MALICK DIOP 627 ELECTRICIEN-MONTEUR
041 CHAMS-DINE YERIMA 635 CHEF DE SERVICE
042 MAME SAME SENI NDOYE 649 COMPTABLE
043 ABDOU FALL 651 REPONSABLE APPRO/LOGISTIQUE
044 CHEIKH TIDIANE SECK 655 TECHNICIEN BE
045 EUGENE DIBOCOR SARR 658 AGENT DE SECURITE
046 IBRAHIMA DIARRA NIANG 660 ELECTRICIEN-MONTEUR
047 MASSAMBA SOW 679 TECHNICIEN BE
048 IDRISSA BA 680 DIRECTEUR TRAVAUX
049 CHERIF DEYIBOU SOW 681 RESPONSABLE IT
050 AMADOU SADIO BARRY 682 CHAUFFEUR-GRUTIER
051 MAMADOU TALL 683 TECHNICIEN BE
052 NDEYE ANTA MAR THIAM 684 TECHNICIENNE BE
053 ELISABETH CENDRINE DIOUF 685 ASSISTANTE QHSE
054 LOUIS THOMAS CISS 686 ASSISTANT QHSE
055 GREGOIRE BABOU NGOM 688 AGENT DE SECURITE
056 MAMADOU COME MBENGUE 689 AGENT DE SECURITE
057 MOUSSA LY 690 AGENT DE SECURITE
058 AMADOU TIDIANE BALDE 691 RESPONSABLE QHSE
059 DJIBRIL NDIAYE 692 AGENT DE SECURITE
060 MOR KASSE DIRECTEUR GENERAL
061 MOUSTAPHA BA DIRECTEUR FINANCE ET CONTRÔLE
"""

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def generate_email(prenom, nom):
    p = strip_accents(prenom).lower().replace(" ", "").replace(".", "").replace("-", "")
    n = strip_accents(nom).lower().replace(" ", "").replace(".", "").replace("-", "")
    # Prendre le premier prénom complet s'il y a un espace
    if " " in prenom:
        p = strip_accents(prenom.split(" ")[0]).lower()
    return f"{p}.{n}@coselec.sn"

def parse_line(line):
    parts = line.split()
    item_num = parts[0]  # e.g. 001
    
    # Trouver l'index du matricule (c'est le mot qui est uniquement des chiffres après l'ITEM, s'il existe)
    # Pour MOR KASSE et MOUSTAPHA BA, il n'y a pas de matricule.
    mat_index = -1
    for i, p in enumerate(parts[1:], start=1):
        if p.isdigit():
            mat_index = i
            break
            
    if mat_index != -1:
        noms_prenoms = parts[1:mat_index]
        matricule = parts[mat_index]
        fonction = " ".join(parts[mat_index+1:])
    else:
        # Pas de matricule trouvé, on assume que c'est les 2 premiers mots pour prenom/nom
        noms_prenoms = parts[1:3]
        matricule = None
        fonction = " ".join(parts[3:])
        
    # Séparer Prénom et Nom
    # Généralement le dernier mot est le nom
    nom = noms_prenoms[-1]
    prenom = " ".join(noms_prenoms[:-1])
    
    email = generate_email(prenom, nom)
    
    return {
        "matricule": matricule,
        "first_name": prenom.title(),
        "last_name": nom.upper(),
        "position": fonction.title(),
        "email": email,
        "name": f"{prenom.title()} {nom.upper()}"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", type=str, required=False)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    db_url = args.db_url or os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERREUR] DATABASE_URL manquante.")
        sys.exit(1)
        
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)
    
    employees_to_insert = []
    for line in RAW_DATA.strip().split("\n"):
        if line.strip():
            employees_to_insert.append(parse_line(line))
            
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("=== IMPORT DES EMPLOYÉS ===")
            inserted_count = 0
            
            # Récupérer les emails et matricules existants pour éviter les doublons
            existing_emails = {r[0] for r in conn.execute(text("SELECT email FROM users WHERE email IS NOT NULL")).fetchall()}
            existing_matricules = {str(r[0]).strip() for r in conn.execute(text("SELECT matricule FROM users WHERE matricule IS NOT NULL")).fetchall()}
            
            for emp in employees_to_insert:
                if emp["email"] in existing_emails:
                    print(f"[SKIP] Employé déjà existant avec l'email: {emp['email']}")
                    continue
                    
                if emp["matricule"] and emp["matricule"] in existing_matricules:
                    print(f"[SKIP] Employé déjà existant avec le matricule: {emp['matricule']}")
                    continue
                    
                # Pour montrer qu'ils peuvent "devenir utilisateurs", on leur met:
                # - is_employee = True
                # - is_active = True (pour qu'ils soient actifs dans l'annuaire)
                # - hashed_password = NULL (donc ils ne peuvent pas se connecter !)
                # - aucun rôle (donc aucune permission)
                
                query = text("""
                    INSERT INTO users (name, first_name, last_name, email, matricule, position, is_employee, is_active, hashed_password)
                    VALUES (:name, :first_name, :last_name, :email, :matricule, :position, true, true, NULL)
                """)
                
                conn.execute(query, {
                    "name": emp["name"],
                    "first_name": emp["first_name"],
                    "last_name": emp["last_name"],
                    "email": emp["email"],
                    "matricule": emp["matricule"],
                    "position": emp["position"]
                })
                inserted_count += 1
                print(f"[INSERT] {emp['name']} - Mat: {emp['matricule'] or 'N/A'} - {emp['position']} - Email: {emp['email']}")
                
            if args.commit:
                trans.commit()
                print(f"\n[SUCCÈS] {inserted_count} employés ont été ajoutés à la base de données de manière sécurisée (sans accès de connexion).")
            else:
                trans.rollback()
                print(f"\n[SIMULATION] Rollback effectué. {inserted_count} employés prêts à être insérés.")
                print("-> Relance avec --commit pour valider l'insertion.")
                
        except Exception as e:
            trans.rollback()
            print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
