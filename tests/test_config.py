"""Testes de persistência de preferências em config.json."""

import os
import shutil
import tempfile
import unittest

from core import config, paths


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix='arquithon_config_test_')
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

        self._original_config_path = paths.CONFIG_PATH
        paths.CONFIG_PATH = os.path.join(self.tmp_dir, 'config.json')
        self.addCleanup(self._restore_path)

    def _restore_path(self):
        paths.CONFIG_PATH = self._original_config_path

    def test_load_sem_arquivo_devolve_dicionario_vazio(self):
        self.assertEqual(config.load(), {})

    def test_load_com_json_corrompido_devolve_dicionario_vazio(self):
        with open(paths.CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write('{isso nao e json valido')
        self.assertEqual(config.load(), {})

    def test_save_e_load_fazem_ida_e_volta(self):
        config.save({'org_mode': 'tamanho'})
        self.assertEqual(config.load(), {'org_mode': 'tamanho'})

    def test_get_com_chave_ausente_devolve_default(self):
        self.assertIsNone(config.get('chave_que_nao_existe'))
        self.assertEqual(config.get('chave_que_nao_existe', 'padrao'), 'padrao')

    def test_get_com_chave_presente(self):
        config.save({'org_mode': 'nome'})
        self.assertEqual(config.get('org_mode'), 'nome')

    def test_set_persiste_e_preserva_outras_chaves(self):
        config.set('org_mode', 'nome')
        config.set('search_content', False)
        self.assertEqual(config.load(), {'org_mode': 'nome', 'search_content': False})

    def test_set_sobrescreve_valor_existente(self):
        config.set('org_mode', 'nome')
        config.set('org_mode', 'tamanho')
        self.assertEqual(config.get('org_mode'), 'tamanho')


if __name__ == '__main__':
    unittest.main()
