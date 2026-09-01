# COSELEC ERP

Une solution de planification des ressources de l'entreprise (ERP) moderne et performante conçue pour centraliser et automatiser la gestion des processus internes de COSELEC.

---

## Fonctionnalités

L'application est divisée en plusieurs grands modules logiques :

### 🔐 Authentification & Sécurité (RBAC)
- Authentification par JWT avec middleware de session glissante (Sliding Session).
- Gestion fine des rôles (Admin, RH, Direction, Finance, Logistique, Responsable Projet, etc.) et permissions gérées dynamiquement.
- **Réinitialisation de mot de passe** : Workflow complet pour les utilisateurs.

### 👥 Ressources Humaines (RH)
- **Gestion des employés & Départements** : Répertoire complet et affectation.
- **Contrats & Documents** : Suivi des contrats, stockage des documents avec alertes automatiques à l'expiration (badges visuels et Cron job quotidien).
- **Signatures de documents** : Processus de signature intégré pour les documents RH.
- **Pointage / Présences** : Suivi du temps de travail.

### 📝 Gestion des Demandes
- **Demandes générales** : Workflow de soumission et de validation par les managers/RH.
- **Demandes de carburant** : Workflow spécifique, validation finance, et génération de bons en PDF.

### 📦 Stock & Logistique
- **Produits & Catégories** : Catalogue complet des références.
- **Entrepôts** : Suivi multi-sites.
- **Mouvements & Réservations** : Entrées, sorties, transferts inter-dépôts et réservation de matériel par projet.

### 🛒 Achats (Procurement)
- **Partenaires & Fournisseurs** : Gestion des tiers.
- **Demandes d'Achats & Bons de Commande (BC)** : Workflow d'approbation et génération/impression PDF automatisée des BC.

### 🚀 Gestion de Projets & KPIs
- **Tableaux de bord (Dashboards)** : Suivi d'avancement des projets, indicateurs de performance (KPI) et portefeuille.
- **Tâches & Jalons (Milestones)** : Gantt et planification.
- **Budget & Dépenses** : Suivi financier granulaire par projet.

### 📄 Finance & Documents
- **Pièces de Caisse** : Module de création, traçabilité historique et génération PDF des pièces de caisse.

---

## Stack Technique

Le projet repose sur une architecture moderne séparant le frontend du backend.

**Frontend**
- **Framework** : Vue.js 3 (Composition API) via Vite.
- **Style** : TailwindCSS 4.
- **Routing & State** : Vue Router, Pinia.
- **Graphiques & UI** : Chart.js, Vue-ganttastic, TanStack Vue Table.

**Backend**
- **Framework API** : FastAPI (Python 3).
- **Base de Données** : PostgreSQL avec SQLAlchemy (ORM) et Alembic (Migrations).
- **Tâches en arrière-plan** : APScheduler.
- **Génération PDF** : ReportLab.
- **Stockage Fichiers** : Cloudflare R2 / Système de fichiers local.

**Infrastructure**
- Docker & Docker Compose (pour la DB et/ou les environnements complets).

---

## Architecture

L'architecture suit un modèle Client-Serveur classique de type "Single Page Application" (SPA) avec une API REST.

```mermaid
graph TD
    Client[Navigateur Web / Vue.js] -->|Requêtes HTTP / Axios| API[Backend FastAPI]
    API -->|SQLAlchemy ORM| DB[(PostgreSQL)]
    API -->|Sauvegarde de Fichiers| Storage[Cloudflare R2 / Dossier uploads/]
    API -->|Génération PDF| ReportLab[Générateur PDF]
    Cron[APScheduler] -->|Tâches de fond| API
```

---

## Structure du Projet

Le dépôt est composé de deux dossiers principaux :

```text
ERP/
├── backend/                  # API FastAPI
│   ├── alembic/              # Fichiers de migration de la base de données
│   ├── app/
│   │   ├── core/             # Configuration, Base de données, Sécurité (JWT)
│   │   ├── enums/            # Enumérations partagées
│   │   ├── models/           # Modèles SQLAlchemy (Définition des tables)
│   │   ├── modules/          # Modules "métier" (RH, Users, Requests)
│   │   ├── repositories/     # Couche d'accès aux données
│   │   ├── routers/          # Points d'entrée (Endpoints) de l'API
│   │   ├── schemas/          # Schémas Pydantic pour la validation (Input/Output)
│   │   ├── services/         # Logique métier, Génération PDF, Storage S3
│   │   ├── tasks/            # Tâches planifiées (ex: alertes RH)
│   │   ├── templates/        # Templates HTML/Jinja2 (ex: emails, PDF)
│   │   └── main.py           # Point d'entrée de l'application FastAPI
│   ├── requirements.txt      # Dépendances Python
│   ├── Dockerfile            # Image Docker pour le backend
│   └── seed.py               # Script de remplissage de la base de données
│
├── frontend/                 # Application Vue.js
│   ├── public/               # Ressources statiques
│   ├── src/
│   │   ├── assets/           # Ressources globales (Styles, Images)
│   │   ├── components/       # Composants réutilisables (AppTable, AppPagination, Modals, etc.)
│   │   ├── composables/      # Fonctions réutilisables (ex: useToast)
│   │   ├── layouts/          # Composants de mise en page (Main, Auth)
│   │   ├── router/           # Configuration Vue Router
│   │   ├── services/         # Services API (Axios), Auth Session
│   │   ├── stores/           # Gestion de l'état global (Pinia)
│   │   └── views/            # Pages de l'application (Views)
│   ├── package.json          # Dépendances Node.js
│   ├── vite.config.ts        # Configuration Vite
│   └── Dockerfile            # Image Docker & Nginx pour le frontend
│
└── docker-compose.yml        # Orchestration Docker (Base de données, Front, Back)
```

---

## Démarrage rapide

### Prérequis
- [Node.js](https://nodejs.org/) (v22+ ou v24+)
- [Python](https://www.python.org/) 3.10+
- [PostgreSQL](https://www.postgresql.org/) (ou Docker pour l'exécuter via `docker-compose`)

### Variables d'environnement

Vous devez configurer les variables d'environnement dans le `backend/.env`.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Chaîne de connexion PostgreSQL (ex: `postgresql://user:pass@localhost/erp_db`) |
| `SECRET_KEY` | Clé secrète pour signer les jetons JWT |
| `CORS_ALLOW_ORIGINS` | URLs autorisées pour le frontend (ex: `http://localhost:5173`) |
| `MINIO_*` | (Optionnel) Identifiants pour le stockage S3 si activé |

### Démarrage avec Docker Compose (Recommandé)

Le projet inclut un fichier `docker-compose.yml` qui provisionne la base de données PostgreSQL, le Backend et le Frontend.

```bash
# Lancer les conteneurs en tâche de fond
docker-compose up -d
```

### Installation manuelle (Développement)

**1. Base de données & Migrations**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Sous Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Créer la base de données PostgreSQL puis exécuter les migrations
alembic upgrade head

# Optionnel : Remplir la base de données avec des données de test
python app/seed.py
```

**2. Lancer le Backend (FastAPI)**
```bash
# Toujours dans le dossier backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
L'API sera disponible sur : `http://localhost:8000` (Documentation Swagger accessible sur `/docs`).

**3. Lancer le Frontend (Vue.js)**
```bash
cd frontend
npm install
npm run dev
```
Le frontend sera disponible sur : `http://localhost:5173`.

---

## Base de données & Modélisation

Le backend utilise **SQLAlchemy 2.0** pour l'ORM.  
Les migrations sont gérées par **Alembic**.

Principaux domaines de la modélisation :
- **Users & RBAC** : `User`, `Role`, `Permission`, `Employee`, `Department`.
- **Stock** : `Product`, `Category`, `Stock`, `Warehouse`, `StockMovement`, `ProjectStockReservation`.
- **Procurement** : `Partner`, `PurchaseRequest`, `PurchaseOrder`, `PurchaseOrderLine`.
- **Projects** : `Project`, `ProjectPhase`, `ProjectMilestone`, `ProjectBudget`, `ProjectExpense`.

---
