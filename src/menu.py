LARGURA = 46

def _linha(texto: str = "") -> str:
    return "║" + (" " + texto).ljust(LARGURA) + "║"

def menu_principal(status: str) -> str:
    return "\n".join([
        "╔" + "═" * LARGURA + "╗",
        _linha("MelobudsNext - QCY Melobuds Pro"),
        _linha(status),
        "╠" + "═" * LARGURA + "╣",
        _linha("1. Ativar/Desativar Game Mode"),
        _linha("2. Alterar modo ANC"),
        _linha("3. Consultar estados"),
        _linha("4. Reconfigurar fone (MAC/UUIDs)"),
        _linha("5. Sair"),
        "╚" + "═" * LARGURA + "╝",
    ])

def painel_estado(bateria: str, anc: str, game_mode: str, versao: str) -> str:
    return "\n".join([
        "╔" + "═" * LARGURA + "╗",
        _linha("MelobudsNext - Estado do Fone"),
        "╠" + "═" * LARGURA + "╣",
        _linha(f"Bateria:   {bateria}"),
        _linha(f"ANC:       {anc}"),
        _linha(f"Game Mode: {game_mode}"),
        _linha(f"Versao:    {versao}"),
        "╠" + "═" * LARGURA + "╣",
        _linha("1. Atualizar tudo agora (leituras + 0xFE)"),
        _linha("Enter/outro: voltar ao menu"),
        "╚" + "═" * LARGURA + "╝",
    ])

ANC_MENU = """
╔══════════════════════════════════════════╗
║   MelobudsNext - ANC                     ║
╠══════════════════════════════════════════╣
║  1. Desligado                            ║
║  2. Interior                             ║
║  3. Viagens Diárias                      ║
║  4. Barulho                              ║
║  5. Ruído Contra o Vento                 ║
║  6. Cancelamento Adaptativo              ║
║  7. Transparência                        ║
╚══════════════════════════════════════════╝
"""
ANC_INTENSE = """
╔══════════════════════════════════════════╗
║   MelobudsNext - Nível do ANC            ║
╠══════════════════════════════════════════╣
║  1. Intensidade 1                        ║
║  2. Intensidade 2                        ║
║  3. Intensidade 3                        ║
╚══════════════════════════════════════════╝
"""
TRANSP_MENU = """
╔══════════════════════════════════════════╗
║   MelobudsNext - Modo Transparência      ║
╠══════════════════════════════════════════╣
║  1. Aprimoramento Vocal                  ║
║  2. Intensidade 1                        ║
║  3. Intensidade 2                        ║
║  4. Intensidade 3                        ║
║  5. Intensidade 4                        ║
║  6. Intensidade 5                        ║
║  7. Intensidade 6                        ║
╚══════════════════════════════════════════╝
"""