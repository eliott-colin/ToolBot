import os
import discord
import json
from discord.ext import commands

# Récupère le token depuis les secrets (variable d'environnement)
my_secret = os.getenv('DISCORD_TOKEN')

# Configure les intents
intents = discord.Intents.default()
intents.messages = True  # Active l'intent pour lire les messages
intents.message_content = True  # Requis pour lire le contenu des messages
intents.reactions = True  # Requis pour gérer les réactions

# Crée une instance du bot avec les intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Fichier JSON pour enregistrer les configurations par serveur
config_file = "server_config.json"
types_file = "types.json"

# Fonction pour charger les configurations des serveurs
def load_server_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            return json.load(file)
    else:
        return {}

# Fonction pour sauvegarder les configurations des serveurs
def save_server_config(config):
    with open(config_file, "w") as file:
        json.dump(config, file, indent=4)

# Fonction pour charger les types depuis le fichier JSON
def load_types():
    if os.path.exists(types_file):
        with open(types_file, "r") as file:
            return json.load(file)
    else:
        return []

# Fonction pour sauvegarder les types dans le fichier JSON
def save_types(types):
    with open(types_file, "w") as file:
        json.dump(types, file, indent=4)

# Fonction pour vérifier si un message contient un lien
def contains_link(content):
    return "http" in content or "www" in content

# Fonction pour sauvegarder les messages contenant des liens dans un fichier JSON
def save_message(message, type=None):
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as file:
            data = json.load(file)
    else:
        data = []

    # Ajoute le message dans la liste avec le type
    data.append({
        "author": message.author.name,
        "content": message.content,
        "timestamp": message.created_at.isoformat(),
        "url": message.jump_url,
        "type": type
    })

    # Sauvegarde les données dans le fichier JSON
    with open("messages.json", "w") as file:
        json.dump(data, file, indent=4)

# Fonction pour vérifier si l'utilisateur a le rôle "vérif-lien"
def has_verif_lien_role(user):
    return any(role.name == "vérif-lien" for role in user.roles)

# Commande pour configurer le salon de collecte
@bot.command()
async def setup(ctx, channel: discord.TextChannel):
    if not has_verif_lien_role(ctx.author):
        await ctx.send("Tu dois avoir le rôle 'vérif-lien' pour utiliser cette commande.")
        return

    if ctx.author.guild_permissions.administrator:
        # Charge la configuration actuelle
        config = load_server_config()

        # Ajoute ou met à jour la configuration du serveur
        config[str(ctx.guild.id)] = {
            "collect_channel_id": str(channel.id)
        }

        # Sauvegarde la configuration
        save_server_config(config)

        await ctx.send(f"Salon de collecte des liens configuré : {channel.mention}")
    else:
        await ctx.send("Tu dois être administrateur pour configurer le salon.")

# Commande pour ajouter un type
@bot.command()
async def addType(ctx, *, type_name: str,emoji_name: str):
    if not has_verif_lien_role(ctx.author):
        await ctx.send("Tu dois avoir le rôle 'vérif-lien' pour utiliser cette commande.")
        return

    # Charge les types existants
    types = load_types()

    # Si le type n'existe pas déjà, on l'ajoute
    if type_name not in types:
        types.append(type_name)
        save_types(types)
        await ctx.send(f"Le type '{type_name}' a été ajouté.")
    else:
        await ctx.send(f"Le type '{type_name}' existe déjà.")

# Événement quand le bot est prêt
@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

    # Événement pour traiter les nouveaux messages
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        config = load_server_config()
        if str(message.guild.id) in config:
            collect_channel_id = int(config[str(message.guild.id)]["collect_channel_id"])
            collect_channel = bot.get_channel(collect_channel_id)

            if message.channel == collect_channel and contains_link(message.content):
                # Envoie un message pour demander une réaction
                msg = await message.channel.send(f"Message contenant un lien : {message.content}.\nClique sur la réaction ✅ pour valider.")
                await msg.add_reaction("✅")

                def check(reaction, user):
                    return user != bot.user and reaction.message.id == msg.id and reaction.emoji == "✅" and has_verif_lien_role(user)

                # Attend la réaction d'une personne avec le rôle 'vérif-lien'
                reaction, user = await bot.wait_for('reaction_add', check=check)

                # Charge les types existants et demander un type
                types = load_types()
                type_message = "Choisis un type pour ce message :\n" + "\n".join([f"{i+1}. {type_}" for i, type_ in enumerate(types)])
                type_msg = await message.channel.send(type_message)

                # Ajouter les réactions correspondant aux types
                for i in range(len(types)):
                    await type_msg.add_reaction(str(i+1))  # Réactions de type '1', '2', '3', etc.

                # Attente de la réaction pour choisir un type
                def type_check(reaction, user):
                    return user != bot.user and reaction.message.id == type_msg.id and reaction.emoji in [str(i+1) for i in range(len(types))]

                reaction, user = await bot.wait_for('reaction_add', check=type_check)

                # Ajoute le type choisi au message et le sauvegarde
                selected_type = types[int(reaction.emoji) - 1]
                save_message(message, selected_type)
                await type_msg.edit(content=f"Message validé et de type '{selected_type}' ajouté au fichier JSON : {message.content}")

        await bot.process_commands(message)
        

# Commande pour vérifier le contenu du fichier JSON
@bot.command()
async def show_messages(ctx):
    if not has_verif_lien_role(ctx.author):
        await ctx.send("Tu dois avoir le rôle 'vérif-lien' pour utiliser cette commande.")
        return

    if os.path.exists("messages.json"):
        with open("messages.json", "r") as file:
            data = json.load(file)
        await ctx.send(f"Messages contenant des liens : {len(data)}")
    else:
        await ctx.send("Aucun message trouvé.")

# Utilise le token pour démarrer le bot
bot.run(my_secret)
