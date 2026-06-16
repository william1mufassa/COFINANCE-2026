# COFINANCE CI — Plateforme Digitale de Microfinance & Assurance Mobile

Ce projet est la plateforme numérique de **COFINANCE CI**, conçue pour automatiser la gestion des microcrédits, les souscriptions aux assurances mobiles, le suivi des remboursements et offrir un support client en temps réel via WebSockets.

---

## 🛠️ Stack Technique

- **Backend** : Python 3.11+ / Django 5.x / Django REST Framework
- **Temps Réel** : Django Channels / Daphne / WebSockets (In-Memory Channel Layer)
- **Authentification** : JWT (JSON Web Tokens)
- **Base de données** : SQLite (dev) / Prêt pour PostgreSQL
- **Documentation API** : OpenAPI 3 / drf-spectacular (Swagger UI / Redoc)

---

## 🚀 Installation et Démarrage rapide

### 1. Prérequis
Assurez-vous d'avoir **Python 3.11+** et **Git** installés sur votre machine.

### 2. Cloner le projet
```bash
git clone <url_du_depot>
cd "COFINANCE 2026"
```

### 3. Activer l'environnement virtuel et installer les dépendances
Sur Windows :
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Sur Linux/macOS :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Appliquer les migrations de base de données
```bash
python manage.py migrate
```

### 5. Peupler la base de données avec le jeu de données de démonstration
Cette commande configure automatiquement les rôles, les produits d'assurance, crée 3 utilisateurs types (Client, Agent, Admin), enregistre un crédit décaissé avec son historique de remboursement, et initialise une conversation de chat.
```bash
python manage.py seed_db
```

### 6. Lancer le serveur d'application (Daphne - nécessaire pour les WebSockets)
```bash
daphne cofinance_ci.asgi:application
```
Le serveur sera disponible sur : **http://localhost:8000**

---

## 🔑 Comptes de démonstration pré-configurés

Utilisez ces identifiants pour vous connecter et tester les différents niveaux d'autorisation sur l'API ou sur l'interface de chat.

| Rôle | Nom d'utilisateur | Email | Mot de passe | Description |
|---|---|---|---|---|
| **Administrateur** | `admin` | `admin@cofinci.ci` | `Admin1234!` | Accès complet, Dashboard stats global |
| **Agent de terrain** | `agent1` | `agent@cofinci.ci` | `Agent1234!` | Enregistre les paiements, répond au chat client |
| **Client** | `client1` | `client@cofinci.ci` | `Client1234!` | Soumet crédits, souscrit assurances, discute par chat |

---

## 📖 Documentation de l'API

L'API est entièrement documentée avec **Swagger UI** et **Redoc**. Les routes non authentifiées sont accessibles publiquement. Pour les routes protégées, connectez-vous d'abord via `/api/auth/login/` pour récupérer un token d'accès JWT, puis utilisez-le dans l'en-tête de vos requêtes (`Authorization: Bearer <token_access>`).

- **Swagger UI (Interactif)** : [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Redoc** : [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

---

## 💬 Démonstration du Chat Temps Réel (WebSockets)

Le module de chat supporte la communication bidirectionnelle en temps réel avec indicateur de frappe (*typing indicator*).

1. Démarrez le serveur Daphne : `daphne cofinance_ci.asgi:application`
2. Ouvrez **deux fenêtres ou onglets différents** du navigateur sur :
   - [http://localhost:8000/static/chat.html](http://localhost:8000/static/chat.html)
3. Dans la **première fenêtre**, connectez-vous comme **Client** (`client1` / `Client1234!`).
4. Dans la **deuxième fenêtre**, connectez-vous comme **Agent** (`agent1` / `Agent1234!`).
5. Sélectionnez le ticket de discussion actif.
6. Échangez des messages en temps réel. Vous verrez l'indicateur de frappe s'afficher lorsque l'un des deux rédige un message !

---

## 🕒 Commandes de tâches planifiées (Management Commands)

Deux commandes Django personnalisées simulent des processus planifiés en arrière-plan :

1. **Relances de remboursements (J-3 et J+1)** :
   ```bash
   python manage.py send_repayment_alerts
   ```
   - Rappelle aux clients les échéances à venir à J-3.
   - Alerte les clients et les agents des retards à J+1 et marque les échéances en retard.

2. **Alertes d'expiration d'assurance (J-15)** :
   ```bash
   python manage.py check_insurance_expirations
   ```
   - Alerte les clients 15 jours avant la fin de leur police d'assurance pour les inciter au renouvellement.
