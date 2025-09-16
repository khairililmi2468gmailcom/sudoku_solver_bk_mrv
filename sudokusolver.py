import pygame
import time

# Inisialisasi Pygame
pygame.init()
pygame.font.init()

# --- Konstanta Global ---
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 680 
GRID_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
SOLVED_NUMBER_COLOR = (100, 100, 100)
INITIAL_NUMBER_COLOR = (0, 0, 0)
BUTTON_COLOR = (0, 170, 0)
BUTTON_HOVER_COLOR = (0, 200, 0)
BUTTON_TEXT_COLOR = (255, 255, 255)
DISABLED_BUTTON_COLOR = (150, 150, 150)
CELL_SIZE = SCREEN_WIDTH // 9
FONT = pygame.font.SysFont("comicsans", 40)
FONT_MEDIUM = pygame.font.SysFont("comicsans", 20)
FONT_SMALL = pygame.font.SysFont("comicsans", 16)

# Konstanta untuk bitmask, 9 bit pertama disetel ke 1 (merepresentasikan angka 1-9)
ALL_CANDIDATES = 0x1FF 

class SudokuSolver:
    def __init__(self):
        # UI State
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MMAI Sudoku Solver (Bitmask & MRV)")
        self.is_solving = False
        self.solved = False
        self.runtime = None
        self.buttons = self.create_buttons()
        
        # Solver State
        self.board = [0] * 81
        self.initial_board = [0] * 81
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9
        
    def create_buttons(self):
        buttons = {}
        puzzle_files = { "Mudah": "puzzle_mudah.txt", "Menengah": "puzzle_menengah.txt", "Sulit": "puzzle_sulit.txt", "Ahli": "puzzle_ahli.txt", "Ekstrem": "puzzle_ekstrem.txt" }
        btn_width, btn_height, btn_padding = 90, 35, 15
        start_x = (SCREEN_WIDTH - (len(puzzle_files) * btn_width + (len(puzzle_files) - 1) * btn_padding)) // 2
        y_pos = SCREEN_WIDTH + 20
        for i, (name, filename) in enumerate(puzzle_files.items()):
            x_pos = start_x + i * (btn_width + btn_padding); buttons[name] = {'rect': pygame.Rect(x_pos, y_pos, btn_width, btn_height), 'file': filename, 'action': 'load'}
        action_btn_width, action_btn_height = 120, 50; total_width = 2 * action_btn_width + btn_padding; action_start_x = (SCREEN_WIDTH - total_width) // 2; action_y_pos = y_pos + btn_height + 20
        buttons["Solve"] = {'rect': pygame.Rect(action_start_x, action_y_pos, action_btn_width, action_btn_height), 'action': 'solve'}; buttons["Reset"] = {'rect': pygame.Rect(action_start_x + action_btn_width + btn_padding, action_y_pos, action_btn_width, action_btn_height), 'action': 'reset'}
        return buttons

    def load_grid(self, filename):
        """Hanya memuat data dari file dan memanggil reset."""
        try:
            with open(filename, 'r') as f:
                grid_2d = [[int(num) for num in line.split()] for line in f]
            
            # Simpan puzzle awal dan langsung panggil reset untuk setup state
            self.initial_board = [grid_2d[r][c] for r in range(9) for c in range(9)]
            self.reset_state() 
            print(f"Puzzle '{filename}' berhasil dimuat.")
        except FileNotFoundError:
            print(f"Error: File '{filename}' tidak ditemukan. Memuat papan kosong.")
            self.initial_board = [0] * 81
            self.reset_state()

    def reset_state(self):
        """
        Mereset SEMUA state solver ke kondisi awal, termasuk bitmask.
        Ini adalah fungsi yang diperbaiki.
        """
        # Reset papan visual
        self.board = self.initial_board[:]
        
        # Reset UI flags
        self.solved = False
        self.is_solving = False
        self.runtime = None
        
        # *** FIX UTAMA: Inisialisasi ulang bitmask dari papan awal ***
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9
        for i in range(81):
            if self.board[i] != 0:
                val = self.board[i]
                bit = 1 << (val - 1)
                r, c = i // 9, i % 9
                b = (r // 3) * 3 + c // 3
                self.rows[r] |= bit
                self.cols[c] |= bit
                self.boxes[b] |= bit

    def write_solution(self, filename):
        with open(filename, 'w') as f:
            for r in range(9):
                row_str = ' '.join(str(self.board[r*9 + c]) for c in range(9))
                f.write(row_str + '\n')

    def draw_all(self):
        self.screen.fill(BACKGROUND_COLOR); self.draw_grid(); self.draw_ui_elements(); pygame.display.update()

    def draw_grid(self):
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, GRID_COLOR, (0, i * CELL_SIZE), (SCREEN_WIDTH, i * CELL_SIZE), thick); pygame.draw.line(self.screen, GRID_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, SCREEN_WIDTH), thick)
        for i in range(81):
            if self.board[i] != 0:
                r, c = i // 9, i % 9
                color = INITIAL_NUMBER_COLOR if self.initial_board[i] != 0 else SOLVED_NUMBER_COLOR
                text = FONT.render(str(self.board[i]), True, color); self.screen.blit(text, (c * CELL_SIZE + (CELL_SIZE - text.get_width()) / 2, r * CELL_SIZE + (CELL_SIZE - text.get_height()) / 2))

    def draw_ui_elements(self):
        mouse_pos = pygame.mouse.get_pos()
        for name, btn in self.buttons.items():
            rect = btn['rect']; color = BUTTON_COLOR
            is_disabled = (name == "Solve" and (self.solved or self.is_solving)); 
            if is_disabled: color = DISABLED_BUTTON_COLOR
            elif rect.collidepoint(mouse_pos) and not self.is_solving: color = BUTTON_HOVER_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            font = FONT_MEDIUM if len(name) < 6 else FONT_SMALL
            text = font.render(name, True, BUTTON_TEXT_COLOR); self.screen.blit(text, (rect.x + (rect.width - text.get_width()) / 2, rect.y + (rect.height - text.get_height()) / 2))
        if self.runtime is not None:
            time_text = f"Runtime: {self.runtime:.4f} ms"; text = FONT_MEDIUM.render(time_text, True, GRID_COLOR); self.screen.blit(text, (SCREEN_WIDTH - text.get_width() - 20, SCREEN_HEIGHT - 40))

    def solve(self):
        """Fungsi pembungkus yang memanggil solver rekursif."""
        return self._backtrack()

    def _backtrack(self):
        """Solver rekursif menggunakan bitmask dan heuristik MRV."""
        best_cell_idx, min_candidates = -1, 10
        
        empty_cells = []
        for i in range(81):
            if self.board[i] == 0:
                empty_cells.append(i)

        if not empty_cells:
            return True # Base case: tidak ada sel kosong, puzzle selesai

        # Heuristik MRV: Cari sel dengan kandidat paling sedikit
        for i in empty_cells:
            r, c = i // 9, i % 9
            b = (r // 3) * 3 + c // 3
            
            used_mask = self.rows[r] | self.cols[c] | self.boxes[b]
            candidates_mask = ALL_CANDIDATES & ~used_mask
            num_candidates = bin(candidates_mask).count('1')
            
            if num_candidates < min_candidates:
                min_candidates = num_candidates
                best_cell_idx = i
        
        # Recursive step: coba setiap kandidat di sel terbaik
        r, c = best_cell_idx // 9, best_cell_idx % 9
        b = (r // 3) * 3 + c // 3
        used_mask = self.rows[r] | self.cols[c] | self.boxes[b]
        candidates_mask = ALL_CANDIDATES & ~used_mask
        
        while candidates_mask:
            candidate_bit = candidates_mask & -candidates_mask
            num = candidate_bit.bit_length()
            
            self.board[best_cell_idx] = num
            self.rows[r] |= candidate_bit
            self.cols[c] |= candidate_bit
            self.boxes[b] |= candidate_bit
            
            if self._backtrack():
                return True
            
            # Backtrack
            self.rows[r] &= ~candidate_bit
            self.cols[c] &= ~candidate_bit
            self.boxes[b] &= ~candidate_bit
            self.board[best_cell_idx] = 0
            
            candidates_mask &= ~candidate_bit

        return False

    def run(self):
        running = True
        self.load_grid('puzzle_mudah.txt') # Muat puzzle awal
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.is_solving:
                    for name, btn in self.buttons.items():
                        if btn['rect'].collidepoint(event.pos):
                            action = btn.get('action')
                            if action == 'load': self.load_grid(btn['file'])
                            elif action == 'reset': self.reset_state()
                            elif action == 'solve' and not self.solved:
                                self.is_solving = True
                                self.draw_all()
                                start_time = time.perf_counter()
                                solution_found = self.solve()
                                end_time = time.perf_counter()
                                if solution_found:
                                    self.runtime = (end_time - start_time) * 1000
                                    self.write_solution('SolusiSudoku.txt')
                                    print(f"Solusi ditemukan! Runtime: {self.runtime:.4f} ms")
                                    self.solved = True
                                else:
                                    print("Tidak ada solusi untuk puzzle ini."); self.reset_state()
                                self.is_solving = False
            self.draw_all()
        pygame.quit()

if __name__ == "__main__":
    solver = SudokuSolver()
    solver.run()

