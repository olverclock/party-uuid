#!/usr/bin/env python3 criado por olverclock 06/12/2025
"""
GUI para listar partições (Linux/Windows) e gerar
linhas boot=UUID= disk=UUID=, com opção de salvar em .txt.

"""

from __future__ import annotations

import dataclasses
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import List

from PyQt6 import QtCore, QtGui, QtWidgets


# ----------------- Modelo de dados -----------------

@dataclasses.dataclass(frozen=True)
class Partition:
    device: str      # /dev/sda1 ou C:
    uuid: str        # UUID (Linux) ou UniqueId (Windows)
    fstype: str      # ext4, vfat, NTFS, etc.
    label: str | None = None


def _run(cmd: list[str], *, shell: bool = False) -> str:
    result = subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=True,
        shell=shell,
    )
    return result.stdout


def _list_partitions_linux() -> List[Partition]:
    raw = _run(["blkid", "-o", "export"])
    parts: List[Partition] = []
    current: dict[str, str] = {}

    for line in raw.splitlines():
        if not line.strip():
            if {"DEVNAME", "UUID", "TYPE"} <= current.keys():
                parts.append(
                    Partition(
                        device=current["DEVNAME"],
                        uuid=current["UUID"],
                        fstype=current["TYPE"],
                        label=current.get("LABEL"),
                    )
                )
            current = {}
            continue

        key, _, value = line.partition("=")
        current[key] = value

    if {"DEVNAME", "UUID", "TYPE"} <= current.keys():
        parts.append(
            Partition(
                device=current["DEVNAME"],
                uuid=current["UUID"],
                fstype=current["TYPE"],
                label=current.get("LABEL"),
            )
        )

    return parts


def _list_partitions_windows() -> List[Partition]:
    ps_script = r"""
Get-Partition | Get-Volume |
  Select-Object DriveLetter, FileSystemLabel, FileSystem, UniqueId |
  ConvertTo-Json
"""
    raw = _run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        shell=False,
    ).strip()

    if not raw:
        return []

    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]

    parts: List[Partition] = []
    for item in data:
        drive = item.get("DriveLetter")
        label = item.get("FileSystemLabel")
        fstype = item.get("FileSystem") or ""
        unique_id = item.get("UniqueId") or ""

        if drive:
            device = f"{drive}:"
        else:
            device = unique_id or "(sem letra)"

        if not unique_id:
            unique_id = device

        parts.append(
            Partition(
                device=device,
                uuid=unique_id,
                fstype=fstype,
                label=label,
            )
        )

    return parts


def list_partitions() -> List[Partition]:
    system = platform.system().lower()
    if system == "linux":
        return _list_partitions_linux()
    if system == "windows":
        return _list_partitions_windows()
    raise RuntimeError(f"Sistema não suportado: {system}")


# ----------------- Interface gráfica -----------------

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UUID Helper – boot=UUID= / disk=UUID=")
        self.resize(900, 500)
        self._setup_ui()
        self._load_partitions()

    def _setup_ui(self) -> None:
        # Paleta “dark” simples, estilo moderno.
        self._apply_dark_theme()

        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Título
        title = QtWidgets.QLabel("Detecção de Partições e UUIDs")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Tabela de partições
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Dispositivo", "UUID / UniqueId", "Sistema de arquivos", "Rótulo"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.table, stretch=1)

        # Combos para escolher boot/disk
        form = QtWidgets.QHBoxLayout()
        form.setSpacing(10)

        self.combo_boot = QtWidgets.QComboBox()
        self.combo_disk = QtWidgets.QComboBox()

        form.addWidget(QtWidgets.QLabel("Partição BOOT:"))
        form.addWidget(self.combo_boot, stretch=1)
        form.addWidget(QtWidgets.QLabel("Partição DISK:"))
        form.addWidget(self.combo_disk, stretch=1)

        layout.addLayout(form)

        # Campo de saída da linha boot=UUID= disk=UUID=
        self.output_edit = QtWidgets.QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText(
            "Selecione BOOT e DISK para gerar a linha..."
        )
        layout.addWidget(self.output_edit)

        # Botões inferiores
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch(1)

        self.btn_refresh = QtWidgets.QPushButton("Atualizar")
        self.btn_copy = QtWidgets.QPushButton("Copiar")
        self.btn_save = QtWidgets.QPushButton("Salvar em .txt")
        self.btn_exit = QtWidgets.QPushButton("Sair")

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_exit)

        layout.addLayout(btn_layout)

        # Conexões
        self.combo_boot.currentIndexChanged.connect(self._update_cmdline)
        self.combo_disk.currentIndexChanged.connect(self._update_cmdline)
        self.btn_refresh.clicked.connect(self._load_partitions)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        self.btn_save.clicked.connect(self._save_to_txt)
        self.btn_exit.clicked.connect(self.close)

    def _apply_dark_theme(self) -> None:
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(30, 30, 30))
        palette.setColor(
            QtGui.QPalette.ColorRole.WindowText, QtCore.Qt.GlobalColor.white
        )
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(25, 25, 25))
        palette.setColor(
            QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(45, 45, 45)
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.ToolTipBase, QtCore.Qt.GlobalColor.white
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.ToolTipText, QtCore.Qt.GlobalColor.white
        )
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtCore.Qt.GlobalColor.white)
        palette.setColor(
            QtGui.QPalette.ColorRole.Button, QtGui.QColor(45, 45, 45)
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.ButtonText, QtCore.Qt.GlobalColor.white
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(33, 150, 243)
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.HighlightedText, QtCore.Qt.GlobalColor.white
        )
        self.setPalette(palette)

        self.setStyleSheet(
            """
            QMainWindow { background-color: #202020; }
            QLabel { color: #ffffff; }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #2a2a2a;
                color: #f0f0f0;
                border: 1px solid #444;
                padding: 4px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #f0f0f0;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #1976d2;
            }
        """
        )

    # ---------- Lógica da tela ----------

    def _load_partitions(self) -> None:
        try:
            parts = list_partitions()
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                f"Não foi possível listar as partições:\n{exc}",
            )
            return

        self.table.setRowCount(0)
        self.combo_boot.clear()
        self.combo_disk.clear()

        for p in parts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(p.device))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(p.uuid))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(p.fstype))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(p.label or ""))

            display = f"{p.device}  [{p.fstype}]"
            if p.label:
                display += f"  ({p.label})"

            self.combo_boot.addItem(display, userData=p)
            self.combo_disk.addItem(display, userData=p)

        if self.combo_boot.count() > 0:
            self.combo_boot.setCurrentIndex(0)
        if self.combo_disk.count() > 1:
            self.combo_disk.setCurrentIndex(1)

        self._update_cmdline()

    def _get_selected_partition(
        self, combo: QtWidgets.QComboBox
    ) -> Partition | None:
        idx = combo.currentIndex()
        if idx < 0:
            return None
        return combo.currentData()

    def _update_cmdline(self) -> None:
        boot = self._get_selected_partition(self.combo_boot)
        disk = self._get_selected_partition(self.combo_disk)
        if not boot or not disk or boot.device == disk.device:
            self.output_edit.setText("")
            return

        line = f"boot=UUID={boot.uuid} disk=UUID={disk.uuid}"
        self.output_edit.setText(line)

    def _copy_to_clipboard(self) -> None:
        text = self.output_edit.text()
        if not text:
            return
        QtWidgets.QApplication.clipboard().setText(text)
        QtWidgets.QMessageBox.information(
            self, "Copiado", "Linha copiada para a área de transferência."
        )

    def _save_to_txt(self) -> None:
        text = self.output_edit.text()
        if not text:
            QtWidgets.QMessageBox.warning(
                self, "Aviso", "Nenhuma linha gerada para salvar."
            )
            return

        path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Salvar linha boot/disk em TXT",
            str(Path.home() / "boot_disk_uuid.txt"),
            "Arquivos de texto (*.txt);;Todos os arquivos (*)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            path.write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Erro ao salvar",
                f"Não foi possível salvar o arquivo:\n{exc}",
            )
            return

        QtWidgets.QMessageBox.information(
            self,
            "Salvo",
            f"Arquivo salvo em:\n{path}",
        )


# ----------------- Ponto de entrada -----------------

def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
