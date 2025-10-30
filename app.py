import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import markdown
from sqlalchemy import or_ # Importation de l'opérateur OR pour les requêtes complexes

# --- CONFIGURATION ---

# La clé secrète est nécessaire pour les sessions et l'authentification
SECRET_KEY = os.environ.get('SECRET_KEY', 'RVZpJGBVH0EQtG_QsKDJId4_mTGeQlGoC00bd3Llz6o')
# Nom du fichier de base de données SQLite
DATABASE_NAME = 'wiki.db'

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

# --- MODÈLES DE BASE DE DONNÉES ---

class Page(db.Model):
    """
    Modèle pour stocker une page du Wiki.
    Contient le contenu Markdown, le titre, et les métadonnées.
    """
    # Identifiant unique de la page
    id = db.Column(db.Integer, primary_key=True)
    # Le titre de la page
    title = db.Column(db.String(100), nullable=False)
    # Le slug (partie de l'URL) pour une navigation conviviale
    slug = db.Column(db.String(100), unique=True, nullable=False)
    # Le contenu réel de la note, stocké en Markdown
    content = db.Column(db.Text, nullable=False)
    # Date et heure de création
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Date et heure de la dernière modification
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relation pour les révisions (lazy='dynamic' est plus efficace pour une longue liste)
    revisions = db.relationship('PageRevision', backref='page', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Page {self.title}>"

class PageRevision(db.Model):
    """
    Modèle pour stocker l'historique des versions d'une page.
    """
    id = db.Column(db.Integer, primary_key=True)
    # Contenu de la révision (l'ancien contenu de la page)
    content = db.Column(db.Text, nullable=False)
    # Date et heure de l'enregistrement de cette révision
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # Clé étrangère pointant vers la page parente
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)

    def __repr__(self):
        return f"<PageRevision {self.id} for Page {self.page_id}>"

# --- FONCTIONS UTILITAIRES ---

def slugify(s):
    """
    Transforme une chaîne de caractères en un 'slug' pour une URL.
    Ex: "Ma première note" -> "ma-premiere-note"
    """
    # Remplacer les caractères non alphanumériques par des tirets
    s = re.sub(r'[^\w\s-]', '', s).strip().lower()
    # Remplacer les espaces et les tirets multiples par un seul tiret
    s = re.sub(r'[-\s]+', '-', s)
    return s

def create_app():
    # Initialisation de l'application Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Configuration de la connexion à la base de données SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_NAME}'
    # Désactiver le suivi des modifications (non nécessaire pour ce projet simple)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialisation des extensions avec l'application Flask
    db.init_app(app)

    # === DÉFINITION DES ROUTES ===

    # Route de la page d'accueil (liste simple des pages)
    @app.route('/')
    def index():
        # Récupère toutes les pages, triées par date de dernière modification
        all_pages = Page.query.order_by(Page.updated_at.desc()).all()
        # Remarque : on passe l'argument 'query' à None pour éviter une erreur dans le template
        return render_template('index.html', title='Liste des Notes', pages=all_pages, query=None)

    # Route pour afficher une page spécifique
    @app.route('/page/<slug>')
    def view_page(slug):
        # Récupère la page par son slug ou retourne une erreur 404
        page = Page.query.filter_by(slug=slug).first_or_404()
        
        # Convertit le contenu Markdown en HTML
        html_content = markdown.markdown(page.content)
        
        # Affiche le template 'page.html' avec le contenu converti
        # On passe le nombre de révisions pour l'affichage du lien
        revision_count = PageRevision.query.filter_by(page_id=page.id).count()
        return render_template('page.html', title=page.title, page=page, html_content=html_content, revision_count=revision_count)

    # Route pour créer une nouvelle page
    @app.route('/create', methods=['GET', 'POST'])
    def create_page():
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            page_slug = slugify(title)
            
            if Page.query.filter_by(slug=page_slug).first():
                return "Erreur: Une page avec un titre similaire existe déjà. Utilisez l'édition si c'est la même page.", 409

            new_page = Page(title=title, slug=page_slug, content=content)
            db.session.add(new_page)
            db.session.commit()
            
            # La première version est la création, donc on n'enregistre pas de révision avant le commit initial
            
            return redirect(url_for('view_page', slug=page_slug))
            
        # Si c'est une requête GET, affiche le formulaire de création
        # On passe 'page=None' pour réutiliser le template editor.html
        return render_template('editor.html', title='Créer une nouvelle note', page=None)

    # Route pour éditer une page existante
    @app.route('/edit/<slug>', methods=['GET', 'POST'])
    def edit_page(slug):
        page = Page.query.filter_by(slug=slug).first_or_404()
        
        if request.method == 'POST':
            # 1. Enregistrement de la révision (L'ANCIEN contenu)
            # On vérifie que le contenu a réellement changé
            new_content = request.form['content']
            if new_content != page.content:
                # Création de l'objet de révision avec l'ancien contenu
                revision = PageRevision(content=page.content, page_id=page.id)
                db.session.add(revision)

            # 2. Mise à jour de la page (NOUVEAU contenu)
            new_title = request.form['title']
            new_slug = slugify(new_title)

            if new_slug != page.slug and Page.query.filter_by(slug=new_slug).first():
                return "Erreur: Le nouveau titre génère un slug déjà utilisé par une autre page.", 409
            
            page.title = new_title
            page.content = new_content
            page.slug = new_slug 
            
            db.session.commit()
            
            return redirect(url_for('view_page', slug=page.slug))
            
        # On passe la page existante pour pré-remplir le formulaire
        return render_template('editor.html', 
                               title=f"Éditer : {page.title}",
                               page=page)
    
    # Route pour la suppression de page (méthode POST uniquement)
    @app.route('/delete/<slug>', methods=['POST'])
    def delete_page(slug):
        # Récupère la page par son slug ou retourne une erreur 404
        page = Page.query.filter_by(slug=slug).first_or_404()
        
        # SQLAlchemy gère la suppression des révisions associées (cascade="all, delete-orphan")
        # grâce à la relation définie dans le modèle Page
        db.session.delete(page)
        # Validation de la suppression
        db.session.commit()
        
        # Redirection vers la page d'accueil après suppression
        return redirect(url_for('index'))

    # Route pour la recherche plein texte
    @app.route('/search')
    def search():
        # Récupère le terme de recherche depuis les paramètres de l'URL (?q=terme)
        query = request.args.get('q', '').strip()
        results = []

        if query:
            # Construit le motif de recherche LIKE pour SQL (entouré de %)
            search_pattern = f"%{query}%"

            # Effectue la recherche sur le titre OU le contenu, en ignorant la casse (ilike)
            # Utilise 'or_' de SQLAlchemy pour combiner les conditions
            results = Page.query.filter(
                or_(
                    Page.title.ilike(search_pattern),
                    Page.content.ilike(search_pattern)
                )
            ).order_by(Page.updated_at.desc()).all()
        
        # Rend un template spécifique pour les résultats de recherche, 
        # en réutilisant l'affichage de la liste de pages
        return render_template('index.html', 
                               title=f"Résultats pour '{query}'", 
                               pages=results, 
                               query=query)

    # NOUVELLE ROUTE : Afficher l'historique des révisions d'une page
    @app.route('/history/<slug>')
    def view_history(slug):
        page = Page.query.filter_by(slug=slug).first_or_404()
        
        # Récupère toutes les révisions pour cette page, triées par ordre chronologique inverse (la plus récente en premier)
        revisions = PageRevision.query.filter_by(page_id=page.id).order_by(PageRevision.timestamp.desc()).all()
        
        # Affiche un template listant les révisions
        return render_template('history.html', title=f"Historique de : {page.title}", page=page, revisions=revisions)

    # Afficher le contenu d'une révision spécifique
    @app.route('/history/<slug>/<int:revision_id>')
    def view_revision(slug, revision_id):
        page = Page.query.filter_by(slug=slug).first_or_404()
        revision = PageRevision.query.filter_by(id=revision_id, page_id=page.id).first_or_404()
        
        # Convertit le contenu de la révision en HTML
        html_content = markdown.markdown(revision.content)
        
        return render_template('page.html', 
                               title=f"Révision #{revision_id} de {page.title}", 
                               page=page, 
                               html_content=html_content,
                               is_revision=True, # Flag pour le template
                               revision_id=revision_id,
                               current_revision=revision)

    return app

# Exécution de l'application et Initialisation de la DB
if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Va créer la nouvelle table 'page_revision'
        db.create_all() 
        print(f"Base de données '{DATABASE_NAME}' vérifiée et prête.")
    
    app.run(debug=True)

