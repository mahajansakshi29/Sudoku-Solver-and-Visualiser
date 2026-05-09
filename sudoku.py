import tkinter as tk
from tkinter import messagebox
from copy import deepcopy

from sudoku_generator import generate_puzzle 


#  BOARD LOGIC HELPERS


def is_valid(board, num, row, col):
    for c in range(9):
        if board[row][c] == num and c != col:
            return False
    for r in range(9):
        if board[r][col] == num and r != row:
            return False

    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br+3):
        for c in range(bc, bc+3):
            if board[r][c] == num and (r, c) != (row, col):
                return False
    return True


def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


# SOLVER WITH RECORDED STEPS (NO ANIM RECURSION)
def solve_with_steps(board, steps):
    """
    Standard backtracking solver that RECORDS every step in `steps`.
    Each step is ("place"/"backtrack", row, col, value).
    """
    empty = find_empty(board)
    if not empty:
        return True  

    r, c = empty
    for guess in range(1, 10):
        if is_valid(board, guess, r, c):
            steps.append(("place", r, c, guess))
            board[r][c] = guess

            if solve_with_steps(board, steps):
                return True

            # backtrack
            steps.append(("backtrack", r, c, 0))
            board[r][c] = 0

    return False


# CANDIDATE LOGIC

def compute_all_candidates(board):
    cand = [[set() for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for d in range(1, 10):
                    if is_valid(board, d, r, c):
                        cand[r][c].add(d)
    return cand


def find_naked_single(board, candidates):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0 and len(candidates[r][c]) == 1:
                val = next(iter(candidates[r][c]))
                msg = f"Naked single → Cell ({r+1},{c+1}) = {val}"
                return r, c, val, msg
    return None


def find_hidden_single_in_unit(board, candidates, cells, name):
    count = {d: [] for d in range(1, 10)}

    for (r, c) in cells:
        if board[r][c] == 0:
            for d in candidates[r][c]:
                count[d].append((r, c))

    for d in range(1, 10):
        if len(count[d]) == 1:
            r, c = count[d][0]
            msg = f"Hidden single in {name} → digit {d} at ({r+1},{c+1})"
            return r, c, d, msg

    return None


def find_hidden_single(board, candidates):
    # rows
    for r in range(9):
        cells = [(r, c) for c in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"row {r+1}")
        if res:
            return res

    # cols
    for c in range(9):
        cells = [(r, c) for r in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"column {c+1}")
        if res:
            return res

    # boxes
    for br in range(3):
        for bc in range(3):
            cells = [(r, c) for r in range(br*3, br*3+3)
                             for c in range(bc*3, bc*3+3)]
            res = find_hidden_single_in_unit(board, candidates, cells, f"box ({br+1},{bc+1})")
            if res:
                return res

    return None

# MAIN GAME GUI (GRID SCREEN)

class SudokuGUI:
    def __init__(self, root, initial_board=None):
        self.root = root
        self.root.title("Sudoku Game")
        self.root.configure(bg="#222831")

        self.board = deepcopy(initial_board) if initial_board else [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.pencil_mode = False

        self.solve_steps = []
        self.solve_running = False

        self.build_ui()

    # UI setup

    def build_ui(self):
        top = tk.Frame(self.root, bg="#222831")
        top.pack(pady=5)

        # BACK BUTTON
        tk.Button(top, text="◀ Back", bg="#444", fg="white",
                  font=("Arial", 12, "bold"),
                  command=self.go_back).grid(row=0, column=0, padx=10)

        self.pencil_label = tk.Label(top, text="Pencil: OFF",
                                     fg="white", bg="#222831", font=("Arial", 12))
        self.pencil_label.grid(row=0, column=1, padx=10)

        tk.Button(top, text="Pencil (P)", bg="#00adb5", fg="white",
                  command=self.toggle_pencil,
                  font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10)

        tk.Button(top, text="Hint", bg="#393e46", fg="white",
                  command=self.hint,
                  font=("Arial", 12)).grid(row=0, column=3, padx=10)

        tk.Button(top, text="Solve", bg="#00adb5", fg="white",
                  command=self.start_animation,
                  font=("Arial", 12, "bold")).grid(row=0, column=4, padx=10)

        tk.Button(top, text="Clear", bg="#393e46", fg="white",
                  command=self.clear,
                  font=("Arial", 12)).grid(row=0, column=5, padx=10)

        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.root.bind("<Key>", self.key_input)

    #  Back button 

    def go_back(self):
        """Return to main menu."""
        self.root.destroy()
        newroot = tk.Tk()
        MainMenu(newroot)
        newroot.mainloop()

    # ---------------- Drawing ---------------- #

    def redraw(self, event=None):
        self.canvas.delete("all")

        size = min(self.canvas.winfo_width(), self.canvas.winfo_height())
        self.cell = size / 9
        self.size = size

        self.x_offset = (self.canvas.winfo_width() - size)/2
        self.y_offset = (self.canvas.winfo_height() - size)/2

        self.draw_highlights()
        self.draw_numbers()
        self.draw_grid()

    def draw_grid(self):
        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
            # horizontal
            self.canvas.create_line(
                self.x_offset,
                self.y_offset + i*self.cell,
                self.x_offset + self.size,
                self.y_offset + i*self.cell,
                width=thick
            )
            # vertical
            self.canvas.create_line(
                self.x_offset + i*self.cell,
                self.y_offset,
                self.x_offset + i*self.cell,
                self.y_offset + self.size,
                width=thick
            )

    def draw_highlights(self):
        if not self.selected:
            return
        sr, sc = self.selected

        for r in range(9):
            for c in range(9):
                x1 = self.x_offset + c*self.cell
                y1 = self.y_offset + r*self.cell
                x2 = x1 + self.cell
                y2 = y1 + self.cell

                if (r, c) == (sr, sc):
                    color = "#4da3ff"
                elif r == sr or c == sc or (r//3 == sr//3 and c//3 == sc//3):
                    color = "#fff3b0"
                else:
                    continue
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def draw_numbers(self):
        for r in range(9):
            for c in range(9):
                x = self.x_offset + c*self.cell + self.cell/2
                y = self.y_offset + r*self.cell + self.cell/2
                val = self.board[r][c]

                if val != 0:
                    self.canvas.create_text(
                        x, y, text=str(val),
                        font=("Arial", int(self.cell/2)),
                        fill="black"
                    )
                elif self.candidates[r][c]:
                    text = "·".join(str(d) for d in sorted(self.candidates[r][c]))
                    self.canvas.create_text(
                        x, y, text=text,
                        font=("Arial", int(self.cell/5)),
                        fill="#444444"
                    )

    # ---------------- Input handling ---------------- #

    def handle_click(self, event):
        x, y = event.x, event.y
        col = int((x - self.x_offset)//self.cell)
        row = int((y - self.y_offset)//self.cell)

        if 0 <= row < 9 and 0 <= col < 9:
            self.selected = (row, col)
            self.redraw()

    def key_input(self, event):
        if not self.selected or self.solve_running:
            return
        r, c = self.selected
        ch = event.char

        if ch in ("p", "P"):
            self.toggle_pencil()
            return

        if ch == "0" or event.keysym in ("BackSpace", "Delete"):
            self.board[r][c] = 0
            self.candidates[r][c].clear()
            self.redraw()
            return

        if ch in "123456789":
            d = int(ch)
            if self.pencil_mode:
                if d in self.candidates[r][c]:
                    self.candidates[r][c].remove(d)
                else:
                    self.candidates[r][c].add(d)
            else:
                self.board[r][c] = d
                self.candidates[r][c].clear()
            self.redraw()

    # ---------------- Buttons ---------------- #

    def toggle_pencil(self):
        self.pencil_mode = not self.pencil_mode
        self.pencil_label.config(text=f"Pencil: {'ON' if self.pencil_mode else 'OFF'}")

    def clear(self):
        if self.solve_running:
            return
        self.board = [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.redraw()

    # ---------------- Solve animation (record + replay) ---------------- #

    def start_animation(self):
        if self.solve_running:
            return

        temp = deepcopy(self.board)
        steps = []
        solvable = solve_with_steps(temp, steps)

        if not solvable:
            messagebox.showerror("Error", "This puzzle cannot be solved.")
            return

        # steps now contains all place/backtrack moves; temp is fully solved
        self.solve_steps = steps
        self.solve_running = True
        self.play_steps(0)

    def play_steps(self, idx):
        if idx >= len(self.solve_steps):
            self.solve_running = False
            self.selected = None
            self.redraw()
            messagebox.showinfo("Solved!", "Sudoku solved with animation!")
            return

        action, r, c, val = self.solve_steps[idx]

        # apply action to visible board
        self.board[r][c] = val
        self.selected = (r, c)
        self.redraw()

        # adjust speed here (ms)
        self.root.after(20, lambda: self.play_steps(idx+1))

    # ---------------- Hint ---------------- #

    def hint(self):
        if self.solve_running:
            return

        temp = deepcopy(self.board)
        cand = compute_all_candidates(temp)

        res = find_naked_single(temp, cand)
        if not res:
            res = find_hidden_single(temp, cand)

        if not res:
            messagebox.showinfo("Hint", "No simple logical hint available.")
            return

        r, c, val, msg = res
        self.board[r][c] = val
        self.candidates[r][c].clear()
        self.selected = (r, c)
        self.redraw()
        messagebox.showinfo("Hint", msg)


#                     MAIN MENU SCREEN

class MainMenu:
    def __init__(self, root):
        self.root = root
        root.title("Sudoku")
        root.geometry("400x300")
        root.configure(bg="#222831")

        tk.Label(root, text="Sudoku", fg="white", bg="#222831",
                 font=("Arial", 28, "bold")).pack(pady=20)

        tk.Button(root, text="Play with your own input",
                  bg="#00adb5", fg="white",
                  font=("Arial", 16, "bold"),
                  command=self.start_custom).pack(pady=15)

        tk.Button(root, text="Solve a random Sudoku puzzle",
                  bg="#393e46", fg="white",
                  font=("Arial", 16, "bold"),
                  command=self.start_random).pack(pady=15)

    def start_custom(self):
        self.open_game([[0]*9 for _ in range(9)])

    def start_random(self):
        # tweak min_clues for difficulty (e.g., 32 easy, 28 medium, 24 hard)
        puzzle = generate_puzzle()  # uses default clues=30
        self.open_game(puzzle)

    def open_game(self, board):
        self.root.destroy()
        newroot = tk.Tk()
        SudokuGUI(newroot, board)
        newroot.mainloop()


#                        RUN APP

if __name__ == "__main__":
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()
