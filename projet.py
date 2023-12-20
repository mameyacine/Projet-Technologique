import tkinter as tk
from tkinter import ttk, Label, StringVar, messagebox
from ttkthemes import ThemedTk
import sqlite3
import re

class Application(ThemedTk, tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Liste de contacts")
        self.attributes('-fullscreen', True)
        style = ttk.Style()
        style.theme_use("clam") 
        #self.set_theme("adapta")
        self.title("Mon carnet d'adresses")

        self.connection = sqlite3.connect("contacts.db")

        # Création d'un objet curseur pour exécuter des commandes SQL
        self.curseur = self.connection.cursor()

        # Création de la table "adresses" si elle n'existe pas
        self.creer_table_adresses()

        self.contacts = []

        self.creer_widgets()

        # Utiliser StringVar pour stocker la valeur du champ de saisie du téléphone
        self.var_telephone = StringVar()
      
        self.entry_search = tk.Entry(self, width=30)
        self.entry_search.pack(pady=5)
      
        self.bouton_rechercher = tk.Button(self, text="Rechercher", command=self.rechercher_contacts)
        self.bouton_rechercher.pack(pady=5)

    def creer_table_adresses(self):
        self.curseur.execute('''
            CREATE TABLE IF NOT EXISTS adresses (
                id INTEGER PRIMARY KEY,
                nom TEXT,
                prenom TEXT,
                telephone INTEGER,
                adresse TEXT,
                email TEXT
            )
        ''')
        self.connection.commit()

    def creer_widgets(self):
        colonnes = ("ID", "Nom", "Prénom", "Numéro de téléphone", "Adresse", "Email")
        self.tree = ttk.Treeview(self, columns=colonnes, show="headings")

        for col in colonnes:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)

        self.tree.pack(fill=tk.BOTH, expand=True)

        bouton_ajouter = tk.Button(self, text="Ajouter un contact", command=self.ajouter_contact)
        bouton_ajouter.pack(pady=5)

        bouton_supprimer = tk.Button(self, text="Supprimer le contact sélectionné", command=self.supprimer_contact)
        bouton_supprimer.pack(pady=5)

        bouton_modifier = tk.Button(self, text="Modifier le contact sélectionné", command=self.modifier_contact)
        bouton_modifier.pack(pady=5)

        # Charger les contacts depuis la base de données
        self.charger_contacts_depuis_db()

       

    def ajouter_contact(self):
        popup = tk.Toplevel(self)
        popup.title("Ajouter un contact")
        
        label_nom = tk.Label(popup, text="Nom:")
        label_nom.grid(row=0, column=0, padx=10, pady=5)
        entry_nom = tk.Entry(popup)
        entry_nom.grid(row=0, column=1, padx=10, pady=5)

        label_prenom = tk.Label(popup, text="Prénom:")
        label_prenom.grid(row=1, column=0, padx=10, pady=5)
        entry_prenom = tk.Entry(popup)
        entry_prenom.grid(row=1, column=1, padx=10, pady=5)

        label_telephone = tk.Label(popup, text="Numéro de téléphone:")
        label_telephone.grid(row=2, column=0, padx=10, pady=5)
        entry_telephone = tk.Entry(popup, textvariable=self.var_telephone)
        entry_telephone.grid(row=2, column=1, padx=10, pady=5)

        label_adresse = tk.Label(popup, text="Adresse:")
        label_adresse.grid(row=3, column=0, padx=10, pady=5)
        entry_adresse = tk.Entry(popup)
        entry_adresse.grid(row=3, column=1, padx=10, pady=5)

        label_email = tk.Label(popup, text="Email:")
        label_email.grid(row=4, column=0, padx=10, pady=5)
        entry_email = tk.Entry(popup)
        entry_email.grid(row=4, column=1, padx=10, pady=5)

        bouton_ajouter = tk.Button(popup, text="Ajouter", command=lambda: self.enregistrer_contact(entry_nom.get(), entry_prenom.get(), entry_telephone.get(), entry_adresse.get(), entry_email.get(), popup))
        bouton_ajouter.grid(row=5, column=0, columnspan=2, pady=10)

        entry_nom.focus_set()


    def enregistrer_contact(self, nom, prenom, telephone, adresse, email, popup):
        # Vérifier que le téléphone est au format correct
        if not re.match(r'^\+33\d{9}$', telephone):
            # Afficher une erreur si le téléphone n'est pas au bon format
            messagebox.showerror("Erreur", "Le numéro de téléphone doit être au format +33 suivi de 9 chiffres.")
            return

        # Vérifier que l'e-mail est au format correct
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            # Afficher une erreur si l'e-mail n'est pas au bon format
            messagebox.showerror("Erreur", "L'adresse e-mail doit être au format correct.")
            return

        # Insérer le contact dans la base de données
        self.curseur.execute("INSERT INTO adresses (nom, prenom, telephone, adresse, email) VALUES (?, ?, ?, ?, ?)", (nom, prenom, telephone, adresse, email))
        self.connection.commit()

        # Charger les contacts depuis la base de données
        self.charger_contacts_depuis_db()

        popup.destroy()


    def supprimer_contact(self):
        # Récupérer l'ID du contact sélectionné
        selection = self.tree.selection()
        if selection:
            id_contact = self.tree.item(selection[0], 'values')[0]

            # Supprimer le contact de la base de données
            self.curseur.execute("DELETE FROM adresses WHERE id=?", (id_contact,))
            self.connection.commit()

            # Réordonner les identifiants dans la base de données
            self.reordonner_identifiants()

            # Charger les contacts depuis la base de données
            self.charger_contacts_depuis_db()

    def reordonner_identifiants(self):
        # Récupérer la liste des contacts après suppression
        self.curseur.execute("SELECT id FROM adresses")
        ids = [item[0] for item in self.curseur.fetchall()]

        # Réordonner les identifiants dans la base de données
        for index, id_contact in enumerate(ids, start=1):
            self.curseur.execute("UPDATE adresses SET id=? WHERE id=?", (index, id_contact))
        
        self.connection.commit()

    def modifier_contact(self):
    # Récupérer l'ID du contact sélectionné
        selection = self.tree.selection()
        if selection:
            id_contact = self.tree.item(selection[0], 'values')[0]

            # Récupérer les détails du contact depuis la base de données
            self.curseur.execute("SELECT * FROM adresses WHERE id=?", (id_contact,))
            contact_details = self.curseur.fetchone()

            popup = tk.Toplevel(self)
            popup.title("Modifier le contact")
            popup.geometry("300x150")

            label_nom = Label(popup, text="Nom:")
            label_nom.grid(row=0, column=0, padx=10, pady=5)
            entry_nom = tk.Entry(popup)
            entry_nom.grid(row=0, column=1, padx=10, pady=5)
            entry_nom.insert(0, contact_details[1]) 

            label_prenom = Label(popup, text="Prénom:")
            label_prenom.grid(row=1, column=0, padx=10, pady=5)
            entry_prenom = tk.Entry(popup)
            entry_prenom.grid(row=1, column=1, padx=10, pady=5)
            entry_prenom.insert(0, contact_details[2])

            label_telephone = Label(popup, text="Numéro de téléphone:")
            label_telephone.grid(row=2, column=0, padx=10, pady=5)
            entry_telephone = tk.Entry(popup)
            entry_telephone.grid(row=2, column=1, padx=10, pady=5)
            entry_telephone.insert(0, contact_details[3])  

            label_adresse = Label(popup, text="Adresse:")
            label_adresse.grid(row=3, column=0, padx=10, pady=5)
            entry_adresse = tk.Entry(popup)
            entry_adresse.grid(row=3, column=1, padx=10, pady=5)
            entry_adresse.insert(0, contact_details[4])

            label_email = Label(popup, text="Email:")
            label_email.grid(row=4, column=0, padx=10, pady=5)
            entry_email = tk.Entry(popup)
            entry_email.grid(row=4, column=1, padx=10, pady=5)
            entry_email.insert(0, contact_details[5])  

            bouton_modifier = tk.Button(popup, text="Modifier", command=lambda: self.enregistrer_modification(id_contact, entry_nom.get(), entry_prenom.get(), entry_telephone.get(), entry_adresse.get(), entry_email.get(), popup))
            bouton_modifier.grid(row=5, column=0, columnspan=2, pady=10)

            entry_nom.focus_set()

    def enregistrer_modification(self, id_contact, nom, prenom, telephone, adresse, email, popup):
        # Mettre à jour le contact dans la base de données
        self.curseur.execute("UPDATE adresses SET nom=?, prenom=?, telephone=?, adresse=?, email=? WHERE id=?", (nom, prenom, telephone, adresse, email, id_contact))
        self.connection.commit()

        # Charger les contacts depuis la base de données
        self.charger_contacts_depuis_db()

        popup.destroy()

    def charger_contacts_depuis_db(self):
        # Effacer les contacts existants
        self.contacts = []
        # Récupérer les contacts depuis la base de données
        self.curseur.execute("SELECT * FROM adresses")
        lignes = self.curseur.fetchall()

        # Mettre à jour la liste des contacts
        for ligne in lignes:
            self.contacts.append(ligne)

        # Mettre à jour le Treeview
        self.mettre_a_jour_treeview()


    def __del__(self):
        # Fermer la connexion à la base de données lorsque l'application est détruite
        self.connection.close()

    def rechercher_contacts(self):
    # Effacer les contacts existants
        self.contacts = []

    # Récupérer la requête de recherche depuis l'entrée utilisateur
        recherche = self.entry_search.get().strip()

    # Si la requête est vide, charger tous les contacts depuis la base de données
        if not recherche:
            self.charger_contacts_depuis_db()
            return

    # Rechercher les contacts par nom, prénom ou adresse e-mail
        self.curseur.execute("SELECT * FROM adresses WHERE prenom LIKE ? OR nom LIKE ? OR email LIKE ?", ('%' + recherche + '%', '%' + recherche + '%', '%' + recherche + '%'))
        lignes = self.curseur.fetchall()

    # Si aucun résultat n'est trouvé, afficher un message d'erreur
        if not lignes:
            messagebox.showinfo("Aucun résultat", f"Aucun contact trouvé pour la recherche : {recherche}")
            return

    # Mettre à jour la liste des contacts
        for ligne in lignes:
            self.contacts.append(ligne)

    # Mettre à jour le Treeview
        self.mettre_a_jour_treeview()


    
    def mettre_a_jour_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for contact in self.contacts:
            self.tree.insert("", "end", values=contact)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
