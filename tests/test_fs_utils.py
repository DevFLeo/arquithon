"""Testes da integração com o Explorer (sem abrir janelas de verdade).

os.startfile e subprocess.run são mockados: chamar o Explorer de verdade a
cada rodada de testes encheria a tela de janelas e tornaria os testes
dependentes do ambiente gráfico.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from core import fs_utils


class FsUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix='arquithon_fs_test_')
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

    @patch('core.fs_utils.os.startfile', create=True)
    def test_open_in_explorer_cria_pasta_se_nao_existir(self, mock_startfile):
        alvo = os.path.join(self.tmp_dir, 'nao_existe_ainda')
        fs_utils.open_in_explorer(alvo)
        self.assertTrue(os.path.isdir(alvo))
        mock_startfile.assert_called_once_with(alvo)

    @patch('core.fs_utils.os.startfile', create=True)
    def test_open_in_explorer_com_pasta_ja_existente(self, mock_startfile):
        fs_utils.open_in_explorer(self.tmp_dir)
        mock_startfile.assert_called_once_with(self.tmp_dir)

    @patch('core.fs_utils.subprocess.run')
    def test_open_and_select_file_chama_explorer_select(self, mock_run):
        arquivo = os.path.join(self.tmp_dir, 'foto.png')
        with open(arquivo, 'wb') as f:
            f.write(b'x')
        fs_utils.open_and_select_file(arquivo)
        mock_run.assert_called_once_with(['explorer', '/select,', os.path.normpath(arquivo)])


if __name__ == '__main__':
    unittest.main()
