"""Mini Pokédex no terminal usando a PokéAPI (gratuita, sem chave).

Mostra dados do Pokémon e a linha evolutiva completa, com o número de cada um.

Uso:
    pip install requests
    python pokedex.py
"""

import io
import random
import webbrowser

import requests

API = "https://pokeapi.co/api/v2"


def get_json(url):
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def buscar_pokemon(nome_ou_id):
    return get_json(f"{API}/pokemon/{str(nome_ou_id).lower().strip()}")


def id_da_url(url):
    # ex.: https://pokeapi.co/api/v2/pokemon-species/25/ -> 25
    return int(url.rstrip("/").split("/")[-1])


def caminhos_evolutivos(no, caminho_atual=None):
    """Percorre a árvore de evoluções e devolve todos os caminhos possíveis."""
    caminho_atual = (caminho_atual or []) + [
        (id_da_url(no["species"]["url"]), no["species"]["name"])
    ]
    if not no["evolves_to"]:
        return [caminho_atual]
    caminhos = []
    for prox in no["evolves_to"]:
        caminhos.extend(caminhos_evolutivos(prox, caminho_atual))
    return caminhos


def buscar_linha_evolutiva(pokemon):
    especie = get_json(pokemon["species"]["url"])
    if not especie or not especie.get("evolution_chain"):
        return []
    cadeia = get_json(especie["evolution_chain"]["url"])
    if not cadeia:
        return []
    return caminhos_evolutivos(cadeia["chain"])


def mostrar_evolucoes(pokemon, caminhos):
    print("\nLinha evolutiva:")
    if len(caminhos) <= 1 and len(caminhos[0] if caminhos else []) <= 1:
        print("  Não evolui.")
        return
    atual = id_da_url(pokemon["species"]["url"])
    for caminho in caminhos:
        partes = []
        for num, nome in caminho:
            texto = f"#{num} {nome.capitalize()}"
            if num == atual:
                texto = f"[{texto}]"  # destaca o Pokémon pesquisado
            partes.append(texto)
        print("  " + " -> ".join(partes))


def mostrar(p):
    tipos = ", ".join(t["type"]["name"] for t in p["types"])
    habilidades = ", ".join(a["ability"]["name"] for a in p["abilities"])
    print(f"\n#{p['id']} - {p['name'].capitalize()}")
    print(f"Tipo(s):      {tipos}")
    print(f"Altura:       {p['height'] / 10} m")
    print(f"Peso:         {p['weight'] / 10} kg")
    print(f"Habilidades:  {habilidades}")
    print("Status base:")
    for s in p["stats"]:
        print(f"  {s['stat']['name']:<18} {s['base_stat']}")


def mostrar_imagem(pokemon):
    """Abre a imagem do Pokémon (arte oficial, ou sprite se não houver)."""
    sprites = pokemon["sprites"]
    url = (
        sprites["other"]["official-artwork"]["front_default"]
        or sprites["front_default"]
    )
    if not url:
        print("Este Pokémon não tem imagem disponível.")
        return
    try:
        from PIL import Image  # pip install pillow

        dados = requests.get(url, timeout=10).content
        Image.open(io.BytesIO(dados)).show()
    except ImportError:
        # Sem o Pillow, abre a imagem direto no navegador
        webbrowser.open(url)


GERACAO_DO_JOGO = {
    "red-blue": 1, "yellow": 1,
    "gold-silver": 2, "crystal": 2,
    "ruby-sapphire": 3, "emerald": 3, "firered-leafgreen": 3,
    "diamond-pearl": 4, "platinum": 4, "heartgold-soulsilver": 4,
    "black-white": 5, "black-2-white-2": 5,
    "x-y": 6, "omega-ruby-alpha-sapphire": 6,
    "sun-moon": 7, "ultra-sun-ultra-moon": 7,
    "lets-go-pikachu-lets-go-eevee": 7,
    "sword-shield": 8, "brilliant-diamond-and-shining-pearl": 8,
    "legends-arceus": 8,
    "scarlet-violet": 9,
}

METODOS = {
    "level-up": "Por nível",
    "machine": "Por TM/HM",
    "egg": "Por ovo",
    "tutor": "Com tutor",
}


def mostrar_ataques(pokemon, geracao):
    """Lista os ataques que o Pokémon aprende em uma geração."""
    por_metodo = {}
    for m in pokemon["moves"]:
        for d in m["version_group_details"]:
            jogo = d["version_group"]["name"]
            if GERACAO_DO_JOGO.get(jogo) != geracao:
                continue
            metodo = d["move_learn_method"]["name"]
            nivel = d["level_learned_at"]
            por_metodo.setdefault(metodo, {})[m["move"]["name"]] = nivel

    print(f"\nAtaques na geração {geracao}:")
    if not por_metodo:
        print("  Este Pokémon não existe nessa geração.")
        return
    for metodo, ataques in por_metodo.items():
        print(f"  {METODOS.get(metodo, metodo)}:")
        for nome, nivel in sorted(ataques.items(), key=lambda x: (x[1], x[0])):
            extra = f" (nv. {nivel})" if metodo == "level-up" else ""
            print(f"    - {nome.replace('-', ' ').title()}{extra}")


def main():
    print("=== Mini Pokédex ===")
    print("Digite um nome ou número, 'r' para aleatório, ou 'sair'.")
    while True:
        entrada = input("\n> ").strip()
        if entrada.lower() in ("sair", "q", "exit"):
            break
        if not entrada:
            continue
        if entrada.lower() == "r":
            entrada = random.randint(1, 1025)
        try:
            pokemon = buscar_pokemon(entrada)
            if pokemon is None:
                print("Pokémon não encontrado.")
                continue
            mostrar(pokemon)
            mostrar_evolucoes(pokemon, buscar_linha_evolutiva(pokemon))
            if input("\nVer imagem? (s/n) ").strip().lower() == "s":
                mostrar_imagem(pokemon)
            if input("Ver ataques? (s/n) ").strip().lower() == "s":
                ger = input("Qual geração? (1-9) ").strip()
                if ger.isdigit() and 1 <= int(ger) <= 9:
                    mostrar_ataques(pokemon, int(ger))
                else:
                    print("Geração inválida.")
        except requests.RequestException as e:
            print(f"Erro de conexão: {e}")


if __name__ == "__main__":
    main()