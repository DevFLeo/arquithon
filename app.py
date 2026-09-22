"""Ponto de entrada do Arquithon.

A lógica de organização e busca mora em `core/`; a interface, em `ui/`. Este
arquivo só sobe a janela.
"""

from ui.app_window import ArquithonApp

if __name__ == '__main__':
    ArquithonApp().mainloop()
