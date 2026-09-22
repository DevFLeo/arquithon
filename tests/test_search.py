"""Testes do motor de busca/indexação (sem abrir GUI nenhuma)."""

import os
import shutil
import tempfile
import unittest

from core import paths, search


class SearchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix='arquithon_search_test_')
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

        self._original_upload_folder = paths.UPLOAD_FOLDER
        self._original_config_path = paths.CONFIG_PATH
        paths.UPLOAD_FOLDER = os.path.join(self.tmp_dir, 'uploads')
        paths.CONFIG_PATH = os.path.join(self.tmp_dir, 'config.json')
        self.addCleanup(self._restore_paths)

    def _restore_paths(self):
        paths.UPLOAD_FOLDER = self._original_upload_folder
        paths.CONFIG_PATH = self._original_config_path

    def _write(self, rel_path, content=''):
        full_path = os.path.join(paths.UPLOAD_FOLDER, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return full_path

    def test_indice_vazio_quando_pasta_nao_existe(self):
        self.assertEqual(search.build_index(), [])

    def test_indice_encontra_todos_os_arquivos(self):
        self._write('imagens/png/foto.png')
        self._write('documentos/pdf/relatorio.pdf')
        index = search.build_index()
        self.assertEqual({item.name for item in index}, {'foto.png', 'relatorio.pdf'})

    def test_busca_por_nome_e_case_insensitive(self):
        self._write('documentos/texto/Notas.txt', 'nada relevante aqui')
        index = search.build_index()
        resultados = search.search(index, 'notas')
        self.assertEqual([r.name for r in resultados], ['Notas.txt'])

    def test_busca_por_conteudo_em_arquivo_de_texto(self):
        self._write('documentos/texto/relatorio.txt', 'projeto arquithon em python')
        index = search.build_index()
        resultados = search.search(index, 'arquithon', include_content=True)
        self.assertEqual(len(resultados), 1)

    def test_busca_por_conteudo_desligada_ignora_texto_interno(self):
        self._write('documentos/texto/relatorio.txt', 'projeto arquithon em python')
        index = search.build_index()
        resultados = search.search(index, 'arquithon', include_content=False)
        self.assertEqual(resultados, [])

    def test_arquivo_binario_nao_tem_conteudo_indexado(self):
        self._write('imagens/png/foto.png', 'texto que não deveria ser indexado')
        index = search.build_index()
        item = next(i for i in index if i.name == 'foto.png')
        self.assertEqual(item.snippet, '')

    def test_busca_vazia_devolve_indice_completo(self):
        self._write('imagens/png/foto.png')
        self._write('documentos/pdf/relatorio.pdf')
        index = search.build_index()
        self.assertEqual(search.search(index, ''), index)

    def test_preferencia_de_busca_no_conteudo_padrao_e_verdadeira(self):
        self.assertTrue(search.load_search_content_pref())

    def test_preferencia_de_busca_no_conteudo_e_persistida(self):
        search.save_search_content_pref(False)
        self.assertFalse(search.load_search_content_pref())


    def test_busca_encontra_pelo_nome_da_pasta(self):
        self._write('imagens/png/foto.png')
        self._write('documentos/pdf/relatorio.pdf')
        index = search.build_index()

        por_categoria = search.search(index, 'imagens')
        self.assertEqual([item.name for item in por_categoria], ['foto.png'])

        por_subpasta = search.search(index, 'pdf')
        self.assertEqual([item.name for item in por_subpasta], ['relatorio.pdf'])

    def test_busca_por_pasta_aceita_caminho_com_barra(self):
        self._write('imagens/png/foto.png')
        index = search.build_index()
        self.assertEqual([i.name for i in search.search(index, 'imagens/png')], ['foto.png'])

    def test_quem_casa_pelo_nome_vem_antes_de_quem_casa_pela_pasta(self):
        self._write('contratos/2026/anexo.txt')          # casa so pela pasta
        self._write('imagens/png/contratos.png')          # casa pelo nome
        index = search.build_index()
        self.assertEqual([item.name for item in search.search(index, 'contratos')],
                         ['contratos.png', 'anexo.txt'])


if __name__ == '__main__':
    unittest.main()
