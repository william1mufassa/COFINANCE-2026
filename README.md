# COFINANCE CI — Plateforme Digitale de Microfinance & Assurance Mobile

Plateforme numérique de **COFINANCE CI** pour automatiser la gestion des microcrédits, les souscriptions aux assurances mobiles, le suivi des remboursements et le support client en temps réel via WebSockets.

---

## Stack Technique

| Couche | Technologies |
|--------|-------------|
| Backend | Python 3.11+ / Django 5.x / Django REST Framework |
| Temps réel | Django Channels 4 / Daphne / WebSockets |
| Channel layer | Redis (production) / InMemory (développement) |
| Authentification | JWT via djangorestframework-simplejwt (blacklist activée) |
| Base de données | SQLite (dev) / PostgreSQL (production) |
| Documentation API | OpenAPI 3 / drf-spectacular — Swagger UI & Redoc |
| Stockage fichiers | Système local (dev) / AWS S3 (optionnel) |

---

## Installation et démarrage rapide

### 1. Prérequis

- Python 3.11+
- Git
- (Production) Redis, PostgreSQL

### 2. Cloner le projet

```bash
git clone https://github.com/william1mufassa/COFINANCE.git
cd "COFINANCE 2026"
```

### 3. Environnement virtuel et dépendances

**Windows**
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Copiez `.env.example` en `.env` et renseignez les valeurs :

```bash
cp .env.example .env
```

Variables obligatoires :

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django — générez-en une avec `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` en dev, `False` en production |
| `ALLOWED_HOSTS` | Ex : `localhost,127.0.0.1` ou votre domaine |
| `CORS_ALLOWED_ORIGINS` | Origines autorisées, ex : `http://localhost:3000` |

Variables optionnelles :

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL — ex : `postgres://user:pass@localhost:5432/cofinance` (SQLite si absent) |
| `REDIS_URL` | Redis pour Channels — ex : `redis://localhost:6379/0` (InMemory si absent) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_STORAGE_BUCKET_NAME` | Stockage S3 (optionnel) |

### 5. Appliquer les migrations

```bash
python manage.py migrate
```

### 6. Peupler la base de données de démonstration

Crée 3 utilisateurs types, des produits d'assurance, un crédit décaissé avec historique de remboursement et une conversation de chat.

```bash
python manage.py seed_db
```

### 7. Lancer le serveur (Daphne — requis pour les WebSockets)

```bash
daphne cofinance_ci.asgi:application
```

Serveur disponible sur : **http://localhost:8000**

---

## Comptes de démonstration

| Rôle | Identifiant | Mot de passe | Accès |
|------|-------------|--------------|-------|
| Administrateur | `admin` | `Admin1234!` | Accès complet, dashboard, gestion utilisateurs |
| Agent de terrain | `agent1` | `Agent1234!` | Enregistrement paiements, chat support |
| Client | `client1` | `Client1234!` | Dépôt crédit, assurance, chat |

---

## Documentation de l'API

| Interface | URL |
|-----------|-----|
| Swagger UI (interactif) | http://localhost:8000/api/docs/ |
| Redoc | http://localhost:8000/api/redoc/ |

**Authentification** : appelez `POST /api/auth/login/` avec `username` et `password` pour obtenir un token JWT, puis ajoutez `Authorization: Bearer <token>` dans vos requêtes.

**Déconnexion** : appelez `POST /api/auth/logout/` avec le `refresh` token pour l'invalider immédiatement (blacklist).

---

## Modules fonctionnels

| Module | Endpoints principaux |
|--------|---------------------|
| **01 — Auth & Profils** | `POST /api/auth/register/` · `POST /api/auth/login/` · `POST /api/auth/logout/` · `GET|PATCH /api/auth/profile/` |
| **02 — Microcrédits** | `POST /api/credits/` · `PATCH /api/credits/<id>/status/` · `POST /api/credits/<id>/documents/` |
| **03 — Remboursements** | `POST /api/repayments/` · `GET /api/repayments/<id>/history/` · `GET /api/repayments/overdue/` |
| **04 — Assurance mobile** | `GET /api/insurance/products/` · `POST /api/insurance/subscriptions/` · `PATCH /api/insurance/subscriptions/<id>/renew/` |
| **05 — Dashboard** | `GET /api/dashboard/summary/?start_date=&end_date=&agent_id=&region=` |
| **06 — Notifications** | `GET /api/notifications/` · `PATCH /api/notifications/<id>/read/` · `GET /api/notifications/unread-count/` |
| **07 — Chat temps réel** | `POST /api/chat/conversations/` · WebSocket `ws://localhost:8000/ws/chat/<id>/` |

### Workflow de statut crédit

Les transitions suivent une matrice stricte :

```
SOUMISE → EN_ANALYSE → APPROUVÉE → DÉCAISSÉE
    └──────────────────────────┘
                ↓ (toute étape)
             REJETÉE
```

---

## Chat temps réel — Démonstration

1. Démarrez le serveur : `daphne cofinance_ci.asgi:application`
2. Ouvrez **deux onglets** sur [http://localhost:8000/static/chat.html](http://localhost:8000/static/chat.html)
3. Premier onglet : connectez-vous comme **Client** (`client1` / `Client1234!`)
4. Deuxième onglet : connectez-vous comme **Agent** (`agent1` / `Agent1234!`)
5. Sélectionnez le ticket actif et échangez des messages en temps réel

L'indicateur de frappe (« en train d'écrire... ») s'affiche en temps réel.

> **Production** : définissez `REDIS_URL` dans `.env` pour que les WebSockets fonctionnent avec plusieurs workers ASGI.

---

## Commandes planifiées

```bash
# Rappels J-3 et alertes retard J+1
python manage.py send_repayment_alerts

# Alertes expiration assurance J-15
python manage.py check_insurance_expirations
```

### Automatisation

**Linux (cron)** — ajoutez à `crontab -e` :
```text
0 0 * * * cd /chemin/projet && /chemin/venv/bin/python manage.py send_repayment_alerts >> logs/cron_alerts.log 2>&1
5 0 * * * cd /chemin/projet && /chemin/venv/bin/python manage.py check_insurance_expirations >> logs/cron_insurance.log 2>&1
```

**Windows (Planificateur de tâches)** — créez `run_alerts.bat` :
```batch
cd "C:\Users\Abdallah\Desktop\COFINANCE 2026"
call .\venv\Scripts\activate.bat
python manage.py send_repayment_alerts
python manage.py check_insurance_expirations
```

---

## Administration Django

Interface d'administration disponible sur `/admin/` — tous les modèles sont enregistrés :
- Utilisateurs (avec champs COFINANCE : rôle, région, vérification)
- Demandes de crédit, documents, échéanciers, paiements
- Souscriptions et produits d'assurance
- Conversations et messages de chat
- Notifications

Créez un superuser si nécessaire : `python manage.py createsuperuser`

---

## Déploiement en production

Les paramètres de sécurité suivants s'activent automatiquement quand `DEBUG=False` :

- `SECURE_SSL_REDIRECT` — redirection HTTPS forcée
- `SECURE_HSTS_SECONDS` — HSTS 1 an
- `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` — cookies HTTPS uniquement
- `SECURE_CONTENT_TYPE_NOSNIFF`

Checklist minimale avant mise en production :

- [ ] `SECRET_KEY` unique et aléatoire dans `.env`
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` limité à votre domaine
- [ ] `CORS_ALLOWED_ORIGINS` limité à votre frontend
- [ ] `DATABASE_URL` → PostgreSQL
- [ ] `REDIS_URL` → Redis (obligatoire si plusieurs workers ASGI)
- [ ] Serveur HTTPS (Nginx + Let's Encrypt recommandé)
