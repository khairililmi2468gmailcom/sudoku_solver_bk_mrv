import pygame
import time
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import random

# Inisialisasi Library 
pygame.init()
pygame.font.init()
random.seed() 
root = tk.Tk()
root.withdraw()

# Konstanta Global & Desain Modern 
PADDING = 20
BOARD_SIZE = 540
SCREEN_WIDTH = BOARD_SIZE + 2 * PADDING
SCREEN_HEIGHT = BOARD_SIZE + 280
CELL_SIZE = BOARD_SIZE // 9

# Palet Warna "Mewah & Modern" (Dark Mode)
BACKGROUND_COLOR = (18, 18, 18)        # Abu-abu sangat gelap
GRID_COLOR = (60, 60, 60)              # Garis grid abu-abu
BOARD_BG_COLOR = (30, 30, 30)          # Latar belakang papan
INITIAL_NUMBER_COLOR = (230, 230, 230) # Putih gading
USER_NUMBER_COLOR = (66, 135, 245)     # Biru cerah
SOLVED_NUMBER_COLOR = (150, 150, 150)   # Abu-abu
INVALID_NUMBER_COLOR = (255, 80, 80)     # Merah

# Warna UI
SELECTION_COLOR = (255, 215, 0)        # Emas untuk seleksi
BUTTON_OUTLINE_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (255, 215, 0)     # Emas saat di-hover
BUTTON_TEXT_COLOR = (230, 230, 230)
ACTIVE_BUTTON_FILL = (255, 215, 0)     # Isian Emas untuk tombol aktif
ACTIVE_BUTTON_TEXT = (18, 18, 18)      # Teks hitam untuk tombol aktif
DISABLED_BUTTON_COLOR = (40, 40, 40)
STATUS_SUCCESS_COLOR = (0, 200, 100)
STATUS_FAIL_COLOR = (255, 100, 100)

# Font STABIL (Comicsans) dengan ukuran yang disesuaikan
FONT = pygame.font.SysFont("comicsans", 45)
FONT_MEDIUM = pygame.font.SysFont("comicsans", 20, bold=True)
FONT_SMALL = pygame.font.SysFont("comicsans", 18, bold=True)
FONT_STATUS = pygame.font.SysFont("comicsans", 18)
FONT_UI_TEXT = pygame.font.SysFont("comicsans", 22, bold=True)
FONT_UI_LABEL = pygame.font.SysFont("comicsans", 15, bold=True)

# Konstanta File & Bitmask
ALL_CANDIDATES = 0x1FF
OUTPUT_FILENAME = 'SolusiSudoku.txt'

class SudokuSolver:
    def __init__(self):
        #  Inisialisasi Window dan Variabel Utama 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MMAI Sudoku Solver")
        
        # Variabel state untuk mengontrol alur program
        self.is_solving, self.solved = False, False
        self.runtime, self.selected_cell = None, None
        
        # Membuat semua tombol dan UI
        self.buttons = self.create_buttons()
        self.status_text, self.status_color, self.status_timer = "", STATUS_SUCCESS_COLOR, 0
        self.current_puzzle_name = "papan custom"
        
        # Variabel untuk mode permainan (waktu & skor)
        self.game_active = False
        self.game_start_time = 0
        self.game_elapsed_time = 0
        self.score = 0
        self.difficulty_multipliers = {
            "puzzle_mudah.txt": 1, "puzzle_menengah.txt": 2.5, 
            "puzzle_sulit.txt": 5, "puzzle_ahli.txt": 10, "puzzle_ekstrem.txt": 20
        }

        # Papan Sudoku dan data-datanya
        self.initial_board, self.board, self.invalid_cells = [0]*81, [0]*81, set()
        self.first_solution = None
        self.rows, self.cols, self.boxes = [0]*9, [0]*9, [0]*9
        self.clear_board(is_initial_load=True)

    def set_status(self, message, success=True, duration=5):
        # Menampilkan pesan status sementara di layar
        self.status_text = message
        self.status_color = STATUS_SUCCESS_COLOR if success else STATUS_FAIL_COLOR
        self.status_timer = time.time() + duration

    def start_game_timer(self):
        self.game_active = True
        self.score = 0
        self.game_start_time = time.time()

    def create_buttons(self):
        buttons = {}
        y_pos = BOARD_SIZE + PADDING + 45
        
        puzzle_files = { "Mudah": "puzzle_mudah.txt", "Menengah": "puzzle_menengah.txt", "Sulit": "puzzle_sulit.txt", "Ahli": "puzzle_ahli.txt", "Ekstrem": "puzzle_ekstrem.txt" }
        btn_width, btn_height, btn_padding = 90, 35, 8
        start_x_levels = (SCREEN_WIDTH - (len(puzzle_files) * btn_width + (len(puzzle_files) - 1) * btn_padding)) // 2
        for i, (name, filename) in enumerate(puzzle_files.items()):
            x_pos = start_x_levels + i * (btn_width + btn_padding)
            buttons[name] = {'rect': pygame.Rect(x_pos, y_pos, btn_width, btn_height), 'file': filename, 'action': 'load', 'type': 'level'}
            
        y_pos_actions = y_pos + btn_height + 55
        action_btn_width, action_btn_height = 100, 45
        total_width_actions = 5 * action_btn_width + 4 * btn_padding
        action_start_x = (SCREEN_WIDTH - total_width_actions) // 2
        
        action_buttons = { "Solve": 'solve', "Solusi Lain": 'solve_another', "Reset": 'reset', "Kosongkan": 'clear', "Upload": 'upload' }
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
        # Fungsi untuk memuat puzzle dari file .txt, lengkap dengan validasi
        try:
            with open(filename, 'r') as f: lines = [line.strip() for line in f if line.strip()]
            if len(lines) != 9: raise ValueError("File harus 9 baris.")
            grid_2d = [[int(num) for num in line.split()] for line in lines]
            temp_board = [num for row in grid_2d for num in row]
            if not self.is_board_valid(temp_board):
                self.invalid_cells.clear(); raise ValueError("Puzzle di file tidak valid.")
            self.initial_board = temp_board[:]
            self.current_puzzle_name = filename.split('/')[-1]
            self.reset_state()
            self.set_status(f"Puzzle '{self.current_puzzle_name}' dimuat.")
            self.start_game_timer()
        except Exception as e:
            self.clear_board(); self.set_status(f"Gagal memuat file.", success=False)

    def reset_state(self):
        # Mengembalikan papan ke kondisi awal puzzle
        self.board = self.initial_board[:]
        self.solved = False; self.is_solving = False
        self.runtime = None; self.selected_cell = None
        self.first_solution = None
        self.is_board_valid(self.board)
        if self.current_puzzle_name != "papan custom": self.start_game_timer()

    def write_solution(self, filename):
        with open(filename, 'w') as f:
            for r in range(9):
                f.write(' '.join(str(self.board[r*9 + c]) for c in range(9)) + '\n')
    
    def calculate_score(self, solved_by_ai=False):
        # Menghitung skor berdasarkan mode: AI (cepat) atau manual (lama)
        multiplier = self.difficulty_multipliers.get(self.current_puzzle_name, 1)
        base_score = 100000 
        if solved_by_ai:
            if self.runtime and self.runtime > 0:
                self.score = int((base_score / (self.runtime * 10)) * multiplier)
            else: self.score = 0
        else:
            if self.game_elapsed_time > 0:
                self.score = int((base_score / self.game_elapsed_time) * multiplier)
            else: self.score = 0

    def draw_all(self):
        # Fungsi utama yang dipanggil setiap frame untuk menggambar semua elemen
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, BOARD_BG_COLOR, (PADDING, PADDING, BOARD_SIZE, BOARD_SIZE))
        self.draw_grid(); self.draw_selection(); self.draw_ui_elements(); self.draw_status()
        pygame.display.update()

    def draw_grid(self):
        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
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
                blit_pos = (PADDING+c*CELL_SIZE+(CELL_SIZE-text.get_width())/2, PADDING+r*CELL_SIZE+(CELL_SIZE-text.get_height())/2)
                self.screen.blit(text, blit_pos)

    def draw_selection(self):
        if self.selected_cell:
            r, c = self.selected_cell
            pygame.draw.rect(self.screen, SELECTION_COLOR, (PADDING + c*CELL_SIZE, PADDING + r*CELL_SIZE, CELL_SIZE, CELL_SIZE), 4)

    def draw_status(self):
        if time.time() < self.status_timer:
            text = FONT_STATUS.render(self.status_text, True, self.status_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, self.buttons['Mudah']['rect'].top - 25))
            self.screen.blit(text, text_rect)

    def draw_ui_elements(self):
        # Menggambar semua elemen antarmuka seperti tombol, teks, skor, dll.
        mouse_pos = pygame.mouse.get_pos()
        
        # Gambar label
        label_levels = FONT_UI_LABEL.render("TINGKAT KESULITAN", True, GRID_COLOR)
        self.screen.blit(label_levels, (PADDING, self.buttons['Mudah']['rect'].top - 25))
        label_actions = FONT_UI_LABEL.render("AKSI", True, GRID_COLOR)
        self.screen.blit(label_actions, (PADDING, self.buttons['Solve']['rect'].top - 25))

        # Gambar semua tombol dengan logikanya (hover, aktif, disabled)
        for name, btn in self.buttons.items():
            rect = btn['rect']
            is_hovered = rect.collidepoint(mouse_pos)
            is_disabled = (name == "Solve" and (self.solved or self.is_solving)) or \
                          (name == "Solusi Lain" and (not self.first_solution or self.is_solving))
            is_active_level = btn['type'] == 'level' and btn.get('file') == self.current_puzzle_name

            if is_active_level:
                pygame.draw.rect(self.screen, ACTIVE_BUTTON_FILL, rect, border_radius=5)
                text_color = ACTIVE_BUTTON_TEXT
            elif is_disabled:
                pygame.draw.rect(self.screen, DISABLED_BUTTON_COLOR, rect, border_radius=5)
                text_color = BUTTON_OUTLINE_COLOR
            else:
                text_color = BUTTON_TEXT_COLOR
                border_color = BUTTON_HOVER_COLOR if is_hovered else BUTTON_OUTLINE_COLOR
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)

            font_to_use = FONT_MEDIUM if btn['type'] == 'action' else FONT_SMALL
            text = font_to_use.render(name, True, text_color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
        
        # Gambar informasi di bagian bawah (Waktu, Skor, Runtime)
        y_pos_info = self.buttons['Solve']['rect'].bottom + 25
        if self.game_active: self.game_elapsed_time = time.time() - self.game_start_time
        minutes, seconds = int(self.game_elapsed_time//60), int(self.game_elapsed_time%60)
        timer_text = FONT_UI_TEXT.render(f"{minutes:02d}:{seconds:02d}", True, INITIAL_NUMBER_COLOR)
        self.screen.blit(FONT_UI_LABEL.render("WAKTU", True, GRID_COLOR), (PADDING, y_pos_info))
        self.screen.blit(timer_text, (PADDING, y_pos_info + 20))
        
        score_text = FONT_UI_TEXT.render(f"{self.score}", True, SELECTION_COLOR)
        score_label = FONT_UI_LABEL.render("SKOR", True, GRID_COLOR)
        self.screen.blit(score_label, (SCREEN_WIDTH/2 - score_label.get_width()/2, y_pos_info))
        self.screen.blit(score_text, (SCREEN_WIDTH/2 - score_text.get_width()/2, y_pos_info + 20))
        
        if self.runtime is not None:
            runtime_text = FONT_UI_TEXT.render(f"{self.runtime:.2f} ms", True, INITIAL_NUMBER_COLOR)
            runtime_label = FONT_UI_LABEL.render("RUNTIME", True, GRID_COLOR)
            self.screen.blit(runtime_label, (SCREEN_WIDTH-PADDING-runtime_label.get_width(), y_pos_info))
            self.screen.blit(runtime_text, (SCREEN_WIDTH-PADDING-runtime_text.get_width(), y_pos_info + 20))

    def solve(self, randomize=False, avoid_solution=None):
        # Fungsi persiapan sebelum memanggil algoritma backtracking.
        # Mengatur jumlah percobaan dan me-reset state papan.
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
        #  Inti Algoritma Backtracking 

        # 1. Cari sel terbaik untuk diisi (heuristik Minimum Remaining Values)
        min_candidates, best_cells = 10, []
        for i in range(81):
            if self.board[i] == 0:
                r,c=i//9,i%9; b=(r//3)*3+c//3
                used = self.rows[r]|self.cols[c]|self.boxes[b]
                num_candidates = bin(ALL_CANDIDATES & ~used).count('1')
                if num_candidates < min_candidates:
                    min_candidates, best_cells = num_candidates, [i]
                elif num_candidates == min_candidates: best_cells.append(i)
        
        if not best_cells: return True # Basis rekursi: tidak ada sel kosong, puzzle selesai.

        # Pilih sel dari daftar sel terbaik (acak jika mencari solusi lain)
        best_cell_idx = random.choice(best_cells) if randomize else best_cells[0]
            
        # 2. Dapatkan semua kandidat angka yang valid untuk sel tersebut
        r,c=best_cell_idx//9,best_cell_idx%9; b=(r//3)*3+c//3
        candidates_mask = ALL_CANDIDATES & ~(self.rows[r]|self.cols[c]|self.boxes[b])
        
        candidates_list = []
        temp_mask = candidates_mask
        while temp_mask > 0:
            bit = temp_mask & -temp_mask; candidates_list.append(bit); temp_mask -= bit
        if randomize: random.shuffle(candidates_list)
        
        # 3. Coba setiap kandidat satu per satu
        for bit in candidates_list:
            num = bit.bit_length()
            self.board[best_cell_idx] = num
            self.rows[r]|=bit; self.cols[c]|=bit; self.boxes[b]|=bit
            
            # Panggil diri sendiri untuk sel berikutnya (rekursi)
            if self._backtrack(randomize): return True
            
            # Jika panggilan di atas gagal (jalan buntu), batalkan pilihan dan coba kandidat lain
            self.rows[r]&=~bit; self.cols[c]&=~bit; self.boxes[b]&=~bit
            self.board[best_cell_idx]=0
            
        return False # Jika semua kandidat gagal, kembali ke panggilan sebelumnya

    def handle_solve_action(self, find_another=False):
        # Fungsi yang dipanggil oleh tombol. Mengelola proses solve dan menampilkan hasilnya.
        if sum(self.initial_board) == 0 and sum(self.board) == 0:
            self.set_status("Papan kosong, tidak bisa diselesaikan.", success=False); return
        if self.invalid_cells:
            messagebox.showerror("Error", "Papan tidak valid."); return

        self.is_solving = True
        self.draw_all(); pygame.event.pump()
        start_perf = time.perf_counter()
        
        # Memutuskan apakah akan mencari solusi pertama (cepat) atau solusi lain (acak)
        solution_found = self.solve(randomize=find_another, avoid_solution=self.first_solution if find_another else None)
        
        end_perf = time.perf_counter()
        self.is_solving = False

        if solution_found:
            self.runtime = (end_perf-start_perf)*1000
            self.write_solution(OUTPUT_FILENAME)
            self.solved = True
            self.game_active = False
            self.calculate_score(solved_by_ai=True) # Hitung skor untuk AI
            if not find_another:
                self.first_solution = self.board[:]
                self.set_status(f"Solusi ditemukan! Skor: {self.score}")
            else:
                self.set_status(f"Solusi alternatif ditemukan! Skor: {self.score}")
        else:
            self.runtime = None; self.board = self.initial_board[:]; self.is_board_valid(self.board)
            if find_another: self.set_status("Tidak ada solusi alternatif.", success=False)
            else: self.set_status("Gagal: Tidak ada solusi.", success=False)
    
    def run(self):
        #  LOOP UTAMA PROGRAM 
        # Terus berjalan selama pengguna belum menutup window.
        running = True
        while running:
            # 1. Tangani Input dari Pengguna
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                # Menangani klik mouse pada papan dan tombol
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
                # Menangani input keyboard untuk mengisi angka                                    
                if event.type == pygame.KEYDOWN and self.selected_cell and not self.solved:
                    r, c = self.selected_cell
                    idx = r*9+c
                    if not self.game_active and self.board[idx] == 0: self.start_game_timer()
                    if self.initial_board[idx]==0:
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            self.board[idx] = event.key - pygame.K_0
                            self.initial_board[idx] = self.board[idx]
                        elif event.key in [pygame.K_BACKSPACE, pygame.K_DELETE]:
                            self.board[idx] = 0; self.initial_board[idx] = 0
                        self.solved = False; self.runtime = None; self.first_solution = None
                        is_valid_now = self.is_board_valid(self.board)
                        if self.current_puzzle_name != "papan custom": self.current_puzzle_name = "papan editan"
                        if is_valid_now and 0 not in self.board:
                            self.game_active = False
                            self.calculate_score(solved_by_ai=False)
                            self.set_status(f"Selamat! Skor akhir Anda: {self.score}", duration=10)
            # 2. Gambar Ulang Tampilan           
            self.draw_all()
        # 3. Keluar dari Program
        pygame.quit()

if __name__ == "__main__":
    solver = SudokuSolver()
    try: solver.run()
    except (KeyboardInterrupt, SystemExit): print("\nProgram dihentikan oleh pengguna.")
    finally:
        pygame.quit()
        sys.exit()