import json

nodes = [
    {"key": "dg", "title": "DIRECTEUR GÉNÉRAL", "l": 670, "t": 20},
    {"key": "dga", "title": "DIRECTEUR GÉNÉRAL ADJOINT", "l": 370, "t": 120},
    {"key": "assistante", "title": "ASSISTANTE DE DIRECTION", "l": 970, "t": 120},
    {"key": "ast_smqse", "title": "ASSISTANT SMQSE", "l": 270, "t": 220},
    {"key": "resp_smqse", "title": "RESPONSABLE SMQSE", "l": 470, "t": 220},
    {"key": "resp_it", "title": "RESPONSABLE SUPPORT IT", "l": 370, "t": 320},
    
    {"key": "dir_fin", "title": "DIRECTEUR DES FINANCES ET CONTRÔLE", "l": 170, "t": 440, "hl": "yellow"},
    {"key": "comp_rh", "title": "COMPTABLE ET RESPONSABLE RH", "l": 170, "t": 540},
    {"key": "comp_tres", "title": "COMPTABLE TRÉSORERIE", "l": 170, "t": 620},
    {"key": "comp_fourn", "title": "COMPTABLE FOURNISSEURS CLIENTS", "l": 170, "t": 700},
    {"key": "recouv", "title": "CHARGÉE DU RECOUVREMENT", "l": 170, "t": 780},
    
    {"key": "resp_com", "title": "RESPONSABLE PÔLE COMMERCIAL & APPRO", "l": 670, "t": 440, "hl": "yellow"},
    {"key": "serv_com", "title": "SERVICE COMMERCIAL", "l": 470, "t": 540},
    {"key": "serv_appro", "title": "SERVICE APPRO", "l": 670, "t": 540},
    {"key": "serv_log", "title": "SERVICE LOGISTIQUE", "l": 870, "t": 540},
    
    {"key": "dir_tech", "title": "DIRECTEUR TECHNIQUE", "l": 1170, "t": 440, "hl": "yellow"},
    {"key": "chef_etudes", "title": "CHEF SERVICE ÉTUDES", "l": 1020, "t": 540},
    {"key": "chef_travaux", "title": "CHEF SERVICE TRAVAUX", "l": 1320, "t": 540},
    
    {"key": "tech_etudes", "title": "TECHNICIENS BUREAU D'ÉTUDES", "l": 1150, "t": 620},
    {"key": "charge_projet", "title": "CHARGÉS DE PROJET", "l": 1150, "t": 700},
    {"key": "charge_suivi", "title": "CHARGÉ DU SUIVI ET DES PLANNINGS", "l": 1150, "t": 780},
    
    {"key": "cond_travaux", "title": "CONDUCTEURS DE TRAVAUX", "l": 1450, "t": 620},
    {"key": "chef_atelier", "title": "CHEF D'ATELIER", "l": 1450, "t": 700},
    {"key": "chef_chantier", "title": "CHEFS DE CHANTIER", "l": 1450, "t": 780},
    {"key": "vigiles", "title": "VIGILES", "l": 1450, "t": 860},
]

lines = [
    {"l": 749, "t": 80, "w": 2, "h": 340},
    {"l": 250, "t": 419, "w": 1000, "h": 2},
    {"l": 249, "t": 420, "w": 2, "h": 20},
    {"l": 749, "t": 420, "w": 2, "h": 20},
    {"l": 1249, "t": 420, "w": 2, "h": 20},
    {"l": 450, "t": 149, "w": 300, "h": 2},
    {"l": 750, "t": 149, "w": 300, "h": 2},
    {"l": 449, "t": 180, "w": 2, "h": 20},
    {"l": 350, "t": 199, "w": 200, "h": 2},
    {"l": 349, "t": 200, "w": 2, "h": 20},
    {"l": 549, "t": 200, "w": 2, "h": 20},
    {"l": 530, "t": 349, "w": 220, "h": 2},
    {"l": 140, "t": 469, "w": 30, "h": 2},
    {"l": 139, "t": 470, "w": 2, "h": 310},
    {"l": 140, "t": 569, "w": 30, "h": 2},
    {"l": 140, "t": 649, "w": 30, "h": 2},
    {"l": 140, "t": 729, "w": 30, "h": 2},
    {"l": 140, "t": 809, "w": 30, "h": 2},
    {"l": 749, "t": 500, "w": 2, "h": 20},
    {"l": 550, "t": 519, "w": 400, "h": 2},
    {"l": 549, "t": 520, "w": 2, "h": 20},
    {"l": 749, "t": 520, "w": 2, "h": 20},
    {"l": 949, "t": 520, "w": 2, "h": 20},
    {"l": 1249, "t": 500, "w": 2, "h": 20},
    {"l": 1100, "t": 519, "w": 300, "h": 2},
    {"l": 1099, "t": 520, "w": 2, "h": 20},
    {"l": 1399, "t": 520, "w": 2, "h": 20},
    {"l": 1099, "t": 600, "w": 2, "h": 210},
    {"l": 1100, "t": 649, "w": 50, "h": 2},
    {"l": 1100, "t": 729, "w": 50, "h": 2},
    {"l": 1100, "t": 809, "w": 50, "h": 2},
    {"l": 1399, "t": 600, "w": 2, "h": 290},
    {"l": 1400, "t": 649, "w": 50, "h": 2},
    {"l": 1400, "t": 729, "w": 50, "h": 2},
    {"l": 1400, "t": 809, "w": 50, "h": 2},
    {"l": 1400, "t": 889, "w": 50, "h": 2},
]

html_nodes = []
for n in nodes:
    hl = f"highlight: '{n.get('hl')}'" if 'hl' in n else ""
    title = n['title'].replace("'", "\\'")
    obj_str = "{ key: '" + n['key'] + "', title: '" + title + "'"
    if hl:
        obj_str += ", " + hl
    obj_str += " }"
    
    html_nodes.append(f'          <div class="absolute z-10" style="left: {n["l"]}px; top: {n["t"]}px; width: 160px;">')
    html_nodes.append(f'            <OrgCard :node="{obj_str}" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({obj_str})" />')
    html_nodes.append(f'          </div>')

html_lines = []
for i, l in enumerate(lines):
    html_lines.append(f'          <div class="absolute bg-[#9ca3af] z-0" style="left: {l["l"]}px; top: {l["t"]}px; width: {l["w"]}px; height: {l["h"]}px;"></div>')

with open("org_output.html", "w", encoding="utf-8") as f:
    f.write("<!-- NODES -->\n")
    f.write("\n".join(html_nodes) + "\n")
    f.write("<!-- LINES -->\n")
    f.write("\n".join(html_lines) + "\n")
