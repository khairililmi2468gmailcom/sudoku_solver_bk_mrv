import pygame
import time
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import random

# --- Inisialisasi Library ---
pygame.init()
pygame.font.init()
random.seed() 
root = tk.Tk()
root.withdraw()

# --- Konstanta Global ---
PADDING = 20
BOARD_SIZE = 540
SCREEN_WIDTH = BOARD_SIZE + 2 * PADDING
SCREEN_HEIGHT = BOARD_SIZE + 280
CELL_SIZE = BOARD_SIZE // 9

# Warna
GRID_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (245, 245, 245)
# Warna Angka & Status
INITIAL_NUMBER_COLOR = (0, 0, 0)
SOLVED_NUMBER_COLOR = (60, 60, 60)
USER_NUMBER_COLOR = (0, 0, 200)
INVALID_NUMBER_COLOR = (255, 0, 0)
UI_TEXT_COLOR = (50, 50, 50)
UI_LABEL_COLOR = (100, 100, 100)
STATUS_SUCCESS_COLOR = (0, 150, 0)
STATUS_FAIL_COLOR = (200, 0, 0)
# UI Lainnya
SELECTION_COLOR = (255, 0, 0)
BUTTON_COLOR = (0, 170, 0)
BUTTON_HOVER_COLOR = (0, 200, 0)
BUTTON_TEXT_COLOR = (255, 255, 255)
DISABLED_BUTTON_COLOR = (150, 150, 150)
# --- WARNA BARU: Untuk tombol level yang aktif ---
ACTIVE_LEVEL_BUTTON_COLOR = (0, 100, 0) 

# Font
FONT = pygame.font.SysFont("comicsans", 40)
FONT_MEDIUM = pygame.font.SysFont("comicsans", 18) # Ukuran font disesuaikan agar pas
FONT_SMALL = pygame.font.SysFont("comicsans", 16)
FONT_STATUS = pygame.font.SysFont("comicsans", 16)
FONT_UI_TEXT = pygame.font.SysFont("comicsans", 20, bold=True)
FONT_UI_LABEL = pygame.font.SysFont("comicsans", 14, bold=True)

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
        
        self.game_active = False
        self.game_start_time = 0
        self.game_elapsed_time = 0
        self.score = 0
        self.difficulty_multipliers = {
            "puzzle_mudah.txt": 1, "puzzle_menengah.txt": 2, 
            "puzzle_sulit.txt": 4, "puzzle_ahli.txt": 8, "puzzle_ekstrem.txt": 12
        }

        self.initial_board, self.board, self.invalid_cells = [0]*81, [0]*81, set()
        self.first_solution = None
        self.rows, self.cols, self.boxes = [0]*9, [0]*9, [0]*9
        self.clear_board(is_initial_load=True)

    def set_status(self, message, success=True, duration=5):
        self.status_text = message
        self.status_color = STATUS_SUCCESS_COLOR if success else STATUS_FAIL_COLOR
        self.status_timer = time.time() + duration

    def start_game_timer(self):
        self.game_active = True
        self.score = 0
        self.game_start_time = time.time()

    def create_buttons(self):
        buttons = {}
        y_pos = BOARD_SIZE + PADDING + 35
        
        puzzle_files = { "Mudah": "puzzle_mudah.txt", "Menengah": "puzzle_menengah.txt", "Sulit": "puzzle_sulit.txt", "Ahli": "puzzle_ahli.txt", "Ekstrem": "puzzle_ekstrem.txt" }
        btn_width, btn_height, btn_padding = 90, 35, 8
        start_x_levels = (SCREEN_WIDTH - (len(puzzle_files) * btn_width + (len(puzzle_files) - 1) * btn_padding)) // 2
        for i, (name, filename) in enumerate(puzzle_files.items()):
            x_pos = start_x_levels + i * (btn_width + btn_padding)
            # Menambahkan 'type' untuk membedakan jenis tombol
            buttons[name] = {'rect': pygame.Rect(x_pos, y_pos, btn_width, btn_height), 'file': filename, 'action': 'load', 'type': 'level'}
            
        y_pos_actions = y_pos + btn_height + 55
        action_btn_width, action_btn_height = 100, 45
        total_width_actions = 5 * action_btn_width + 4 * btn_padding
        action_start_x = (SCREEN_WIDTH - total_width_actions) // 2
        
        # --- PERBAIKAN UI: Mempersingkat teks tombol agar pas ---
        action_buttons = {
            "Solve": 'solve', "Solusi Lain": 'solve_another',
            "Reset": 'reset', "Kosongkan": 'clear', "Upload": 'upload'
        }
        
        for i, (name, action) in enumerate(action_buttons.items()):
            x_pos = action_start_x + i * (action_btn_width + btn_padding)
            buttons[name] = {'rect': pygame.Rect(x_pos, y_pos_actions, action_btn_width, action_btn_height), 'action': action, 'type': 'action'}

        return buttons
    
    def upload_file(self):
        root.deiconify(); root.lift(); root.focus_force()
        filepath = filedialog.askopenfilename(title="Pilih file puzzle Sudoku (*.txt)", filetypes=[("Text files", "*.txt")])
        root.withdraw()
        if filepath: self.load_grid(filepath)
        else: self.set_status("Pemilihan file dibatalkan.", success=False, duration=3)

    def clear_board(self, is_initial_load=False):
        self.initial_board = [0] * 81
        self.current_puzzle_name = "papan custom"
        self.reset_state()
        if not is_initial_load: self.set_status("Papan dikosongkan.")
        self.start_game_timer()
    
    def is_board_valid(self, board_to_check):
        self.invalid_cells.clear()
        rows, cols, boxes = [set() for _ in range(9)], [set() for _ in range(9)], [set() for _ in range(9)]
        is_valid = True
        for r in range(9):
            for c in range(9):
                num = board_to_check[r * 9 + c]
                if num == 0: continue
                b = (r // 3) * 3 + (c // 3)
                if num in rows[r] or num in cols[c] or num in boxes[b]: is_valid = False
                rows[r].add(num); cols[c].add(num); boxes[b].add(num)
        if not is_valid: self.find_and_set_all_invalid_cells(board_to_check)
        return is_valid

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
                for r_in_box in range(box_start_r, box_start_r + 3):
                    for c_in_box in range(box_start_c, box_start_c + 3):
                        if r_in_box*9+c_in_box > r*9+c and board_to_check[r_in_box*9+c_in_box] == num:
                           self.invalid_cells.add(r*9 + c); self.invalid_cells.add(r_in_box*9+c_in_box)
    
    def load_grid(self, filename):
        try:
            with open(filename, 'r') as f: lines = [line.strip() for line in f if line.strip()]
            if len(lines) != 9: raise ValueError(f"File harus memiliki 9 baris, ditemukan {len(lines)}.")
            grid_2d = []
            for line in lines:
                row_str = line.split()
                if len(row_str) != 9: raise ValueError(f"Setiap baris harus memiliki 9 angka, ditemukan {len(row_str)}.")
                row_int = [int(num) for num in row_str]
                if any(not (0 <= n <= 9) for n in row_int): raise ValueError("Angka dalam file harus antara 0 dan 9.")
                grid_2d.append(row_int)
            temp_board = [grid_2d[r][c] for r in range(9) for c in range(9)]
            if not self.is_board_valid(temp_board):
                self.invalid_cells.clear()
                raise ValueError("Puzzle di dalam file tidak valid.")
            self.initial_board = temp_board[:]
            self.current_puzzle_name = filename.split('/')[-1]
            self.reset_state()
            self.set_status(f"Puzzle '{self.current_puzzle_name}' dimuat.")
            self.start_game_timer()
        except Exception as e:
            self.clear_board()
            self.set_status(f"Gagal memuat: file tidak valid.", success=False)

    def reset_state(self):
        self.board = self.initial_board[:]
        self.solved = False; self.is_solving = False
        self.runtime = None; self.selected_cell = None
        self.first_solution = None
        self.is_board_valid(self.board)
        if self.current_puzzle_name != "papan custom": self.start_game_timer()

    def write_solution(self, filename):
        with open(filename, 'w') as f:
            for r in range(9):
                row_str = ' '.join(str(self.board[r*9 + c]) for c in range(9))
                f.write(row_str + '\n')
    
    def calculate_score(self):
        if self.game_elapsed_time == 0: self.score = 0; return
        multiplier = self.difficulty_multipliers.get(self.current_puzzle_name, 1)
        base_score = 100000 
        self.score = int((base_score / self.game_elapsed_time) * multiplier)

    def draw_all(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid(); self.draw_selection(); self.draw_ui_elements(); self.draw_status()
        pygame.display.update()

    def draw_grid(self):
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, GRID_COLOR, (PADDING, PADDING + i*CELL_SIZE), (PADDING + BOARD_SIZE, PADDING + i*CELL_SIZE), thick)
            pygame.draw.line(self.screen, GRID_COLOR, (PADDING + i*CELL_SIZE, PADDING), (PADDING + i*CELL_SIZE, PADDING + BOARD_SIZE), thick)
        for i in range(81):
            if self.board[i] != 0:
                r, c = i//9, i%9
                color = INITIAL_NUMBER_COLOR
                if i in self.invalid_cells: color = INVALID_NUMBER_COLOR
                elif self.solved and self.initial_board[i] == 0: color = SOLVED_NUMBER_COLOR
                elif self.initial_board[i] == 0: color = USER_NUMBER_COLOR
                text = FONT.render(str(self.board[i]), True, color)
                blit_pos = (PADDING + c*CELL_SIZE+(CELL_SIZE-text.get_width())/2, PADDING + r*CELL_SIZE+(CELL_SIZE-text.get_height())/2)
                self.screen.blit(text, blit_pos)

    def draw_selection(self):
        if self.selected_cell:
            r, c = self.selected_cell
            pygame.draw.rect(self.screen, SELECTION_COLOR, (PADDING + c*CELL_SIZE, PADDING + r*CELL_SIZE, CELL_SIZE, CELL_SIZE), 4)

    def draw_status(self):
        if time.time() < self.status_timer:
            text = FONT_STATUS.render(self.status_text, True, self.status_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, self.buttons['Mudah']['rect'].bottom + 18))
            self.screen.blit(text, text_rect)

    def draw_ui_elements(self):
        mouse_pos = pygame.mouse.get_pos()
        
        label_levels = FONT_UI_LABEL.render("PILIH TINGKAT KESULITAN", True, UI_LABEL_COLOR)
        self.screen.blit(label_levels, ((SCREEN_WIDTH - label_levels.get_width()) / 2, self.buttons['Mudah']['rect'].top - 22))
        label_actions = FONT_UI_LABEL.render("AKSI", True, UI_LABEL_COLOR)
        self.screen.blit(label_actions, ((SCREEN_WIDTH - label_actions.get_width()) / 2, self.buttons['Solve']['rect'].top - 22))

        for name, btn in self.buttons.items():
            rect = btn['rect']
            color = BUTTON_COLOR
            
            # --- PERBAIKAN UI: Logika pewarnaan tombol ---
            is_disabled = (name == "Solve" and (self.solved or self.is_solving)) or \
                          (name == "Solusi Lain" and (not self.first_solution or self.is_solving))
            
            # Beri warna khusus jika ini adalah tombol level yang aktif
            if btn['type'] == 'level' and btn.get('file') == self.current_puzzle_name:
                color = ACTIVE_LEVEL_BUTTON_COLOR
            elif is_disabled:
                color = DISABLED_BUTTON_COLOR
            elif rect.collidepoint(mouse_pos) and not self.is_solving:
                color = BUTTON_HOVER_COLOR

            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            
            # Tentukan font yang sesuai agar teks tidak keluar
            font_to_use = FONT_MEDIUM
            if rect.width < 100: # Tombol level lebih kecil
                 font_to_use = FONT_SMALL

            text = font_to_use.render(name, True, BUTTON_TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center) # Posisi teks tepat di tengah
            self.screen.blit(text, text_rect)
        
        y_pos_info = self.buttons['Solve']['rect'].bottom + 25
        if self.game_active: self.game_elapsed_time = time.time() - self.game_start_time
        minutes = int(self.game_elapsed_time // 60)
        seconds = int(self.game_elapsed_time % 60)
        timer_text_str = f"Waktu: {minutes:02d}:{seconds:02d}"
        timer_text = FONT_UI_TEXT.render(timer_text_str, True, UI_TEXT_COLOR)
        self.screen.blit(timer_text, (PADDING, y_pos_info))
        if self.runtime is not None:
            runtime_str = f"Runtime: {self.runtime:.4f} ms"
            runtime_text = FONT_UI_TEXT.render(runtime_str, True, UI_TEXT_COLOR)
            self.screen.blit(runtime_text, (SCREEN_WIDTH/2 - runtime_text.get_width()/2, y_pos_info))
        score_text_str = f"Skor: {self.score}"
        score_text = FONT_UI_TEXT.render(score_text_str, True, UI_TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - PADDING, y_pos_info))

    def solve(self, randomize=False, avoid_solution=None):
        max_attempts = 20 if randomize else 1
        for _ in range(max_attempts):
            self.board = self.initial_board[:] 
            self.rows, self.cols, self.boxes = [0]*9, [0]*9, [0]*9
            for i in range(81):
                if self.board[i] != 0:
                    val=self.board[i]; bit=1<<(val-1); r,c=i//9, i%9; b=(r//3)*3+c//3
                    self.rows[r]|=bit; self.cols[c]|=bit; self.boxes[b]|=bit
            if self._backtrack(randomize):
                if avoid_solution and self.board == avoid_solution: continue
                return True
        return False

    def _backtrack(self, randomize=False):
        min_candidates = 10
        best_cells = []
        for i in range(81):
            if self.board[i] == 0:
                r,c=i//9,i%9; b=(r//3)*3+c//3
                used = self.rows[r]|self.cols[c]|self.boxes[b]
                num_candidates = bin(ALL_CANDIDATES & ~used).count('1')
                if num_candidates < min_candidates:
                    min_candidates = num_candidates
                    best_cells = [i]
                elif num_candidates == min_candidates:
                    best_cells.append(i)
        
        if not best_cells: return True
        best_cell_idx = random.choice(best_cells) if randomize else best_cells[0]
            
        r,c=best_cell_idx//9,best_cell_idx%9; b=(r//3)*3+c//3
        candidates_mask = ALL_CANDIDATES & ~(self.rows[r]|self.cols[c]|self.boxes[b])
        
        candidates_list = []
        temp_mask = candidates_mask
        while temp_mask > 0:
            bit = temp_mask & -temp_mask
            candidates_list.append(bit)
            temp_mask -= bit
        
        if randomize: random.shuffle(candidates_list)
            
        for bit in candidates_list:
            num = bit.bit_length()
            self.board[best_cell_idx] = num
            self.rows[r]|=bit; self.cols[c]|=bit; self.boxes[b]|=bit
            if self._backtrack(randomize): return True
            self.rows[r]&=~bit; self.cols[c]&=~bit; self.boxes[b]&=~bit
            self.board[best_cell_idx]=0
        return False

    def handle_solve_action(self, find_another=False):
        if sum(self.initial_board) == 0 and sum(self.board) == 0:
            self.set_status("Papan kosong, tidak ada yang bisa diselesaikan.", success=False); return
        if self.invalid_cells:
            messagebox.showerror("Error", "Papan tidak valid."); return

        self.is_solving = True
        self.draw_all(); pygame.event.pump()
        start_perf = time.perf_counter()
        
        if find_another:
            solution_found = self.solve(randomize=True, avoid_solution=self.first_solution)
        else:
            solution_found = self.solve(randomize=False)

        end_perf = time.perf_counter()
        self.is_solving = False

        if solution_found:
            self.runtime = (end_perf-start_perf)*1000
            self.write_solution(OUTPUT_FILENAME)
            self.solved = True
            self.game_active = False
            if not find_another:
                self.first_solution = self.board[:]
                self.set_status(f"Solusi disimpan ke '{OUTPUT_FILENAME}'")
            else:
                self.set_status("Solusi alternatif ditemukan!")
        else:
            self.runtime = None
            self.board = self.initial_board[:] 
            self.is_board_valid(self.board)
            if find_another: self.set_status("Tidak ada solusi alternatif ditemukan.", success=False)
            else: self.set_status("Gagal: Tidak ada solusi untuk papan ini.", success=False)
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.is_solving:
                    pos = pygame.mouse.get_pos()
                    if PADDING < pos[0] < PADDING + BOARD_SIZE and PADDING < pos[1] < PADDING + BOARD_SIZE:
                        c,r = (pos[0] - PADDING) // CELL_SIZE, (pos[1] - PADDING) // CELL_SIZE
                        self.selected_cell = (r, c)
                    else:
                        self.selected_cell = None
                        for name, btn in self.buttons.items():
                            if btn['rect'].collidepoint(pos):
                                action = btn.get('action')
                                if action == 'load': self.load_grid(btn['file'])
                                elif action == 'reset': self.reset_state()
                                elif action == 'clear': self.clear_board()
                                elif action == 'upload': self.upload_file()
                                elif action == 'solve': self.handle_solve_action()
                                elif action == 'solve_another': self.handle_solve_action(find_another=True)
                                    
                if event.type == pygame.KEYDOWN and self.selected_cell and not self.solved:
                    r, c = self.selected_cell
                    idx = r*9+c
                    if not self.game_active and self.board[idx] == 0: self.start_game_timer()
                    if self.initial_board[idx]==0:
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            self.board[idx] = event.key - pygame.K_0
                            self.initial_board[idx] = self.board[idx]
                        elif event.key in [pygame.K_BACKSPACE, pygame.K_DELETE]:
                            self.board[idx] = 0
                            self.initial_board[idx] = 0
                        self.solved = False; self.runtime = None; self.first_solution = None
                        is_valid_now = self.is_board_valid(self.board)
                        if self.current_puzzle_name != "papan custom": self.current_puzzle_name = "papan editan"
                        if is_valid_now and 0 not in self.board:
                            self.game_active = False
                            self.calculate_score()
                            self.set_status(f"Selamat! Skor: {self.score}", duration=10)
            
            self.draw_all()
        pygame.quit()

if __name__ == "__main__":
    solver = SudokuSolver()
    try: solver.run()
    except (KeyboardInterrupt, SystemExit): print("\nProgram dihentikan oleh pengguna.")
    finally:
        pygame.quit()
        sys.exit()