#!/usr/bin/env python3
"""
Script simples para verificar e instalar dependências
"""

import subprocess
import sys

def check_vlc():
    """Verifica se o VLC está instalado no sistema"""
    try:
        result = subprocess.run(['which', 'vlc'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✓ VLC encontrado no sistema")
            return True
        else:
            print("✗ VLC não encontrado")
            print("  Por favor, instale o VLC Media Player:")
            print("  macOS: brew install --cask vlc")
            print("  Ou baixe de: https://www.videolan.org/vlc/")
            return False
    except Exception as e:
        print(f"Erro ao verificar VLC: {e}")
        return False


def install_requirements():
    """Instala as dependências Python"""
    try:
        print("Instalando dependências Python...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependências instaladas com sucesso")
        return True
    except Exception as e:
        print(f"Erro ao instalar dependências: {e}")
        return False

if __name__ == "__main__":
    print("Verificando requisitos...\n")
    
    vlc_ok = check_vlc()
    print()
    
    if vlc_ok:
        install_requirements()
        print("\n✓ Setup completo! Pode executar: python video_quality_test.py")
    else:
        print("\n⚠ Por favor, instale o VLC antes de continuar.")

