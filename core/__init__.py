# core/__init__.py
# Làm thư mục core thành package, import các lớp chính để dễ sử dụng
from .board import Board
from .game_state import GameState
from .move_validator import MoveValidator
from .piece import Piece, create_piece