"""Testes de receber o repositório de outro Arquithon."""

import os
import shutil
import tempfile
import unittest

from core import importer, organizer, paths


class ImporterTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='arquithon_imp_')
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self._orig = paths.UPLOAD_FOLDER
        paths.UPLOAD_FOLDER = os.path.join(self.tmp, 'meu', 'uploads')
        self.addCleanup(setattr, paths, 'UPLOAD_FOLDER', self._orig)
        self.outro = os.path.join(self.tmp, 'outro')

    def _write(self, base, rel, content=b'x'):
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def test_copia_mantendo_subpastas_a_partir_da_pasta_do_app(self):
        self._write(self.outro, os.path.join('uploads', 'imagens', 'png', 'a.png'))
        r = importer.import_repository(self.outro)
        self.assertEqual((r.copied, r.duplicates, r.failed), (1, 0, 0))
        self.assertTrue(os.path.isfile(os.path.join(paths.UPLOAD_FOLDER, 'imagens', 'png', 'a.png')))

    def test_aceita_a_propria_pasta_uploads(self):
        self._write(self.outro, os.path.join('uploads', 'docs', 'b.txt'))
        r = importer.import_repository(os.path.join(self.outro, 'uploads'))
        self.assertEqual(r.copied, 1)

    def test_arquivo_identico_e_pulado_e_diferente_ganha_sufixo(self):
        self._write(paths.UPLOAD_FOLDER, os.path.join('docs', 'igual.txt'), b'mesmo')
        self._write(paths.UPLOAD_FOLDER, os.path.join('docs', 'nome.txt'), b'antigo')
        self._write(self.outro, os.path.join('uploads', 'docs', 'igual.txt'), b'mesmo')
        self._write(self.outro, os.path.join('uploads', 'docs', 'nome.txt'), b'novo')
        r = importer.import_repository(self.outro)
        self.assertEqual((r.copied, r.duplicates), (1, 1))
        self.assertTrue(os.path.isfile(os.path.join(paths.UPLOAD_FOLDER, 'docs', 'nome (2).txt')))

    def test_recusa_a_propria_pasta(self):
        os.makedirs(paths.UPLOAD_FOLDER)
        with self.assertRaises(importer.ImportError_):
            importer.import_repository(os.path.dirname(paths.UPLOAD_FOLDER))

    def test_desfazer_remove_so_o_que_foi_recebido(self):
        origem = self._write(self.outro, os.path.join('uploads', 'docs', 'c.txt'))
        r = importer.import_repository(self.outro)
        organizer.undo_operations(r.operations)
        self.assertFalse(os.path.exists(os.path.join(paths.UPLOAD_FOLDER, 'docs', 'c.txt')))
        self.assertTrue(os.path.isfile(origem))


if __name__ == '__main__':
    unittest.main()
