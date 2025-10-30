### DISCLAIMER: Ce projet à été réalisé en partie avec l'aide de Google Gemini 2.5 Flash.

### 📚 Mini-Wiki/Système de Notes Personnelles

### Vue d'Ensemble du Projet

Ce projet est une application web simple de type Wiki ou système de prise de notes développée avec le micro-framework **Flask** et utilisant **SQLAlchemy** pour la gestion des données. L'objectif est de fournir une interface utilisateur basique mais fonctionnelle pour créer, lire, modifier et gérer l'historique de versions des notes.

Il intègre la conversion de contenu en **Markdown** pour un formatage riche des notes.

### Fonctionnalités Clés

* **CRUD** : Création, lecture, édition et suppression des pages.
* **Historique de Révisions (Versioning)** : Chaque modification d'une page sauvegarde l'ancien contenu dans une table `PageRevision`, permettant de consulter les versions précédentes.
* **Affichage Markdown** : Le contenu est rédigé en Markdown et converti en HTML pour l'affichage.
* **Recherche Plein Texte** : Recherche de notes par mot-clé, dans le titre ou le contenu.
* **URL Conviviales (Slugs)** : Utilisation de slugs générés à partir du titre pour des URL claires et lisibles.

### Prérequis et installation

* Python 3.x
* pip (gestionnaire de paquets Python)

### Installation et Démarrage

Suivez ces étapes pour lancer le projet en local :

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python app.py

### Accès à l'Application

Ouvrez votre navigateur web et accédez à :

[http://127.0.0.1:5000/]

### Structure des Fichiers

* app.py, Le cœur de l'application Flask, incluant les modèles de BDD (Page, PageRevision), les routes, la logique de révision et la recherche.
* requirements.txt, Liste des dépendances Python requises pour le projet.
* templates/, Dossier contenant les templates Jinja2 (index.html, page.html, editor.html, history.html).
* wiki.db, La base de données SQLite générée.

### Améliorations Possibles

Ajout d'un système d'authentification utilisateur (en cours, sera probablement dans un dépôt séparé)

Ajout d'une fonctionnalité de restauration à partir de l'historique de révision.

Amélioration du style CSS (intégration de Bootstrap ou Tailwind).
