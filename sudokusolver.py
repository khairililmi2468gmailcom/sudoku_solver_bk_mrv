import pygame
import time
import sys
import tkinter as tk
from tkinter import messagebox

# --- Inisialisasi Library ---
pygame.init()
pygame.font.init()
root = tk.Tk()
root.withdraw()

# --- Konstanta Global ---
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 750
GRID_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
# Warna Angka & Status
INITIAL_NUMBER_COLOR = (0, 0, 0)
SOLVED_NUMBER_COLOR = (100, 100, 100)
USER_NUMBER_COLOR = (0, 0, 200)
INVALID_NUMBER_COLOR = (255, 0, 0)
RUNTIME_TEXT_COLOR = (50, 50, 50)
STATUS_SUCCESS_COLOR = (0, 150, 0)
STATUS_FAIL_COLOR = (200, 0, 0)
# UI Lainnya
SELECTION_COLOR = (255, 0, 0)
BUTTON_COLOR = (0, 170, 0)
BUTTON_HOVER_COLOR = (0, 200, 0)
BUTTON_TEXT_COLOR = (255, 255, 255)
DISABLED_BUTTON_COLOR = (150, 150, 150)
CELL_SIZE = SCREEN_WIDTH // 9
# Font
FONT = pygame.font.SysFont("comicsans", 40)
FONT_MEDIUM = pygame.font.SysFont("comicsans", 20)
FONT_SMALL = pygame.font.SysFont("comicsans", 16)
FONT_STATUS = pygame.font.SysFont("comicsans", 16)
FONT_RUNTIME = pygame.font.SysFont("comicsans", 18)

# Konstanta File & Bitmask
ALL_CANDIDATES = 0x1FF
OUTPUT_FILENAME = 'SolusiSudoku.txt'

class SudokuSolver:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MMAI Sudoku Solver")
        self.is_solving, self.solved = False, False
        self.runtime, self.selected_cell = None, None
        self.buttons = self.create_buttons()
        self.status_text, self.status_color, self.status_timer = "", STATUS_SUCCESS_COLOR, 0
        self.current_puzzle_name = "papan custom"
        self.initial_board, self.board, self.invalid_cells = [0]*81, [0]*81, set()
        self.rows, self.cols, self.boxes = [0]*9, [0]*9, [0]*9
        self.clear_board(is_initial_load=True)

    def set_status(self, message, success=True, duration=5):
        self.status_text = message
        self.status_color = STATUS_SUCCESS_COLOR if success else STATUS_FAIL_COLOR
        self.status_timer = time.time() + duration

    def create_buttons(self):
        buttons = {}
        # Tombol Level
        puzzle_files = { "Mudah": "puzzle_mudah.txt", "Menengah": "puzzle_menengah.txt", "Sulit": "puzzle_sulit.txt", "Ahli": "puzzle_ahli.txt", "Ekstrem": "puzzle_ekstrem.txt" }
        btn_width, btn_height, btn_padding = 90, 35, 15
        start_x_levels = (SCREEN_WIDTH - (len(puzzle_files) * btn_width + (len(puzzle_files) - 1) * btn_padding)) // 2
        y_pos_levels = SCREEN_WIDTH + 15
        for i, (name, filename) in enumerate(puzzle_files.items()):
            x_pos = start_x_levels + i * (btn_width + btn_padding)
            buttons[name] = {'rect': pygame.Rect(x_pos, y_pos_levels, btn_width, btn_height), 'file': filename, 'action': 'load'}
            
        # Tombol Aksi (Solve, Reset, Kosongkan)
        action_btn_width, action_btn_height = 120, 50
        total_width_actions = 3 * action_btn_width + 2 * btn_padding # 3 tombol
        action_start_x = (SCREEN_WIDTH - total_width_actions) // 2
        y_pos_actions = y_pos_levels + btn_height + 20
        buttons["Solve"] = {'rect': pygame.Rect(action_start_x, y_pos_actions, action_btn_width, action_btn_height), 'action': 'solve'}
        buttons["Reset"] = {'rect': pygame.Rect(action_start_x + action_btn_width + btn_padding, y_pos_actions, action_btn_width, action_btn_height), 'action': 'reset'}
        buttons["Kosongkan"] = {'rect': pygame.Rect(action_start_x + 2 * (action_btn_width + btn_padding), y_pos_actions, action_btn_width, action_btn_height), 'action': 'clear'}
        return buttons
    
    def clear_board(self, is_initial_load=False):
        self.initial_board = [0] * 81
        self.current_puzzle_name = "papan custom"
        self.reset_state()
        if not is_initial_load:
            self.set_status("Papan dikosongkan, siap untuk input baru.")
    
    def is_board_valid(self, board_to_check):
        self.invalid_cells.clear()
        rows, cols, boxes = [set() for _ in range(9)], [set() for _ in range(9)], [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                num = board_to_check[r * 9 + c]
                if num == 0: continue
                b = (r // 3) * 3 + (c // 3)
                if num in rows[r] or num in cols[c] or num in boxes[b]:
                    self.find_and_set_all_invalid_cells(board_to_check); return False
                rows[r].add(num); cols[c].add(num); boxes[b].add(num)
        return True

    def find_and_set_all_invalid_cells(self, board_to_check):
        self.invalid_cells.clear()
        for r in range(9):
            for c in range(9):
                num = board_to_check[r*9 + c]
                if num == 0: continue
                for c2 in range(c + 1, 9):
                    if board_to_check[r*9 + c2] == num: self.invalid_cells.add(r*9 + c); self.invalid_cells.add(r*9 + c2)
                for r2 in range(r + 1, 9):
                    if board_to_check[r2*9 + c] == num: self.invalid_cells.add(r*9 + c); self.invalid_cells.add(r2*9 + c)
                box_start_r, box_start_c = r - r % 3, c - c % 3
                for r_in_box in range(r, box_start_r + 3):
                    for c_in_box in range(box_start_c, box_start_c + 3):
                        if r_in_box*9+c_in_box > r*9+c and board_to_check[r_in_box*9+c_in_box] == num:
                           self.invalid_cells.add(r*9 + c); self.invalid_cells.add(r_in_box*9+c_in_box)
    
    def load_grid(self, filename):
        try:
            with open(filename, 'r') as f:
                grid_2d = [[int(num) for num in line.strip().split()] for line in f if line.strip()]
            temp_board = [grid_2d[r][c] for r in range(9) for c in range(9)]
            self.initial_board = temp_board[:]
            self.current_puzzle_name = filename.split('/')[-1]
            self.reset_state()
            self.set_status(f"Puzzle '{self.current_puzzle_name}' dimuat.")
        except Exception as e:
            print(f"Error memuat file {filename}: {e}")
            self.clear_board()
            self.set_status(f"Gagal memuat file '{filename}'.", success=False)

    def reset_state(self):
        self.board = self.initial_board[:]
        self.solved = False; self.is_solving = False
        self.runtime = None; self.selected_cell = None
        self.is_board_valid(self.board)

    def write_solution(self, filename):
        print(f"Menyimpan papan ke '{filename}'...")
        with open(filename, 'w') as f:
            for r in range(9):
                row_str = ' '.join(str(self.board[r*9 + c]) for c in range(9))
                f.write(row_str + '\n')
            f.flush()
        print("Penyimpanan berhasil.")

    def draw_all(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid(); self.draw_selection(); self.draw_ui_elements(); self.draw_status()
        pygame.display.update()

    def draw_grid(self):
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, GRID_COLOR, (0, i*CELL_SIZE), (SCREEN_WIDTH, i*CELL_SIZE), thick)
            pygame.draw.line(self.screen, GRID_COLOR, (i*CELL_SIZE, 0), (i*CELL_SIZE, SCREEN_WIDTH), thick)
        for i in range(81):
            if self.board[i] != 0:
                r, c = i//9, i%9
                color = INITIAL_NUMBER_COLOR
                if i in self.invalid_cells: color = INVALID_NUMBER_COLOR
                elif self.solved and self.initial_board[i] == 0: color = SOLVED_NUMBER_COLOR
                elif self.initial_board[i] == 0: color = USER_NUMBER_COLOR
                text = FONT.render(str(self.board[i]), True, color)
                self.screen.blit(text, (c*CELL_SIZE+(CELL_SIZE-text.get_width())/2, r*CELL_SIZE+(CELL_SIZE-text.get_height())/2))

    def draw_selection(self):
        if self.selected_cell:
            r, c = self.selected_cell
            pygame.draw.rect(self.screen, SELECTION_COLOR, (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE), 4)

    def draw_status(self):
        if time.time() < self.status_timer:
            text = FONT_STATUS.render(self.status_text, True, self.status_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 20))
            self.screen.blit(text, text_rect)

    def draw_ui_elements(self):
        mouse_pos = pygame.mouse.get_pos()
        for name, btn in self.buttons.items():
            rect = btn['rect']; color = BUTTON_COLOR
            is_disabled = (name == "Solve" and (self.solved or self.is_solving))
            if is_disabled: color = DISABLED_BUTTON_COLOR
            elif rect.collidepoint(mouse_pos) and not self.is_solving: color = BUTTON_HOVER_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            font = FONT_MEDIUM if len(name) < 9 else FONT_SMALL
            text = font.render(name, True, BUTTON_TEXT_COLOR)
            self.screen.blit(text, (rect.x+(rect.width-text.get_width())/2, rect.y+(rect.height-text.get_height())/2))
        
        if self.runtime is not None:
            text = FONT_RUNTIME.render(f"Runtime: {self.runtime:.4f} ms", True, RUNTIME_TEXT_COLOR)
            y_pos_runtime = self.buttons['Solve']['rect'].bottom + 30
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, y_pos_runtime))
            self.screen.blit(text, text_rect)

    def solve(self):
        self.initial_board = self.board[:]
        self.rows, self.cols, self.boxes = [0]*9, [0]*9, [0]*9
        for i in range(81):
            if self.board[i] != 0:
                val=self.board[i]; bit=1<<(val-1); r,c=i//9, i%9; b=(r//3)*3+c//3
                self.rows[r]|=bit; self.cols[c]|=bit; self.boxes[b]|=bit
        self.board_before_solve = self.board[:]
        return self._backtrack()

    def _backtrack(self):
        min_candidates, best_cell_idx = 10, -1
        for i in range(81):
            if self.board[i] == 0:
                r,c=i//9,i%9; b=(r//3)*3+c//3
                used = self.rows[r]|self.cols[c]|self.boxes[b]
                num_candidates = bin(ALL_CANDIDATES & ~used).count('1')
                if num_candidates < min_candidates:
                    min_candidates, best_cell_idx = num_candidates, i
        if best_cell_idx == -1: return True
        r,c=best_cell_idx//9,best_cell_idx%9; b=(r//3)*3+c//3
        candidates = ALL_CANDIDATES & ~(self.rows[r]|self.cols[c]|self.boxes[b])
        while candidates:
            bit = candidates & -candidates; num = bit.bit_length()
            self.board[best_cell_idx] = num
            self.rows[r]|=bit; self.cols[c]|=bit; self.boxes[b]|=bit
            if self._backtrack(): return True
            self.rows[r]&=~bit; self.cols[c]&=~bit; self.boxes[b]&=~bit
            self.board[best_cell_idx]=0; candidates&=~bit
        return False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.is_solving:
                    pos = pygame.mouse.get_pos()
                    if pos[1] < SCREEN_WIDTH: self.selected_cell=(pos[1]//CELL_SIZE, pos[0]//CELL_SIZE)
                    else:
                        self.selected_cell = None
                        for name, btn in self.buttons.items():
                            if btn['rect'].collidepoint(pos):
                                action = btn.get('action')
                                if action=='load': self.load_grid(btn['file'])
                                elif action=='reset': self.reset_state(); self.set_status(f"Papan direset ke puzzle '{self.current_puzzle_name}'.")
                                elif action=='clear': self.clear_board()
                                elif action=='solve' and not self.solved:
                                    if sum(self.board) == 0:
                                        self.set_status("Papan kosong, tidak ada yang bisa diselesaikan.", success=False); continue
                                    if self.invalid_cells:
                                        messagebox.showerror("Error", "Papan tidak valid (ada angka merah)."); continue
                                    self.is_solving=True; self.draw_all(); pygame.event.pump()
                                    start=time.perf_counter()
                                    solution_found = self.solve()
                                    end=time.perf_counter()
                                    if solution_found:
                                        self.runtime=(end-start)*1000
                                        self.write_solution(OUTPUT_FILENAME); self.solved=True
                                        self.set_status(f"Solusi untuk '{self.current_puzzle_name}' disimpan ke file '{OUTPUT_FILENAME}'")
                                    else:
                                        self.set_status(f"Gagal: Tidak ada solusi untuk '{self.current_puzzle_name}'.", success=False)
                                        self.board = self.board_before_solve[:]; self.is_board_valid(self.board)
                                    self.is_solving=False
                if event.type == pygame.KEYDOWN and self.selected_cell and not self.solved:
                    r,c=self.selected_cell; idx=r*9+c
                    if self.initial_board[idx]==0:
                        if pygame.K_1<=event.key<=pygame.K_9: self.board[idx]=event.key-pygame.K_0
                        elif event.key in [pygame.K_BACKSPACE, pygame.K_DELETE]: self.board[idx]=0
                        self.solved=False; self.runtime=None; self.is_board_valid(self.board)
                        self.current_puzzle_name="papan custom"
            self.draw_all()
        pygame.quit()

if __name__ == "__main__":
    solver = SudokuSolver()
    try:
        solver.run()
    except (KeyboardInterrupt, SystemExit):
        print("\nProgram dihentikan oleh pengguna.")
    finally:
        pygame.quit()
        sys.exit()