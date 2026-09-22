"""Testes do núcleo de organização de arquivos (sem abrir GUI nenhuma)."""

import os
import shutil
import tempfile
import unittest

from core import organizer, paths


class OrganizerTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix='arquithon_test_')
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

        self._original_upload_folder = paths.UPLOAD_FOLDER
        self._original_config_path = paths.CONFIG_PATH
        paths.UPLOAD_FOLDER = os.path.join(self.tmp_dir, 'uploads')
        paths.CONFIG_PATH = os.path.join(self.tmp_dir, 'config.json')
        self.addCleanup(self._restore_paths)

        self.source_dir = os.path.join(self.tmp_dir, 'origem')
        os.makedirs(self.source_dir)

    def _restore_paths(self):
        paths.UPLOAD_FOLDER = self._original_upload_folder
        paths.CONFIG_PATH = self._original_config_path

    def _make_file(self, name, content=b'conteudo de teste'):
        path = os.path.join(self.source_dir, name)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def test_extensao_conhecida_vai_para_subpasta_mapeada(self):
        foto = self._make_file('foto.png')
        resultado = organizer.organize_files([foto], mode='extensao')
        self.assertEqual((resultado.successful, resultado.failed), (1, 0))
        organizados = organizer.scan_organized_files()
        self.assertEqual(organizados[os.path.join('imagens', 'png')], ['foto.png'])

    def test_extensao_desconhecida_cai_em_outros(self):
        misterioso = self._make_file('misterioso.xyz')
        organizer.organize_files([misterioso], mode='extensao')
        organizados = organizer.scan_organized_files()
        self.assertIn(os.path.join('outros', 'xyz'), organizados)

    def test_arquivo_sem_extensao_nao_fica_sem_categoria(self):
        sem_ext = self._make_file('semextensao')
        organizer.organize_files([sem_ext], mode='extensao')
        organizados = organizer.scan_organized_files()
        self.assertIn(os.path.join('outros', 'sem_extensao'), organizados)

    def test_modo_nome_agrupa_por_primeira_letra(self):
        arquivo = self._make_file('Manual.pdf')
        organizer.organize_files([arquivo], mode='nome')
        organizados = organizer.scan_organized_files()
        self.assertIn(os.path.join('alfabetico', 'M'), organizados)

    def test_modo_tamanho_agrupa_arquivos_pequenos(self):
        pequeno = self._make_file('pequeno.bin', content=b'x' * 100)
        organizer.organize_files([pequeno], mode='tamanho')
        organizados = organizer.scan_organized_files()
        self.assertTrue(any('pequenos' in categoria for categoria in organizados))

    def test_arquivos_de_mesmo_nome_nao_se_sobrescrevem(self):
        outra_origem = os.path.join(self.tmp_dir, 'outra_origem')
        os.makedirs(outra_origem)
        primeiro = self._make_file('foto.png', content=b'primeiro')
        segundo_path = os.path.join(outra_origem, 'foto.png')
        with open(segundo_path, 'wb') as f:
            f.write(b'segundo')

        resultado = organizer.organize_files([primeiro, segundo_path], mode='extensao')
        self.assertEqual((resultado.successful, resultado.failed), (2, 0))

        organizados = organizer.scan_organized_files()
        arquivos = organizados[os.path.join('imagens', 'png')]
        self.assertEqual(sorted(arquivos), ['foto (2).png', 'foto.png'])

    def test_falha_ao_copiar_arquivo_inexistente_e_contabilizada(self):
        caminho_inexistente = os.path.join(self.source_dir, 'nao_existe.txt')
        resultado = organizer.organize_files([caminho_inexistente], mode='extensao')
        self.assertEqual((resultado.successful, resultado.failed), (0, 1))

    def test_modo_mover_remove_o_arquivo_da_origem(self):
        arquivo = self._make_file('nota.txt')
        organizer.organize_files([arquivo], mode='extensao', move=True)
        self.assertFalse(os.path.exists(arquivo))
        organizados = organizer.scan_organized_files()
        self.assertEqual(organizados[os.path.join('documentos', 'texto')], ['nota.txt'])

    def test_callback_de_progresso_e_chamado_por_arquivo(self):
        arquivos = [self._make_file(f'{i}.txt') for i in range(3)]
        chamadas = []
        organizer.organize_files(arquivos, mode='extensao', on_progress=lambda feito, total: chamadas.append((feito, total)))
        self.assertEqual(chamadas, [(1, 3), (2, 3), (3, 3)])

    def test_desfazer_copia_remove_a_copia_e_preserva_original(self):
        foto = self._make_file('foto.png')
        resultado = organizer.organize_files([foto], mode='extensao')
        restaurados, falhas = organizer.undo_operations(resultado.operations)
        self.assertEqual((restaurados, falhas), (1, 0))
        self.assertTrue(os.path.exists(foto))
        self.assertEqual(organizer.scan_organized_files(), {})

    def test_desfazer_mover_restaura_o_arquivo_na_origem(self):
        arquivo = self._make_file('nota.txt')
        resultado = organizer.organize_files([arquivo], mode='extensao', move=True)
        restaurados, falhas = organizer.undo_operations(resultado.operations)
        self.assertEqual((restaurados, falhas), (1, 0))
        self.assertTrue(os.path.exists(arquivo))
        self.assertEqual(organizer.scan_organized_files(), {})

    def test_preferencia_de_organizacao_e_persistida(self):
        self.assertEqual(organizer.load_org_mode(), organizer.DEFAULT_ORG_MODE)
        organizer.save_org_mode('tamanho')
        self.assertEqual(organizer.load_org_mode(), 'tamanho')

    def test_modo_invalido_no_config_cai_no_padrao(self):
        organizer.save_org_mode('modo-que-nao-existe-mais')
        self.assertEqual(organizer.load_org_mode(), organizer.DEFAULT_ORG_MODE)

    def test_format_file_size_em_unidades_diferentes(self):
        self.assertEqual(organizer.format_file_size(500), '500 B')
        self.assertEqual(organizer.format_file_size(2048), '2.0 KB')
        self.assertEqual(organizer.format_file_size(5 * 1024 * 1024), '5.0 MB')

    def test_format_modified_date(self):
        import time
        timestamp = time.mktime((2024, 3, 15, 12, 0, 0, 0, 0, -1))
        self.assertEqual(organizer.format_modified_date(timestamp), '15/03/2024')

    def test_delete_file_remove_arquivo_organizado(self):
        foto = self._make_file('foto.png')
        organizer.organize_files([foto], mode='extensao')
        caminho = os.path.join(paths.UPLOAD_FOLDER, 'imagens', 'png', 'foto.png')
        organizer.delete_file(caminho)
        self.assertFalse(os.path.exists(caminho))

    def test_delete_file_inexistente_levanta_oserror(self):
        with self.assertRaises(OSError):
            organizer.delete_file(os.path.join(paths.UPLOAD_FOLDER, 'nao_existe.txt'))

    def test_format_category_label_preserva_maiusculas_de_unidade(self):
        rotulo = organizer.format_category_label(os.path.join('tamanho', 'pequenos (menos de 1MB)'))
        self.assertIn('1MB', rotulo)
        self.assertNotIn('1mb', rotulo)

    def test_format_category_label_capitaliza_mes_mesmo_apos_numero(self):
        rotulo = organizer.format_category_label(os.path.join('2024', '01 - janeiro'))
        self.assertIn('01 - Janeiro', rotulo)


if __name__ == '__main__':
    unittest.main()
