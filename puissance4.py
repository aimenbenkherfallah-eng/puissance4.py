import time
import tkinter as tk

L, C = 6, 7
VIDE, ROUGE, JAUNE = 0, 1, 2
ORDRE = [3, 2, 4, 1, 5, 0, 6]
WIN = 100000
INF = float("inf")


# les 69 fenetres de 4 cases (indices dans la grille aplatie)
def fenetres():
    f = []
    for r in range(L):
        for c in range(C):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if 0 <= r + 3 * dr < L and 0 <= c + 3 * dc < C:
                    f.append(tuple((r + k * dr) * C + c + k * dc for k in range(4)))
    return f


FENETRES = fenetres()


# regles du jeu
class Jeu:
    def __init__(self):
        self.g = [VIDE] * (L * C)
        self.h = [0] * C
        self.nb = 0
        self.joueur = ROUGE
        self.gagnant = VIDE
        self.ligne = []

    def coups(self):
        return [c for c in ORDRE if self.h[c] < L]

    def jouer(self, c):
        i = self.h[c] * C + c
        self.g[i] = self.joueur
        self.h[c] += 1
        self.nb += 1
        self.ligne = self.alignement(i)
        if self.ligne:
            self.gagnant = self.joueur
        self.joueur = 3 - self.joueur

    def annuler(self, c):
        self.h[c] -= 1
        i = self.h[c] * C + c
        self.joueur = self.g[i]
        self.g[i] = VIDE
        self.nb -= 1
        self.gagnant = VIDE
        self.ligne = []

    def alignement(self, i):
        r, c = divmod(i, C)
        p = self.g[i]
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            cases = [i]
            for s in (1, -1):
                rr, cc = r + s * dr, c + s * dc
                while 0 <= rr < L and 0 <= cc < C and self.g[rr * C + cc] == p:
                    cases.append(rr * C + cc)
                    rr += s * dr
                    cc += s * dc
            if len(cases) >= 4:
                return cases
        return []

    def fini(self):
        return self.gagnant != VIDE or self.nb == L * C


# heuristique : score par fenetre + bonus colonne centrale
def evaluer(j, ia):
    g = j.g
    adv = 3 - ia
    s = 0
    for a, b, c, d in FENETRES:
        x = (g[a], g[b], g[c], g[d])
        n1 = x.count(ia)
        n2 = x.count(adv)
        if n2 == 0:
            if n1 == 3:
                s += 5
            elif n1 == 2:
                s += 2
        elif n1 == 0:
            if n2 == 3:
                s -= 5
            elif n2 == 2:
                s -= 2
    for v in g[3::C]:
        if v == ia:
            s += 3
        elif v == adv:
            s -= 3
    return s


stats = {"noeuds": 0}


def terminal(j, prof, ia):
    if j.gagnant:
        return WIN + prof if j.gagnant == ia else -(WIN + prof)
    if j.nb == L * C:
        return 0
    return None


# minmax a profondeur limitee
def minmax(j, prof, est_max, ia):
    stats["noeuds"] += 1
    t = terminal(j, prof, ia)
    if t is not None:
        return t
    if prof == 0:
        return evaluer(j, ia)
    if est_max:
        m = -INF
        for c in j.coups():
            j.jouer(c)
            m = max(m, minmax(j, prof - 1, False, ia))
            j.annuler(c)
        return m
    m = INF
    for c in j.coups():
        j.jouer(c)
        m = min(m, minmax(j, prof - 1, True, ia))
        j.annuler(c)
    return m


# minmax avec elagage alpha-beta
def alphabeta(j, prof, alpha, beta, est_max, ia):
    stats["noeuds"] += 1
    t = terminal(j, prof, ia)
    if t is not None:
        return t
    if prof == 0:
        return evaluer(j, ia)
    if est_max:
        m = -INF
        for c in j.coups():
            j.jouer(c)
            m = max(m, alphabeta(j, prof - 1, alpha, beta, False, ia))
            j.annuler(c)
            alpha = max(alpha, m)
            if beta <= alpha:
                break
        return m
    m = INF
    for c in j.coups():
        j.jouer(c)
        m = min(m, alphabeta(j, prof - 1, alpha, beta, True, ia))
        j.annuler(c)
        beta = min(beta, m)
        if beta <= alpha:
            break
    return m


# choix du coup de l'ordinateur (max a la racine)
def choisir_coup(j, prof, algo):
    ia = j.joueur
    stats["noeuds"] = 1
    meilleur, coup = -INF, None
    for c in j.coups():
        j.jouer(c)
        if algo == "minmax":
            v = minmax(j, prof - 1, False, ia)
        else:
            v = alphabeta(j, prof - 1, meilleur, INF, False, ia)
        j.annuler(c)
        if v > meilleur:
            meilleur, coup = v, c
    return coup, meilleur


# interface
T = 80
NOMS = {ROUGE: "rouge", JAUNE: "jaune"}
COULEURS = {VIDE: "white", ROUGE: "red", JAUNE: "yellow"}


class App:
    def __init__(self, root):
        self.root = root
        root.title("puissance 4")
        top = tk.Frame(root)
        top.pack()
        self.mode = tk.StringVar(value="alphabeta")
        choix = (("humain vs humain", "hh"), ("ordi minmax", "minmax"),
                 ("ordi alpha-beta", "alphabeta"))
        for txt, val in choix:
            tk.Radiobutton(top, text=txt, variable=self.mode, value=val,
                           command=self.nouvelle).pack(side="left")
        tk.Label(top, text="profondeur").pack(side="left")
        self.prof = tk.IntVar(value=4)
        tk.Spinbox(top, from_=2, to=7, width=3, textvariable=self.prof).pack(side="left")
        tk.Button(top, text="nouvelle partie", command=self.nouvelle).pack(side="left")
        self.cv = tk.Canvas(root, width=C * T, height=L * T, bg="blue")
        self.cv.pack()
        self.cv.bind("<Button-1>", self.clic)
        self.info = tk.Label(root, text="", height=2)
        self.info.pack()
        self.nouvelle()

    def nouvelle(self):
        self.j = Jeu()
        self.occupe = False
        self.stat = ""
        self.dessiner()

    def message(self):
        j = self.j
        if j.gagnant:
            return NOMS[j.gagnant] + " a gagne"
        if j.nb == L * C:
            return "match nul"
        return "au tour de " + NOMS[j.joueur]

    def dessiner(self):
        self.cv.delete("all")
        for i, v in enumerate(self.j.g):
            r, c = divmod(i, C)
            x, y = c * T, (L - 1 - r) * T
            gag = i in self.j.ligne
            self.cv.create_oval(x + 8, y + 8, x + T - 8, y + T - 8, fill=COULEURS[v],
                                outline="black" if gag else "blue", width=5 if gag else 1)
        self.info.config(text=self.message() + "\n" + self.stat)

    def clic(self, e):
        c = e.x // T
        if self.occupe or self.j.fini() or c not in self.j.coups():
            return
        self.jouer(c)
        if self.mode.get() != "hh" and not self.j.fini():
            self.occupe = True
            self.info.config(text="l'ordi reflechit...")
            self.root.after(50, self.tour_ordi)

    def jouer(self, c):
        self.j.jouer(c)
        self.dessiner()

    def tour_ordi(self):
        t = time.time()
        c, v = choisir_coup(self.j, self.prof.get(), self.mode.get())
        dt = time.time() - t
        self.stat = "ordi : colonne %d, valeur %s, %d noeuds, %.2f s" % (
            c + 1, v, stats["noeuds"], dt)
        self.occupe = False
        self.jouer(c)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
