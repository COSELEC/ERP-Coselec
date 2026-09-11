import json

W = 180
H = 70

# CX, CY, Title, Highlight
nodes_data = {
    'dg': (750, 50, 'DIRECTEUR GÉNÉRAL', None),
    'dga': (450, 140, 'DIRECTEUR GÉNÉRAL ADJOINT', None),
    'assistante': (1050, 190, 'ASSISTANTE DE DIRECTION', None),
    'resp_smqse': (550, 250, 'RESPONSABLE SMQSE', None),
    'ast_smqse': (250, 250, 'ASSISTANT SMQSE', None),
    'resp_it': (450, 330, 'RESPONSABLE SUPPORT IT', None),
    
    'dir_fin': (250, 480, 'DIRECTEUR DES FINANCES ET CONTRÔLE', 'yellow'),
    'comp_rh': (250, 580, 'COMPTABLE ET RESPONSABLE RH', None),
    'comp_tres': (250, 660, 'COMPTABLE TRÉSORERIE', None),
    'comp_fourn': (250, 740, 'COMPTABLE FOURNISSEURS CLIENTS', None),
    'recouv': (250, 820, 'CHARGÉE DU RECOUVREMENT', None),
    
    'resp_com': (750, 480, 'RESPONSABLE PÔLE COMMERCIAL & APPRO', 'yellow'),
    'serv_com': (500, 580, 'SERVICE COMMERCIAL', None),
    'serv_appro': (750, 580, 'SERVICE APPRO', None),
    'serv_log': (1000, 580, 'SERVICE LOGISTIQUE', None),
    
    'dir_tech': (1450, 480, 'DIRECTEUR TECHNIQUE', 'yellow'),
    'chef_etudes': (1300, 580, 'CHEF SERVICE ÉTUDES', None),
    'chef_travaux': (1600, 580, 'CHEF SERVICE TRAVAUX', None),
    
    'tech_etudes': (1420, 660, "TECHNICIENS BUREAU D'ÉTUDES", None),
    'charge_projet': (1420, 740, 'CHARGÉS DE PROJET', None),
    'charge_suivi': (1420, 820, 'CHARGÉ DU SUIVI ET DES PLANNINGS', None),
    
    'cond_travaux': (1720, 660, 'CONDUCTEURS DE TRAVAUX', None),
    'chef_atelier': (1720, 740, "CHEF D'ATELIER", None),
    'chef_chantier': (1720, 820, 'CHEFS DE CHANTIER', None),
    'vigiles': (1720, 900, 'VIGILES', None),
}

lines_data = []
def add_line(x, y, w, h):
    lines_data.append({"l": x, "t": y, "w": w, "h": h})

def hline(x1, x2, y):
    add_line(min(x1, x2), y, abs(x2 - x1), 2)

def vline(x, y1, y2):
    add_line(x, min(y1, y2), 2, abs(y2 - y1))

# Spine
vline(750, 85, 430)

# DGA
hline(750, 540, 140)

# Assistante
hline(750, 960, 190)

# Resp SMQSE
hline(750, 640, 250)

# Ast SMQSE (from Resp SMQSE)
hline(460, 340, 250)

# Resp IT
hline(750, 540, 330)

# Main Horizontal Divider
hline(250, 1450, 430)
vline(250, 430, 445)
vline(750, 430, 445)
vline(1450, 430, 445)

# Finance Sub-branch
vline(250, 515, 530)
hline(250, 130, 530)
vline(130, 530, 820)
for cy in [580, 660, 740, 820]:
    hline(130, 160, cy)

# Commercial Sub-branch
vline(750, 515, 540)
hline(500, 1000, 540)
for cx in [500, 750, 1000]:
    vline(cx, 540, 545)

# Technique Sub-branch
vline(1450, 515, 540)
hline(1300, 1600, 540)
for cx in [1300, 1600]:
    vline(cx, 540, 545)

# Chef Etudes Sub-branch
vline(1300, 615, 630)
vline(1300, 630, 820)
for cy in [660, 740, 820]:
    hline(1300, 1330, cy)

# Chef Travaux Sub-branch
vline(1600, 615, 630)
vline(1600, 630, 900)
for cy in [660, 740, 820, 900]:
    hline(1600, 1630, cy)


html_nodes = []
for key, (cx, cy, title, hl) in nodes_data.items():
    l = cx - W // 2
    t = cy - H // 2
    hl_str = f"highlight: '{hl}'" if hl else ""
    title_escaped = title.replace("'", "\\'")
    obj_str = "{ key: '" + key + "', title: '" + title_escaped + "'"
    if hl_str:
        obj_str += ", " + hl_str
    obj_str += " }"
    
    html_nodes.append(f'          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: {l}px; top: {t}px; width: {W}px;">')
    html_nodes.append(f'            <OrgCard :node="{obj_str}" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({obj_str})" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{obj_str}.highlight === \'yellow\' ? \'border-yellow-400\' : \'border-red-600\']" />')
    html_nodes.append(f'          </div>')

html_lines = []
for l in lines_data:
    # Use rounded corners for lines to make it "plus sympa"
    html_lines.append(f'          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: {l["l"]}px; top: {l["t"]}px; width: {l["w"]}px; height: {l["h"]}px;"></div>')

with open("org_output.html", "w", encoding="utf-8") as f:
    f.write("<!-- NODES -->\n")
    f.write("\n".join(html_nodes) + "\n")
    f.write("<!-- LINES -->\n")
    f.write("\n".join(html_lines) + "\n")
