import tkinter as tk
from tkinter import scrolledtext, Scrollbar
import math
from time import time
import re
from datetime import datetime
import os
import sys

# Liste des modules à vérifier et à installer
modules = ['PIL', 'psutil']

# Vérification et installation des modules sur macOS
if sys.platform == 'darwin':
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"{module} n'est pas installé. Installation...")
            if module == 'PIL':
                os.system("brew install pillow")
            elif module == 'psutil':
                os.system("brew install python-psutil")

# Vérification et installation des modules sur Windows
elif sys.platform == 'win32':
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"{module} n'est pas installé. Installation...")
            if module == 'PIL':
                os.system("pip install pillow")
            elif module == 'psutil':
                os.system("pip install psutil")

import psutil
from PIL import Image, ImageDraw, ImageTk

"""
L'écran principal affiche l'expression en cours, le résultat calculé et l'historique.
Les boutons de déplacement du curseur clignotant nous permettent de naviguer dans l'expression pour éditer notre saisie.
En plus des boutons numériques et d'opérations, nous avons ajouté des parenthèses pouvant être utilisées pour grouper les expressions.
En cas d'erreur, la calculatrice affiche un message approprié au type d'erreur.
Certaines 'règles' mathématiques que Python ne gère pas bien ont été ajoutées comme la gestion des nombres commencant par 0 
ou les multiplications implicites entre deux termes collés.
"""

class Calculatrice(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TP5 Calculatrice")
        self.blink_timer = time()  # Initialise le timer pour le clignotement du curseur
        self.cursor_visible = True  # Indique si le curseur est actuellement visible ou non
        self.disw = False


        # Frame principale qui représente l'écran de la calculatrice
        self.main_frame = tk.Frame(self, bg="#f0f0f0", relief="ridge", bd=15)
        self.main_frame.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        # Couleur générale de la calculatrice
        self.configure(bg="#bbbbbb")

        self.resultat = tk.StringVar()  # Variable pour stocker les résultats des calculs
        self.cursorframe = tk.StringVar()  # Variable pour afficher le curseur

        # Ajout de la barre d'état en haut de la frame principale
        self.status_bar = tk.Label(self.main_frame, text="", bg="#cccccc", fg="black", font=("Monaco", 10), bd=1, anchor=tk.CENTER, justify=tk.CENTER)
        self.status_bar.grid(row=0, column=0, columnspan=5, sticky="ew")

        # Met à jour la barre d'état toutes les secondes
        self.update_status_bar()

        # Frame pour la zone de saisie
        self.entry_frame = tk.Frame(self)
        self.entry_frame.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="ew")
        self.entry_frame.grid_remove()  # Masquer la frame car elle est utile pour effectuer les calculs mais inutile visuellement

        # Entrée de la calculatrice
        self.entry = tk.Entry(self.entry_frame, textvariable=self.resultat, font=("Monaco", 20), justify="right", state='readonly', bd=0)
        self.entry.pack(fill="both", expand=True)

        # Ajout du défilement horizontal pour l'entrée
        self.x_scrollbar = Scrollbar(self.entry_frame, orient='horizontal', command=self.entry.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')
        self.entry.config(xscrollcommand=self.x_scrollbar.set)

        # Frame pour afficher le curseur
        self.cursor_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.cursor_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Entrée pour afficher le curseur
        self.cursor_entry = tk.Entry(self.cursor_frame, textvariable=self.cursorframe, font=("Monaco", 20), justify="right", bd=0, bg="#f0f0f0")
        self.cursor_entry.pack(fill="both", expand=True)

        # Ajout du défilement horizontal pour l'affichage du curseur
        self.x_scrollbar = Scrollbar(self.cursor_frame, orient='horizontal', command=self.cursor_entry.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')
        self.cursor_entry.config(xscrollcommand=self.x_scrollbar.set)

        # Frame pour afficher le résultat
        self.result_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.result_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Entrée pour afficher le résultat
        self.result_entry = tk.Entry(self.result_frame, font=("Monaco", 20), justify="right", state='readonly', bd=0)
        self.result_entry.pack(fill="both", expand=True)

        # Frame pour afficher l'historique
        self.history_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.history_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # Zone de texte avec défilement pour afficher l'historique des calculs
        self.history_text = scrolledtext.ScrolledText(self.history_frame, height=4, font=("Monaco", 14), state='disabled', bd=0, bg="#f0f0f0")
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Définition des couleurs pour les boutons
        self.button_colors = {
            "num": "#aaaaaa",  # Boutons numériques
            "op": "#8fc9e1",  # Boutons d'opérations
            "func": "#b39ddb",  # Boutons de fonctions trigo
            "eq": "#a5d6a7",  # Bouton d'égalité
            "del": "#ef9a9a",  # Boutons de suppression
            "pi": "#bbdefb",  # Bouton de pi
            "move": "#aaaaaa",  # Boutons de déplacement du curseur et parenthèses
            "quit": "#f44336"
        }

        # Liste de tuples contenant les informations sur chaque bouton : (texte, ligne, colonne, couleur)
        self.buttons = [
            ("7", 4, 0, "num", 1), ("8", 4, 1, "num", 1), ("9", 4, 2, "num", 1), ("DEL", 4, 3, "del", 1), ("C", 4, 4, "del", 1),
            ("4", 5, 0, "num", 1), ("5", 5, 1, "num", 1), ("6", 5, 2, "num", 1), ("←", 5, 3, "move", 1), ("→", 5, 4, "move", 1),
            ("1", 6, 0, "num", 1), ("2", 6, 1, "num", 1), ("3", 6, 2, "num", 1), ("×", 6, 3, "op", 1), ("÷", 6, 4, "op", 1),
            (".", 7, 0, "num", 1), ("0", 7, 1, "num", 1), ("π", 7, 2, "pi", 1), ("+", 7, 3, "op", 1), ("-", 7, 4, "op", 1),
            ("sin", 8, 0, "func", 1), ("cos", 8, 1, "func", 1), ("tan", 8, 2, "func", 1), ("√", 8, 3, "op", 1), ("^", 8, 4, "op", 1),
            ("(", 9, 0, "move", 1), (")", 9, 1, "move", 1),
            ("=", 9, 2, "eq", 2), ("QUITTER", 9, 4, "quit", 1)
        ]

        self.create_buttons()

        self.history = []
        self.cursor_position = 0

        # Configurer la grille pour rendre la fenêtre responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        for i in range(5):
            self.grid_columnconfigure(i, weight=1)

        # Centrer les widgets dans la fenêtre
        self.center_window()

        # Commencer à faire clignoter le curseur lorsque l'application démarre
        self.start_blinking()

    def battery_icon(self, percent):
        img = Image.new("RGBA", (22, 22), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(1, 6), (21, 16)], fill="black", outline="black")
        fill = int((percent / 100) * 16)
        draw.rectangle([(3, 8), (3 + fill, 14)], fill="white", outline="white")

        return img

    def update_status_bar(self):
        battery_percent = psutil.sensors_battery().percent
        battery_icon = self.battery_icon(battery_percent)
        tk_battery_icon = ImageTk.PhotoImage(battery_icon)
        current_time = datetime.now().strftime("%H:%M")

        # Obtenir la largeur actuelle de la frame principale
        frame_width = self.main_frame.winfo_width()

        # Calculer l'espacement en fonction de la largeur de la frame
        # Ajuster ce facteur pour changer l'espacement
        num_spaces = frame_width // 30
        tabs = "\u00A0" * num_spaces

        # Mettre à jour la barre d'état avec l'espacement dynamique
        self.status_bar.config(image=tk_battery_icon, compound=tk.LEFT,
                               text=f" {battery_percent}%{tabs}Calculatrice{tabs}{current_time}")
        self.status_bar.image = tk_battery_icon  # Garde une référence à l'image pour éviter la suppression par le garbage collector
        self.after(1, self.update_status_bar)  # Appel récursif pour mettre à jour la barre d'état

    def create_buttons(self):
        # Créer les boutons en fonction des informations dans self.buttons
        for (text, row, column, color, columnspan) in self.buttons:
            button = tk.Button(self, text=text, font=("Bahnschrift SemiBold", 15),
                               command=lambda t=text: self.on_button_click(t), relief="raised", bd=3, cursor="hand2",
                               bg=self.button_colors[color])
            # Place le bouton dans la grille avec les paramètres spécifiés
            button.grid(row=row, column=column, columnspan=columnspan, padx=15, pady=5, ipadx=10, ipady=10, sticky="nsew")

    def on_button_click(self, value):
        current_text = self.resultat.get()
        # Fonction appelée lorsqu'un bouton est cliqué
        if current_text.startswith("Erreur"):
            self.clear()  # Efface le contenu de la zone de saisie si un message d'erreur est affiché
            current_text = self.resultat.get()
            
        if value == "=":
            self.calculate()
        elif value == "C":
            self.clear()
        elif value == "←":
            self.move_cursor_left()
        elif value == "→":
            self.move_cursor_right()
        elif value == "DEL":
            self.delete_char()
        elif value == "QUITTER":
            self.clear()
            self.resultat.set("À bientôt 👋 Bisous 😘")
            self.cursor_position += len("À bientôt 👋 Bisous 😘")
            self.update_cursor_entry()
            self.cursor_entry.config(state='disabled')
            self.disw = True
            self.after(2000, self.destroy)
        else:
            left = current_text.rfind('(', 0, self.cursor_position)
            right = current_text.find(')', self.cursor_position)
            if value in ("sin", "cos", "tan", "√", "^") and left != -1 and right != -1:
                if value == "√":
                    value = "sqrt"
                # Si le curseur est entre des parenthèses, ajouter la fonction à cet endroit
                current_text = current_text[:self.cursor_position] + value + "()" + current_text[self.cursor_position:]
                self.cursor_position += len(value) + 1
            elif value == "π":
                current_text = current_text[:self.cursor_position] + "π" + current_text[self.cursor_position:]
                self.cursor_position += 1
            elif value == "^":
                current_text += "^()"
                # Place le curseur entre les parenthèses de ^()
                self.cursor_position += 2
            elif value in ("sin", "cos", "tan"):
                current_text += f"{value}()"
                # Place le curseur entre les parenthèses de la fonction trigonométrique
                self.cursor_position += len(value) + 1
            elif value == "√":
                current_text += "sqrt()"
                # Place le curseur entre les parenthèses de sqrt()
                self.cursor_position += len(value) + 4
            else:
                current_text = current_text[:self.cursor_position] + value + current_text[self.cursor_position:]
                self.cursor_position += 1
            self.resultat.set(current_text)
            self.update_cursor_entry()  # Met à jour l'affichage du curseur

    def remove_zeros_expression(self):
        # Liste pour stocker les éléments de l'expression après traitement
        elements = []
        # Chaîne de caractères pour stocker l'élément actuel en cours de construction
        current_element = ''

        # Parcourir chaque caractère dans l'expression actuelle
        for char in self.resultat.get():
            # Si le caractère est un chiffre ou un point décimal, ajouter au current_element
            if char.isdigit() or char == '.':
                current_element += char
            else:
                # Si le caractère est une opération ou une parenthèse, ajouter l'élément actuel à la liste d'éléments et réinitialiser current_element
                if current_element:
                    elements.append(current_element)
                    current_element = ''
                elements.append(char)

        # Ajouter le dernier élément à la liste d'éléments s'il en reste un
        if current_element:
            elements.append(current_element)

        # Traiter les éléments commençant par 0
        processed_elements = []
        for element in elements:
            # Si l'élément est composé uniquement de zéros, le remplacer par '0'
            if element.lstrip('0') == '':
                processed_element = '0'
            # Si l'élément commence par un zéro et n'est pas un nombre décimal, retirer les zéros superflus
            elif element.startswith('0') and len(element) > 1 and '.' not in element[1:]:
                processed_element = element.lstrip('0')
                # Si l'élément devient vide après suppression des zéros, le remplacer par '0'
                if processed_element == '':
                    processed_element = '0'
            else:
                # Sinon, conserver l'élément tel quel
                processed_element = element
            # Ajouter l'élément traité à la liste des éléments traités
            processed_elements.append(processed_element)

        # Fusionner les éléments traités en une seule chaîne et la retourner
        return ''.join(processed_elements)

    def insert_multiplication_sign(self, expression):
        # Insérer un signe × pour les multiplications implicites
        modified_expression = re.sub(r'(\d|\))(?=[^\d,.\)\^+\-×÷])', r'\1×', expression)
        return modified_expression

    def calculate(self):
        expression = self.remove_zeros_expression()
        expression = self.insert_multiplication_sign(expression)

        # Copie de l'expression pour la modifier sans altérer l'originale
        expression2 = expression

        # Remplacer les symboles spéciaux et les fonctions par leur équivalent en Python
        expression2 = expression2.replace("π", str(math.pi))
        expression2 = expression2.replace("×", "*")
        expression2 = expression2.replace("÷", "/")
        expression2 = expression2.replace("^", "**")
        for trigo in ("sin", "cos", "tan"):
            expression2 = expression2.replace(f"{trigo}", f"math.{trigo}")
        expression2 = expression2.replace("sqrt", "math.sqrt")

        try:
            # Évalue l'expression modifiée pour obtenir le résultat
            result = round(eval(expression2), 9)
        except ZeroDivisionError:
            # Gère les erreurs spécifiques
            self.resultat.set("Erreur: Division par zéro")
            self.cursor_position = len("Erreur: Division par zéro")
            self.update_cursor_entry()
            return
        except ArithmeticError:
            self.resultat.set("Erreur: Erreur arithmétique")
            self.cursor_position = len("Erreur: Erreur arithmétique")
            self.update_cursor_entry()
            return
        except ValueError:
            self.resultat.set("Erreur: Valeur invalide")
            self.cursor_position = len("Erreur: Valeur invalide")
            self.update_cursor_entry()
            return
        except OverflowError:
            self.resultat.set("Erreur: Résultat trop grand")
            self.cursor_position = len("Erreur: Résultat trop grand")
            self.update_cursor_entry()
            return
        except SyntaxError:
            self.resultat.set("Erreur: Syntaxe invalide")
            self.cursor_position = len("Erreur: Syntaxe invalide")
            self.update_cursor_entry()
            return
        except Exception:
            self.resultat.set("Erreur")
            self.cursor_position = len("Erreur")
            self.update_cursor_entry()
            return

        # Met à jour la zone de résultat avec le résultat obtenu
        self.resultat.set(result)
        self.result_entry.config(state='normal')
        self.result_entry.delete(0, tk.END)
        self.result_entry.insert(0, str(result))
        self.result_entry.config(state='readonly')

        # Ajoute l'expression et le résultat à l'historique
        self.history.append(expression + " = " + str(result))
        # Afficher l'historique
        self.update_history()

        # Positionne le curseur à la fin du résultat
        self.cursor_position = len(str(result))
        self.update_cursor_entry()

    def clear(self):
        # Efface l'entrée actuelle et réinitialise le curseur
        self.resultat.set("")
        self.cursorframe.set("")
        self.cursor_position = 0
        self.result_entry.config(state='normal')  # Active la modification de la zone de résultat
        self.result_entry.delete(0, tk.END)  # Efface le contenu de la zone de résultat
        self.result_entry.config(state='readonly')  # Désactive la modification de la zone de résultat

    def update_history(self):
        # Met à jour l'affichage de l'historique des calculs
        self.history_text.config(state='normal')
        self.history_text.delete(1.0, tk.END)
        reversed_history = reversed(self.history)
        for entry in reversed_history:
            self.history_text.insert(tk.END, entry + "\n") 
        self.history_text.config(state='disabled')

    def move_cursor_left(self):
        # Déplace le curseur d'un pas vers la gauche
        if self.cursor_position > 0:  # S'assure que le curseur ne soit pas déjà au début de la ligne
            # Si le curseur est juste après 'π', le déplacer juste avant 'π'
            if self.cursor_position < len(self.resultat.get()) and self.resultat.get()[self.cursor_position - 1] == "π":
                self.cursor_position -= 1
            else:
                self.cursor_position -= 1
            self.update_cursor_entry()  # Met à jour l'affichage du curseur

    def move_cursor_right(self):
        # Déplace le curseur d'un pas vers la droite
        if self.cursor_position < len(
                self.resultat.get()):  # S'assure que le curseur ne soit pas déjà à la fin de la ligne
            # Si le curseur est juste avant 'π', le déplacer juste après 'π'
            if self.resultat.get()[self.cursor_position] == "π":
                self.cursor_position += 1
            else:
                self.cursor_position += 1
            self.update_cursor_entry()  # Met à jour l'affichage du curseur

    def delete_char(self):
        # Supprime le caractère à gauche du curseur ou la fonction à gauche du curseur
        current_text = self.resultat.get()
        if self.cursor_position > 0:
            char_before_cursor = current_text[self.cursor_position - 1]
            if char_before_cursor == 't':
                current_text = current_text[:self.cursor_position - 4] + current_text[self.cursor_position:]
                self.cursor_position -= 4
            elif char_before_cursor in ('n', 's'):
                current_text = current_text[:self.cursor_position - 3] + current_text[self.cursor_position:]
                self.cursor_position -= 3
            elif char_before_cursor in ('o', 'i', 'a'):
                current_text = current_text[:self.cursor_position - 2] + current_text[self.cursor_position:]
                self.cursor_position -= 2
                self.move_cursor_right()
                current_text = current_text[:self.cursor_position - 1] + current_text[self.cursor_position:]
                self.cursor_position -= 1
            elif char_before_cursor in ('r'):
                current_text = current_text[:self.cursor_position - 3] + current_text[self.cursor_position:]
                self.cursor_position -= 3
                self.move_cursor_right()
                current_text = current_text[:self.cursor_position - 1] + current_text[self.cursor_position:]
                self.cursor_position -= 1
            elif char_before_cursor in ('q'):
                current_text = current_text[:self.cursor_position - 2] + current_text[self.cursor_position:]
                self.cursor_position -= 2
                self.move_cursor_right()
                self.move_cursor_right()
                current_text = current_text[:self.cursor_position - 2] + current_text[self.cursor_position:]
                self.cursor_position -= 2
            else:
                current_text = current_text[:self.cursor_position - 1] + current_text[self.cursor_position:]
                self.cursor_position -= 1
            self.resultat.set(current_text)
            self.update_cursor_entry()

    def update_cursor_entry(self):
        if self.disw == True:
            pass
        else:
            # Met à jour l'affichage de la zone de saisie avec le curseur
            current_text = self.resultat.get()
            # Affiche le curseur ou un espace selon sa visibilité actuelle
            cursor = "|" if self.cursor_visible else " "
            # Concatène le texte avant le curseur, le curseur lui-même et le texte après le curseur
            cursor_text = current_text[:self.cursor_position] + cursor + current_text[self.cursor_position:]
            self.cursor_entry.config(state='normal')
            self.cursor_entry.delete(0, tk.END)
            self.cursor_entry.insert(0, cursor_text)
            self.cursor_entry.config(state='readonly')

    def start_blinking(self):
        # Méthode récursive qui lance le clignotement du curseur
        self.blinking()  # Appelle la méthode blinking une fois immédiatement
        self.after(500, self.start_blinking)  # Appelle la méthode blinking toutes les 500 millisecondes

    def blinking(self):
        # Gère le clignotement du curseur
        if time() - self.blink_timer > 0.5:  # Si le temps écoulé dépasse 0.5 seconde
            self.blink_timer = time()  # Réinitialise le timer
            self.cursor_visible = not self.cursor_visible  # Inverse la visibilité du curseur
            self.update_cursor_entry()  # Met à jour l'affichage du curseur

    def center_window(self):
        # Centre la fenêtre de l'application sur l'écran
        self.update_idletasks()  # Met à jour la géométrie de la fenêtre
        width = self.winfo_width()  # Récupère la largeur de la fenêtre
        height = self.winfo_height()  # Récupère la hauteur de la fenêtre
        x = (self.winfo_screenwidth() // 2) - (width // 2)  # Calcule la position horizontale de la fenêtre
        y = (self.winfo_screenheight() // 2) - (height // 2)  # Calcule la position verticale de la fenêtre
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))  # Configure la géométrie de la fenêtre

        # Définir la taille minimale de la fenêtre
        min_width = width // 2
        min_height = height
        self.minsize(min_width, min_height)


if __name__ == "__main__":
    app = Calculatrice()
    app.mainloop()
