import discord
import asyncio
import os
import re
import aiohttp
import json
from collections import defaultdict, deque
from pathlib import Path
from dotenv import load_dotenv

from discord.ext import commands, tasks
from discord.utils import get
from discord import ui
from discord.ui import View, Button, button
from datetime import datetime, timedelta

# Charger le .env situé dans le même dossier que bot.py
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("DISCORD_TOKEN")

print("FICHIER .ENV :", env_path)
print("TOKEN CHARGE :", bool(TOKEN))

if not TOKEN:
    raise RuntimeError("❌ La variable DISCORD_TOKEN n'est pas définie.")



# ============================================================
# CONFIGURATION DU SYSTÈME DE PREUVES
# ============================================================

# Salon dans lequel le panneau sera affiché
PROOF_PANEL_CHANNEL_ID = 1559297407559401622

# Salon privé/staff dans lequel les demandes seront envoyées
PROOF_REVIEW_CHANNEL_ID = 1559297408381493423

# Rôle donné automatiquement lorsque la demande est validée
PROOF_ROLE_ID = 1559297026175410287

# Salon où seront annoncées les validations
PROOF_SUCCESS_CHANNEL_ID = 1559297410214404150

# ============================================================
# CONFIGURATION DU PANNEAU VIP
# ============================================================

# Salon vers lequel le bouton "CLIQUE POUR LE STG VIP" redirige (#🎫・tickets-vip)
VIP_ACCESS_CHANNEL_ID = 1559297379490996245

# Logo affiché à droite du titre du panneau VIP (à mettre à côté de bot.py)
STGFR_WEBHOOK_LOGO_PATH = Path(__file__).parent / "stgfr_webhook_logo.png"


# Préfixe pour les commandes
intents = discord.Intents.default()
intents.members = True  # Pour gérer les membres
intents.presences = True  # Pour +stats : compter les membres en ligne (à activer aussi dans le portail Discord)
intents.moderation = True  # Pour les logs de bans / débans
intents.message_content = True  # Pour pouvoir lire les messages

bot = commands.Bot(command_prefix="+", intents=intents)



    


# Fonction pour créer un embed vert
def create_embed(title, description):
    embed = discord.Embed(title=title, description=description, color=0x00FF00)  # Couleur verte
    return embed

# Commande pour bannir un membre
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(embed=create_embed("Membre banni", f"{member} a été banni pour la raison: {reason}"))


# Commande pour expulser un membre
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(embed=create_embed("Membre expulsé", f"{member} a été expulsé pour la raison: {reason}"))


# Commande pour ajouter un rôle à un membre
@bot.command()
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Rôle {role} ajouté à {member}.")


# Commande pour supprimer un rôle d'un membre
@bot.command()
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"❌ Rôle {role} retiré à {member}.")

# Commande pour déplacer un membre dans un autre canal vocal
@bot.command()
@commands.has_permissions(move_members=True)
async def move(ctx, member: discord.Member, channel: discord.VoiceChannel):
    embed = create_embed("Membre déplacé", f"{member} a été déplacé vers {channel}")
    await ctx.send(embed=embed)

# Commande pour muter temporairement un membre
@bot.command()
@commands.has_permissions(manage_messages=True)
async def tempmute(ctx, member: discord.Member, duration: int):
    mute_role = get(ctx.guild.roles, name="Muted")
    
    if not mute_role:
        perms = discord.Permissions(send_messages=False, speak=False)
        mute_role = await ctx.guild.create_role(name="Muted", permissions=perms)

    await member.add_roles(mute_role)
    await ctx.send(f"🔇 {member.mention} a été muté pour {duration} minutes.")

    await asyncio.sleep(duration * 60)
    await member.remove_roles(mute_role)
    await ctx.send(f"🔊 {member.mention} n'est plus muté.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Supprime un certain nombre de messages dans le canal."""
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 **{amount} messages supprimés !**", delete_after=3)




@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx, time: int):
    """Verrouille un salon pendant un certain temps (en minutes)."""
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
    }
    await ctx.channel.edit(overwrites=overwrites)
    await ctx.send("🔒 Le salon est maintenant en lockdown.")

    # Attendre la durée du lockdown, puis rétablir les permissions
    await asyncio.sleep(time * 60)
    await ctx.channel.edit(overwrites={})
    await ctx.send("🔓 Le salon a été débloqué.")

@bot.command()
async def roles(ctx, member: discord.Member):
    """Affiche les rôles d'un membre."""
    roles = [role.name for role in member.roles]
    await ctx.send(f"{member.mention} a les rôles suivants : {', '.join(roles)}")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nickname(ctx, member: discord.Member, *, new_nickname: str):
    """Change le pseudonyme d'un membre."""
    try:
        await member.edit(nick=new_nickname)
        await ctx.send(f"Le pseudonyme de {member.mention} a été changé en {new_nickname}.")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de changer le pseudonyme de ce membre.")



# ============================================================
# IMPORTER UN EMOJI DEPUIS UN AUTRE SERVEUR
# ============================================================

CUSTOM_EMOJI_RE = re.compile(r"^<(?P<animated>a?):(?P<name>[A-Za-z0-9_]{2,32}):(?P<id>\d+)>$")


@bot.group(name="emoji", invoke_without_command=True)
async def emoji_group(ctx):
    await ctx.send(
        "Utilisation : `+emoji add <:nom:ID>`\n"
        "Exemple : `+emoji add <:monemoji:123456789012345678>`"
    )


@emoji_group.command(name="add")
@commands.has_permissions(manage_emojis_and_stickers=True)
async def emoji_add(ctx, *, emoji_input: str):
    """Télécharge un emoji personnalisé et l'ajoute au serveur actuel."""
    if ctx.guild is None:
        await ctx.send("❌ Cette commande doit être utilisée dans un serveur.")
        return

    match = CUSTOM_EMOJI_RE.fullmatch(emoji_input.strip().strip('"\''))
    if match is None:
        await ctx.send(
            "❌ Emoji invalide. Envoie un emoji personnalisé Discord au format "
            "`<:nom:ID>` ou `<a:nom:ID>` (animé)."
        )
        return

    bot_member = ctx.guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_emojis_and_stickers:
        await ctx.send(
            "❌ Je n'ai pas la permission **Gérer les émojis et les autocollants** "
            "sur ce serveur."
        )
        return

    emoji_name = match.group("name")
    emoji_id = match.group("id")
    animated = bool(match.group("animated"))
    extension = "gif" if animated else "png"
    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}?quality=lossless"

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(emoji_url) as response:
                if response.status != 200:
                    await ctx.send(
                        "❌ Impossible de récupérer cet emoji. Vérifie qu'il s'agit "
                        "bien d'un emoji personnalisé encore accessible."
                    )
                    return
                image_data = await response.read()

        # Limite de sécurité pour éviter les fichiers trop volumineux.
        if len(image_data) > 256 * 1024:
            await ctx.send(
                "❌ Cet emoji dépasse la limite de 256 Ko acceptée par cette commande."
            )
            return

        created = await ctx.guild.create_custom_emoji(
            name=emoji_name,
            image=image_data,
            reason=f"Emoji importé par {ctx.author} depuis la commande +emoji add"
        )

        await ctx.send(f"✅ Emoji {created} ajouté au serveur **{ctx.guild.name}** !")

    except discord.Forbidden:
        await ctx.send(
            "❌ Discord a refusé l'ajout. Vérifie que le bot possède la permission "
            "**Gérer les émojis et les autocollants**."
        )
    except discord.HTTPException as error:
        if getattr(error, "code", None) == 30008:
            await ctx.send("❌ Ce serveur a atteint sa limite d'émojis personnalisés.")
        else:
            await ctx.send(f"❌ Discord n'a pas pu ajouter cet emoji : `{error}`")
    except aiohttp.ClientError:
        await ctx.send("❌ Erreur réseau pendant le téléchargement de l'emoji.")


# ============================================================
# PROTECTION ANTI-LINK / ANTI-PUB / ANTI-SPAM
# Commandes : +antilink / +antilink on / +antilink off
# ============================================================

ANTILINK_SETTINGS_FILE = Path(__file__).parent / "antilink_settings.json"


def load_antilink_settings():
    try:
        if ANTILINK_SETTINGS_FILE.exists():
            saved = json.loads(ANTILINK_SETTINGS_FILE.read_text(encoding="utf-8"))
            return {int(guild_id) for guild_id in saved.get("enabled_guilds", [])}
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"⚠️ Impossible de charger les réglages anti-link : {error}")
    return set()


antilink_enabled_guilds = load_antilink_settings()
message_history = defaultdict(deque)
recent_message_content = defaultdict(deque)


def save_antilink_settings():
    try:
        ANTILINK_SETTINGS_FILE.write_text(
            json.dumps({"enabled_guilds": sorted(antilink_enabled_guilds)}, indent=2),
            encoding="utf-8"
        )
    except OSError as error:
        print(f"⚠️ Impossible d'enregistrer les réglages anti-link : {error}")


LINK_PATTERN = re.compile(
    r"(?:https?://|www\.|discord\.gg/|discord(?:app)?\.com/invite/|"
    r"\b[a-z0-9-]+\.(?:com|fr|net|org|gg|io|me|co|tv|xyz|shop|site|online|info|dev|app)\b)",
    re.IGNORECASE
)
MARKDOWN_LINK_PATTERN = re.compile(r"\]\(\s*(?:https?://|www\.)", re.IGNORECASE)


@bot.group(name="antilink", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def antilink(ctx):
    if ctx.guild is None:
        return
    status = "🟢 ACTIVÉE" if ctx.guild.id in antilink_enabled_guilds else "🔴 DÉSACTIVÉE"
    await ctx.send(
        f"🛡️ **Protection Anti-Link :** {status}\n"
        "Utilisation : `+antilink on` ou `+antilink off`."
    )


@antilink.command(name="on")
@commands.has_permissions(administrator=True)
async def antilink_on(ctx):
    antilink_enabled_guilds.add(ctx.guild.id)
    save_antilink_settings()
    await ctx.send("🛡️ **Protection Anti-Link activée !** Les liens et les spams détectés seront supprimés.")


@antilink.command(name="off")
@commands.has_permissions(administrator=True)
async def antilink_off(ctx):
    antilink_enabled_guilds.discard(ctx.guild.id)
    save_antilink_settings()
    await ctx.send("🔓 **Protection Anti-Link désactivée !**")


@bot.listen("on_message")
async def anti_link_protection(message):
    if message.guild is None or message.author.bot:
        return
    if message.guild.id not in antilink_enabled_guilds:
        return

    # Les administrateurs et modérateurs ayant Gérer les messages sont exemptés.
    permissions = message.author.guild_permissions
    if permissions.administrator or permissions.manage_messages:
        return

    content = message.content or ""
    member_key = (message.guild.id, message.author.id)
    now = asyncio.get_running_loop().time()

    # Supprime les liens, invitations Discord et liens Markdown.
    if LINK_PATTERN.search(content) or MARKDOWN_LINK_PATTERN.search(content):
        try:
            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention}, les liens et publicités contenant des liens sont interdits !",
                delete_after=5
            )
        except discord.Forbidden:
            print("⚠️ Anti-link : le bot n'a pas la permission Gérer les messages.")
        except discord.HTTPException as error:
            print(f"⚠️ Anti-link : suppression impossible : {error}")
        return

    # Rafale : 5 messages en 5 secondes.
    timestamps = message_history[member_key]
    while timestamps and now - timestamps[0] > 5:
        timestamps.popleft()
    timestamps.append(now)

    # Répétition : 3 messages identiques en 15 secondes.
    normalized = " ".join(content.lower().split())
    duplicates = recent_message_content[member_key]
    while duplicates and now - duplicates[0][0] > 15:
        duplicates.popleft()
    if normalized:
        duplicates.append((now, normalized))

    repeated_count = sum(1 for _, previous in duplicates if previous == normalized)
    if len(timestamps) >= 5 or repeated_count >= 3:
        try:
            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention}, arrête le spam !",
                delete_after=5
            )
        except discord.Forbidden:
            print("⚠️ Anti-spam : le bot n'a pas la permission Gérer les messages.")
        except discord.HTTPException as error:
            print(f"⚠️ Anti-spam : suppression impossible : {error}")


# Commande pour afficher les informations d'aide (help)
@bot.command()
async def liste(ctx):
    embed = discord.Embed(
        title="📌 Liste des commandes disponibles",
        description="Voici les commandes que tu peux utiliser avec ce bot.",
        color=discord.Color.blue()
    )

    # Catégorie : 🛡️ Commandes Anti-Raid
    embed.add_field(
        name="🛡️ Commandes Anti-Raid",
        value=( 
            "`+antiraid on` → Active la protection anti-raid.\n"
            "`+antiraid off` → Désactive la protection anti-raid.\n"
            "`+antilink on/off` → Active ou désactive la protection anti-liens et anti-spam.\n"
            "🛑 Bloque les comptes récents (-7 jours).\n"
            "⏳ Expulse les spammeurs (5 messages/5 sec).\n"
            "⚠️ Supprime les messages avec trop de mentions (+5)."
        ),
        inline=False
    )

    # Catégorie : ⚒️ Commandes de Modération
    mod_value = (
        "`+ban @user [raison]` → Bannit un membre.\n"
        "`+kick @user [raison]` → Expulse un membre.\n"
        "`+add_role @user @role` → Ajoute un rôle à un membre.\n"
        "`+remove_role @user @role` → Retire un rôle à un membre.\n"
        "`+move @user #salon` → Déplace un membre en vocal.\n"
        "`+tempmute @user <durée en min>` → Mute temporairement un membre.\n"
        "`+clear <nombre>` → Supprime un nombre de messages.\n"
        "`+derank @user` → Supprime tous les rôles d'un membre.\n"
        "`+banlist` → Affiche la liste des membres bannis.\n"
        "`+warn @user [raison]` → Avertit un membre.\n"
        "`+check_warns @user` → Vérifie les avertissements d'un membre.\n"
        "`+tempban @user <durée en h> [raison]` → Banni temporairement un membre.\n"
        "`+mute @user [raison] [durée]` → Muter un membre pour une durée donnée.\n"
        "`+unmute @user` → Dé-muter un membre.\n"
        "`+lockdown <temps en min>` → Verrouille un salon.\n"
        "`+private_channel <nom_du_salon> @membre` → Crée un salon privé pour un utilisateur spécifique.\n"
        "`+roles @user` → Affiche les rôles d'un membre.\n"
        "`+nickname @user <nouveau_pseudo>` → Change le pseudonyme d'un membre.\n"
        "`+add_note @user <note>` → Ajoute une note pour un membre.\n"
        "`+show_notes @user` → Affiche les notes d'un membre."
    )
    # Diviser le texte en plusieurs champs si nécessaire
    embed.add_field(name="⚒️ Commandes de Modération", value=mod_value[:1024], inline=False)
    if len(mod_value) > 1024:
        embed.add_field(name="⚒️ Commandes de Modération (suite)", value=mod_value[1024:], inline=False)

    # Catégorie : 👑 Panneau VIP
    embed.add_field(
        name="👑 Panneau VIP",
        value=(
            "`+setup_vip_access` → Installe le panneau STG VIP dans le salon actuel.\n"
            "🔗 Le bouton **CLIQUE POUR LE STG VIP** redirige vers le salon des tickets VIP."
        ),
        inline=False
    )

    # Catégorie : 🎲 Commandes Diverses
    embed.add_field(
        name="🎲 Commandes Diverses",
        value=( 
            "`+ping` → Vérifie si le bot est en ligne.\n"
            "`+info @user` → Affiche des infos sur un membre.\n"
            "`+avatar @user` → Affiche l'avatar d'un membre.\n"
            "`+server_stats` → Affiche les statistiques du serveur.\n"
            "`+stats` → Affiche le panneau statistiques Components V2.\n"
            "`+server_info` → Affiche les informations du serveur.\n"
            "`+server_emojis` → Liste les emojis du serveur.\n"
            "`+setup_logs` → Crée/configure les salons de logs.\n"
            "`+autoping` → Configure les messages automatiques à l’arrivée.\n"
            "`+emoji add <:nom:ID>` → Importe un emoji personnalisé dans ce serveur.\n"
            "`+uptime` → Affiche le temps de fonctionnement du bot.\n"
            "`+liste` → Affiche cette liste des commandes."
        ),
        inline=False
    )

    embed.set_footer(text="Tape une commande pour l'utiliser !")
    await ctx.send(embed=embed)







# Commande antiraid
from discord.ui import View, Button, button
anti_raid_enabled = False  # On initialise la variable à False


class AntiRaidView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Activer", style=discord.ButtonStyle.success)
    async def activate(self, interaction: discord.Interaction, button: Button):
        global anti_raid_enabled
        anti_raid_enabled = True
        await interaction.response.edit_message(content="🛡️ Mode Anti-Raid **activé**.", view=self)

    @button(label="Désactiver", style=discord.ButtonStyle.danger)
    async def deactivate(self, interaction: discord.Interaction, button: Button):
        global anti_raid_enabled
        anti_raid_enabled = False
        await interaction.response.edit_message(content="🔓 Mode Anti-Raid **désactivé**.", view=self)


@bot.command()
@commands.has_permissions(administrator=True)
async def antiraid(ctx):
    """Affiche un menu pour activer ou désactiver le mode Anti-Raid."""
    view = AntiRaidView()
    await ctx.send("🛡️ Choisissez une option pour le mode Anti-Raid :", view=view)

@bot.event
async def on_member_join(member):
    global anti_raid_enabled  # On indique qu'on utilise la variable globale

    if anti_raid_enabled:
        account_age = datetime.utcnow() - member.created_at
        if account_age < timedelta(days=7):  # Compte de moins de 7 jours
            await member.kick(reason="Compte trop récent - Protection anti-raid")
            channel = discord.utils.get(member.guild.text_channels, name="logs")
            if channel:
                await channel.send(f"🚨 **{member.name}** a été expulsé (compte trop récent)")






    



 
# Commande pour afficher des informations sur un utilisateur
@bot.command()
async def info(ctx, member: discord.Member):
    embed = discord.Embed(
        title=f"Informations sur {member}",
        color=discord.Color.blue()
    )

    # Utilisation de display_avatar pour obtenir l'avatar du membre
    embed.set_thumbnail(url=member.display_avatar.url)
    
    # Ajout d'autres informations sur le membre
    embed.add_field(name="Nom", value=member.name)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Créé le", value=member.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y"))
    
    # Envoi de l'embed dans le chat
    await ctx.send(embed=embed)


# Commande pour vérifier si le bot est en ligne
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong ! Le bot est en ligne.")


# Commande pour voir l'avatar d'une persone
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author  # Si aucun membre n'est mentionné, prend l'appelant
    embed = discord.Embed(
        title=f"Avatar de {member.name}",
        color=discord.Color.blue()
    )
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)


# Commande pour voir les stats d'un serveur
@bot.command()
async def server_stats(ctx):
    server = ctx.guild
    total_channels = len(server.text_channels) + len(server.voice_channels)
    total_roles = len(server.roles)
    total_emojis = len(server.emojis)
    
    embed = discord.Embed(
        title=f"Statistiques de {server.name}",
        color=discord.Color.purple()
    )
    embed.add_field(name="Nombre de membres", value=len(server.members))
    embed.add_field(name="Nombre de canaux", value=total_channels)
    embed.add_field(name="Nombre de rôles", value=total_roles)
    embed.add_field(name="Nombre d'emojis", value=total_emojis)
    embed.set_thumbnail(url=server.icon.url)
    await ctx.send(embed=embed)


# Commande pour voir les infos d'un serveur
@bot.command()
async def server_info(ctx):
    server = ctx.guild
    embed = discord.Embed(
        title=f"Informations sur le serveur {server.name}",
        description=f"Voici quelques informations sur ce serveur.",
        color=discord.Color.green()
    )
    embed.add_field(name="Nom du serveur", value=server.name)
    embed.add_field(name="ID du serveur", value=server.id)
    embed.add_field(name="Créé le", value=server.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Membres", value=len(server.members))
    embed.set_thumbnail(url=server.icon.url)
    await ctx.send(embed=embed)


# Commande pour banlist 
@bot.command()
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    bans = await ctx.guild.bans()
    if bans:
        banned_members = "\n".join([ban.user.name for ban in bans])
        embed = discord.Embed(
            title="Liste des membres bannis",
            description=banned_members,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Il n'y a aucun membre banni sur ce serveur.")



async def uptime(ctx):
    try:
        # Vérification que start_time est bien défini
        if hasattr(bot, 'start_time'):
            uptime_duration = datetime.utcnow() - bot.start_time
            hours, remainder = divmod(uptime_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"⏳ Le bot est en ligne depuis {uptime_duration.days} jours, {hours} heures, {minutes} minutes et {seconds} secondes.")
        else:
            await ctx.send("Le temps de démarrage du bot n'est pas encore défini.")
    except Exception as e:
        # Gestion d'erreur générale pour éviter une exception non gérée
        await ctx.send(f"Une erreur s'est produite : {e}")



# Commande pour voir Liste les emojis du serveur.
@bot.command()
async def server_emojis(ctx):
    emojis = ctx.guild.emojis
    if emojis:
        emoji_list = " ".join([str(emoji) for emoji in emojis])
        embed = discord.Embed(
            title="Emojis du serveur",
            description=emoji_list,
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Il n'y a pas d'emojis personnalisés sur ce serveur.")


# Commande pour reset les roles d'une personne
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):
    roles = member.roles[1:]  # On exclut le rôle @everyone
    if roles:
        await member.remove_roles(*roles)
        await ctx.send(f"🧹 Tous les rôles de {member.mention} ont été supprimés.")
    else:
        await ctx.send(f"{member.mention} n'a aucun rôle à supprimer.")


# Commande pour Mute quelqu'un temporairement
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, reason=None, duration: str = None):
    mute_role = get(ctx.guild.roles, name="Muted")
    if not mute_role:
        perms = discord.Permissions(send_messages=False, speak=False)
        mute_role = await ctx.guild.create_role(name="Muted", permissions=perms)

    await member.add_roles(mute_role)
    await ctx.send(f"🔇 {member.mention} a été mute. Raison: {reason or 'Aucune'}.")

    if duration:
        try:
            duration = int(duration) * 60  # Convertir la durée en secondes
            await asyncio.sleep(duration)
            await member.remove_roles(mute_role)
            await ctx.send(f"🔊 {member.mention} n'est plus mute.")
        except ValueError:
            await ctx.send("⏳ Durée invalide. Utilisez un nombre.")

# Commande pour Unmute quelqu'un 
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    mute_role = get(ctx.guild.roles, name="Muted")
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(f"🔊 {member.mention} a été démuté.")
    else:
        await ctx.send(f"{member.mention} n'est pas mute.")


# Commande pour warn quelqu'un
warns = {}  # Dictionnaire pour stocker les avertissements

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.id not in warns:
        warns[member.id] = []
    warns[member.id].append(reason or "Aucune raison donnée.")
    await ctx.send(f"⚠️ {member.mention} a été averti pour: {reason or 'Aucune raison'}")


# Commande pour voir les warn des gens
@bot.command()
@commands.has_permissions(manage_messages=True)
async def check_warns(ctx, member: discord.Member):
    if member.id in warns:
        warning_count = len(warns[member.id])
        await ctx.send(f"⚠️ {member.mention} a {warning_count} avertissement(s).")
    else:
        await ctx.send(f"{member.mention} n'a aucun avertissement.")

# Commande pour TempBan @bot.command()
@commands.has_permissions(ban_members=True)
async def tempban(ctx, member: discord.Member, duration: str, *, reason=None):
    try:
        duration = int(duration) * 3600  # Convertir en secondes
        await member.ban(reason=reason)
        await ctx.send(f"⚠️ {member.mention} a été temporairement banni pour {duration // 3600} heures.")

        await asyncio.sleep(duration)
        await ctx.guild.unban(member)
        await ctx.send(f"🔓 {member.mention} a été débanni après {duration // 3600} heures.")
    except ValueError:
        await ctx.send("⏳ Durée invalide. Utilisez un nombre.")


# ============================================================
# COMMANDE POUR INSTALLER LE PANNEAU
# ============================================================




@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):

    # =========================
    # COULEUR DE L'EMBED
    # =========================
    embed = discord.Embed(
        title=" TU VEUX ACCEDER AU CONTENUS EXCLUSIFS ?",
        description=(
            "\n\n"
            "<a:verifiedred:1552279526413828149> **Suis simplement les instructions ci-dessous :**\n\n"
            "<:cerise:1554950602088382634> Va sur **TikTok**\n"
            "<:message:1554950656392044726> Recherche  **serveur discord br**\n"
            "<:langue:1554950565828497508> Ouvre **10 vidéos différentes**\n"
            "<:texte:1554952296683544616> Commente sous chaque vidéo\n\n"
            " /stgfr pour du contenue exclusif ! \n\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<:18:1554952122473259018> **Une fois les 10 preuves terminées :**\n"
            "Clique sur le bouton ci-dessous et envoie tes **10 images**.\n\n"
            "<:exclamation:1554958049536380999> Les anciennes preuves ou les fausses preuves "
            "peuvent entraîner un refus."
        ),
        color=discord.Color.from_str("#333333")
    )

    # =========================
    # BANNIÈRE
    # =========================
    file = discord.File(
        "exclusifs.png",
        filename="exclusifs.png"
    )

    embed.set_image(
        url="attachment://exclusifs.png"
    )

    # =========================
    # FOOTER
    # =========================
    embed.set_footer(
        text=" 10 images obligatoires • Vérification par le staff"
    )

    # =========================
    # ENVOI
    # =========================
    await ctx.send(
        embed=embed,
        file=file,
        view=ProofPanelView()
    )

    await ctx.send(
        f"<:point:1554955936609865778> **Panneau installé dans {ctx.channel.mention}.**"
    )


# ============================================================
# PANNEAU STG VIP (Components V2)
# ============================================================
# Nécessite discord.py 2.6 ou plus récent.
# Le bouton "CLIQUE POUR LE STG VIP" est un bouton lien : il ouvre
# directement le salon VIP_ACCESS_CHANNEL_ID (pas de ticket, pas de callback).

class VIPLayout(ui.LayoutView):
    """Panneau STG VIP : conteneur, séparateurs et bouton lien."""

    def __init__(self, channel_url: str = "https://discord.com"):
        super().__init__(timeout=None)

        c = ui.Container(accent_colour=discord.Colour.from_str("#333333"))

        # Titre + intro, logo à droite
        c.add_item(ui.Section(
            ui.TextDisplay("# <:17836minecraftredv:1557097612249669684><:17847minecraftredi:1557097679220252743><:72237minecraftredp:1557097737504165938>     <:23720minecraftreds:1557097784308535396> <:94054minecraftredt:1557097850851164280><:54257minecraftredg:1557097897864986717>"),
            ui.TextDisplay(
                "Découvrez le tout nouveau VIP STG<a:008_whiteexcl:1558922352333684740>\n"
                "Une offre exclusive, disponible uniquement sur **STG FR** "
                "<a:verifiedred:1552279526413828149>"
            ),
            accessory=ui.Thumbnail("attachment://stgfr_webhook_logo.png"),
        ))

        c.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large))

        c.add_item(ui.TextDisplay(
            "## <a:978859redcrown:1557092090574413975> Débloque immédiatement :\n"
            "<:point:1554955936609865778> <:18:1554952122473259018> Vocaux S*XCAM avec nos <@&1550556760622899361>\n"
            "<:point:1554955936609865778> <:cerise:1554950602088382634> 300 000+ contenus exclusifs sur notre espace privé VIP.\n"
            "<:point:1554955936609865778> <:langue:1554950565828497508> Accès au groupe Snapchat Showcam (places limitées).\n"
            "<:point:1554955936609865778> <:14489redheadadminroleicon:1557092022563635361> Vidéos en avant-première : compilations, événements, backstage etc.\n"
            "<:point:1554955936609865778> <:texte:1554952296683544616> Images et vidéos sans aucune restriction.\n"
            "<:point:1554955936609865778> <:62392viprubyshiny:1557092189463388160> Accès à tous les premium et VIP de tous les serveurs Discord"
        ))

        c.add_item(ui.Separator(visible=True))

        c.add_item(ui.TextDisplay(
            "## <:827263redrules:1557092326256418816> Pourquoi passer VIP ?\n"
            "<:exclamation:1554958049536380999> Seulement **1 €** pour débloquer l'intégralité des avantages.\n\n"
            "<:lestenebreswlh:1557090864684212275> Tu soutiens directement l'évolution de STG et le "
            "développement de nouveaux événements et fonctionnalités."
        ))

        c.add_item(ui.Separator(visible=True))

        c.add_item(ui.TextDisplay(
            "## <:couronne:1554951807367913583> Rejoins le VIP dès maintenant !\n"
            "Clique sur le bouton ci-dessous et profite immédiatement de tous les avantages.\n\n"
        ))

        c.add_item(ui.Separator(visible=True))

        # Texte à gauche + bouton lien vers le salon à droite
        c.add_item(ui.Section(
            ui.TextDisplay("Clique sur le bouton afin d'accéder au VIP"),
            accessory=ui.Button(
                label="CLIQUE POUR LE STG VIP",
                style=discord.ButtonStyle.link,
                url=channel_url,
            ),
        ))

        self.add_item(c)


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_vip_access(ctx):
    """Envoie le panneau STG VIP dans le salon actuel."""

    if not STGFR_WEBHOOK_LOGO_PATH.exists():
        await ctx.send(
            "❌ Le fichier `stgfr_webhook_logo.png` est introuvable à côté de `bot.py`."
        )
        return

    # Lien vers le salon #🎫・tickets-vip (le bouton ouvre ce salon)
    channel_url = f"https://discord.com/channels/{ctx.guild.id}/{VIP_ACCESS_CHANNEL_ID}"

    await ctx.send(
        view=VIPLayout(channel_url),
        file=discord.File(STGFR_WEBHOOK_LOGO_PATH, filename="stgfr_webhook_logo.png"),
        allowed_mentions=discord.AllowedMentions.none()
    )

    # On supprime le message de commande pour laisser uniquement le panneau.
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass




# ============================================================
# SYSTÈME DE LOGS + PANEL DE CONFIGURATION
# ============================================================

LOG_CONFIG_FILE = Path(__file__).parent / "logs_config.json"
LOG_TYPES = {
    "serveur": ("⚙️", "Serveur"),
    "role": ("🎭", "Rôles"),
    "messages": ("💬", "Messages"),
    "salon": ("🛠️", "Modifications salons"),
    "vc": ("🔊", "Vocaux"),
    "automods": ("🛡️", "AutoMod"),
    "membres": ("👤", "Membres"),
    "invites": ("🔗", "Invitations"),
    "join": ("📥", "Arrivées"),
    "leave": ("📤", "Départs"),
    "channel": ("📁", "Création/suppression salons"),
}


def load_logs_config():
    try:
        if LOG_CONFIG_FILE.exists():
            raw = json.loads(LOG_CONFIG_FILE.read_text(encoding="utf-8"))
            return {str(gid): {str(k): int(v) for k, v in cfg.items()} for gid, cfg in raw.items()}
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"⚠️ Configuration logs non chargée : {error}")
    return {}


logs_config = load_logs_config()


def save_logs_config():
    LOG_CONFIG_FILE.write_text(json.dumps(logs_config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_log_channel(guild: discord.Guild, kind: str):
    channel_id = logs_config.get(str(guild.id), {}).get(kind)
    return guild.get_channel(channel_id) if channel_id else None


async def send_log(guild: discord.Guild, kind: str, embed: discord.Embed):
    channel = get_log_channel(guild, kind)
    if channel is None:
        return
    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException) as error:
        print(f"⚠️ Logs {kind} impossibles dans {guild.name}: {error}")


def log_embed(title: str, description: str = "", color=discord.Color.blurple()):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
    embed.set_footer(text="STG - Système de logs")
    return embed


def build_logs_panel_embed(guild: discord.Guild):
    cfg = logs_config.get(str(guild.id), {})
    lines = []
    for key, (emoji, label) in LOG_TYPES.items():
        channel = guild.get_channel(cfg.get(key)) if cfg.get(key) else None
        lines.append(f"{emoji} **{label}** → {channel.mention if channel else '`Non configuré`'}")
    return discord.Embed(
        title="⚙️ CONFIGURATION DES LOGS",
        description=(
            "Choisis d’abord une catégorie de logs, puis sélectionne le salon où elle doit être envoyée.\n\n"
            + "\n".join(lines)
        ),
        color=0x333333
    ).set_footer(text="STGFR • Configuration des logs")


class LogTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=label, value=key, emoji=emoji) for key, (emoji, label) in LOG_TYPES.items()]
        super().__init__(placeholder="1️⃣ Choisir le type de logs", min_values=1, max_values=1, options=options, custom_id="logs:type")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return
        view = LogChannelPickerView(self.values[0])
        await interaction.response.send_message(
            f"📍 Choisis maintenant le salon pour **{LOG_TYPES[self.values[0]][1]}** :",
            view=view,
            ephemeral=True
        )


class LogChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, log_kind: str):
        self.log_kind = log_kind
        super().__init__(
            placeholder="2️⃣ Choisir le salon de destination",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        guild_cfg = logs_config.setdefault(str(interaction.guild.id), {})
        guild_cfg[self.log_kind] = channel.id
        save_logs_config()
        await interaction.response.send_message(
            f"✅ **{LOG_TYPES[self.log_kind][1]}** sera maintenant envoyé dans {channel.mention}.",
            ephemeral=True
        )


class LogChannelPickerView(discord.ui.View):
    def __init__(self, log_kind: str):
        super().__init__(timeout=120)
        self.add_item(LogChannelSelect(log_kind))


class LogsConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LogTypeSelect())

    @discord.ui.button(label="Actualiser", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="logs:refresh")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=build_logs_panel_embed(interaction.guild), view=self)

    @discord.ui.button(label="Désactiver tout", emoji="🔴", style=discord.ButtonStyle.danger, custom_id="logs:disable_all")
    async def disable_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return
        logs_config[str(interaction.guild.id)] = {}
        save_logs_config()
        await interaction.response.edit_message(embed=build_logs_panel_embed(interaction.guild), view=self)


@bot.command(name="setup_logs")
@commands.has_permissions(administrator=True)
async def setup_logs(ctx):
    """Affiche le panel interactif permettant d'assigner chaque type de log à un salon."""
    await ctx.send(embed=build_logs_panel_embed(ctx.guild), view=LogsConfigView())


# ----- Arrivées / départs -----
@bot.listen("on_member_join")
async def logs_member_join(member: discord.Member):
    embed = log_embed("📥 Membre arrivé", f"{member.mention} a rejoint le serveur.", discord.Color.green())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Utilisateur", value=f"{member} (`{member.id}`)", inline=False)
    embed.add_field(name="Compte créé", value=discord.utils.format_dt(member.created_at, style="R"), inline=True)
    embed.add_field(name="Nombre de membres", value=str(member.guild.member_count), inline=True)
    await send_log(member.guild, "join", embed)


@bot.listen("on_member_remove")
async def logs_member_leave(member: discord.Member):
    embed = log_embed("📤 Membre parti", f"{member.mention} a quitté le serveur.", discord.Color.red())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Utilisateur", value=f"{member} (`{member.id}`)", inline=False)
    embed.add_field(name="Nombre de membres", value=str(member.guild.member_count), inline=True)
    await send_log(member.guild, "leave", embed)


# ----- Modifications des membres et rôles -----
@bot.listen("on_member_update")
async def logs_member_update(before: discord.Member, after: discord.Member):
    if before.nick != after.nick:
        embed = log_embed("✏️ Pseudonyme modifié", f"{after.mention}", discord.Color.orange())
        embed.add_field(name="Avant", value=before.nick or before.name, inline=True)
        embed.add_field(name="Après", value=after.nick or after.name, inline=True)
        embed.add_field(name="ID utilisateur", value=str(after.id), inline=False)
        await send_log(after.guild, "membres", embed)

    before_roles = set(before.roles)
    after_roles = set(after.roles)
    added = after_roles - before_roles
    removed = before_roles - after_roles
    if added or removed:
        embed = log_embed("🎭 Rôles d'un membre modifiés", f"{after.mention}", discord.Color.gold())
        if added:
            embed.add_field(name="Rôle(s) ajouté(s)", value="\n".join(r.mention for r in added), inline=False)
        if removed:
            embed.add_field(name="Rôle(s) retiré(s)", value="\n".join(r.name for r in removed), inline=False)
        embed.add_field(name="ID utilisateur", value=str(after.id), inline=False)
        await send_log(after.guild, "membres", embed)


@bot.listen("on_guild_role_create")
async def logs_role_create(role: discord.Role):
    embed = log_embed("➕ Rôle créé", role.mention, discord.Color.green())
    embed.add_field(name="Nom", value=role.name, inline=True)
    embed.add_field(name="ID", value=str(role.id), inline=True)
    await send_log(role.guild, "role", embed)


@bot.listen("on_guild_role_delete")
async def logs_role_delete(role: discord.Role):
    embed = log_embed("➖ Rôle supprimé", f"**{role.name}**", discord.Color.red())
    embed.add_field(name="ID", value=str(role.id), inline=True)
    await send_log(role.guild, "role", embed)


@bot.listen("on_guild_role_update")
async def logs_role_update(before: discord.Role, after: discord.Role):
    changes = []
    if before.name != after.name:
        changes.append(f"**Nom :** `{before.name}` → `{after.name}`")
    if before.permissions != after.permissions:
        changes.append("**Permissions :** modifiées")
    if before.colour != after.colour:
        changes.append(f"**Couleur :** `{before.colour}` → `{after.colour}`")
    if changes:
        embed = log_embed("🛠️ Rôle modifié", "\n".join(changes), discord.Color.orange())
        embed.add_field(name="Rôle", value=f"{after.mention} (`{after.id}`)", inline=False)
        await send_log(after.guild, "role", embed)


# ----- Messages -----
@bot.listen("on_message_delete")
async def logs_message_delete(message: discord.Message):
    if message.guild is None or message.author.bot:
        return
    embed = log_embed("🗑️ Message supprimé", discord.utils.escape_markdown(message.content[:3500]) or "*Aucun texte*", discord.Color.red())
    embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
    embed.add_field(name="Auteur", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
    embed.add_field(name="Salon", value=message.channel.mention, inline=True)
    if message.attachments:
        embed.add_field(name="Pièces jointes", value="\n".join(a.url for a in message.attachments[:5]), inline=False)
    await send_log(message.guild, "messages", embed)


@bot.listen("on_message_edit")
async def logs_message_edit(before: discord.Message, after: discord.Message):
    if before.guild is None or before.author.bot or before.content == after.content:
        return
    embed = log_embed("✏️ Message modifié", color=discord.Color.orange())
    embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
    embed.add_field(name="Avant", value=discord.utils.escape_markdown(before.content[:1000]) or "*Vide*", inline=False)
    embed.add_field(name="Après", value=discord.utils.escape_markdown(after.content[:1000]) or "*Vide*", inline=False)
    embed.add_field(name="Salon", value=before.channel.mention, inline=True)
    embed.add_field(name="Lien", value=f"[Voir le message]({after.jump_url})", inline=True)
    await send_log(before.guild, "messages", embed)


# ----- Salons texte / vocaux -----
@bot.listen("on_guild_channel_create")
async def logs_channel_create(channel):
    embed = log_embed("➕ Salon créé", f"{channel.mention if hasattr(channel, 'mention') else channel.name}", discord.Color.green())
    embed.add_field(name="Nom", value=channel.name, inline=True)
    embed.add_field(name="ID", value=str(channel.id), inline=True)
    embed.add_field(name="Type", value=str(channel.type), inline=True)
    await send_log(channel.guild, "channel", embed)


@bot.listen("on_guild_channel_delete")
async def logs_channel_delete(channel):
    embed = log_embed("➖ Salon supprimé", f"**{channel.name}**", discord.Color.red())
    embed.add_field(name="ID", value=str(channel.id), inline=True)
    embed.add_field(name="Type", value=str(channel.type), inline=True)
    await send_log(channel.guild, "channel", embed)


@bot.listen("on_guild_channel_update")
async def logs_channel_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f"**Nom :** `{before.name}` → `{after.name}`")
    if getattr(before, "category_id", None) != getattr(after, "category_id", None):
        changes.append("**Catégorie :** modifiée")
    if getattr(before, "position", None) != getattr(after, "position", None):
        changes.append("**Position :** modifiée")
    if changes:
        embed = log_embed("🛠️ Salon modifié", "\n".join(changes), discord.Color.orange())
        embed.add_field(name="Salon", value=f"{after.mention} (`{after.id}`)", inline=False)
        await send_log(after.guild, "salon", embed)


@bot.listen("on_voice_state_update")
async def logs_voice_state(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel == after.channel:
        return
    if before.channel is None and after.channel is not None:
        text = f"{member.mention} a rejoint **{after.channel.name}**."
        title = "🔊 Connexion vocale"
        color = discord.Color.green()
    elif before.channel is not None and after.channel is None:
        text = f"{member.mention} a quitté **{before.channel.name}**."
        title = "🔇 Déconnexion vocale"
        color = discord.Color.red()
    else:
        text = f"{member.mention} est passé de **{before.channel.name}** à **{after.channel.name}**."
        title = "🔁 Déplacement vocal"
        color = discord.Color.orange()
    embed = log_embed(title, text, color)
    embed.add_field(name="ID utilisateur", value=str(member.id), inline=False)
    await send_log(member.guild, "vc", embed)


# ----- Serveur / bans -----
@bot.listen("on_member_ban")
async def logs_member_ban(guild: discord.Guild, user: discord.User):
    embed = log_embed("🔨 Membre banni", f"{user.mention} a été banni.", discord.Color.red())
    embed.add_field(name="Utilisateur", value=f"{user} (`{user.id}`)", inline=False)
    await send_log(guild, "serveur", embed)


@bot.listen("on_member_unban")
async def logs_member_unban(guild: discord.Guild, user: discord.User):
    embed = log_embed("🔓 Membre débanni", f"{user.mention} a été débanni.", discord.Color.green())
    embed.add_field(name="Utilisateur", value=f"{user} (`{user.id}`)", inline=False)
    await send_log(guild, "serveur", embed)


@bot.listen("on_guild_update")
async def logs_guild_update(before: discord.Guild, after: discord.Guild):
    changes = []
    if before.name != after.name:
        changes.append(f"**Nom :** `{before.name}` → `{after.name}`")
    if before.verification_level != after.verification_level:
        changes.append(f"**Niveau de vérification :** `{before.verification_level}` → `{after.verification_level}`")
    if changes:
        await send_log(after, "serveur", log_embed("⚙️ Serveur modifié", "\n".join(changes), discord.Color.orange()))


# ----- Invitations -----
@bot.listen("on_invite_create")
async def logs_invite_create(invite: discord.Invite):
    if invite.guild is None:
        return
    embed = log_embed("🔗 Invitation créée", f"Code : `{invite.code}`", discord.Color.green())
    if invite.inviter:
        embed.add_field(name="Créée par", value=f"{invite.inviter.mention} (`{invite.inviter.id}`)", inline=False)
    embed.add_field(name="Salon", value=invite.channel.mention if invite.channel else "Inconnu", inline=True)
    embed.add_field(name="Utilisations max", value=str(invite.max_uses or "Illimité"), inline=True)
    await send_log(invite.guild, "invites", embed)


@bot.listen("on_invite_delete")
async def logs_invite_delete(invite: discord.Invite):
    if invite.guild is None:
        return
    embed = log_embed("🗑️ Invitation supprimée", f"Code : `{invite.code}`", discord.Color.red())
    await send_log(invite.guild, "invites", embed)


# ----- AutoMod Discord -----
@bot.listen("on_automod_rule_create")
async def logs_automod_create(rule):
    embed = log_embed("🛡️ Règle AutoMod créée", f"**{rule.name}**", discord.Color.green())
    embed.add_field(name="ID", value=str(rule.id), inline=True)
    await send_log(rule.guild, "automods", embed)


@bot.listen("on_automod_rule_update")
async def logs_automod_update(rule):
    embed = log_embed("🛡️ Règle AutoMod modifiée", f"**{rule.name}**", discord.Color.orange())
    embed.add_field(name="ID", value=str(rule.id), inline=True)
    await send_log(rule.guild, "automods", embed)


@bot.listen("on_automod_rule_delete")
async def logs_automod_delete(rule):
    embed = log_embed("🛡️ Règle AutoMod supprimée", f"**{rule.name}**", discord.Color.red())
    embed.add_field(name="ID", value=str(rule.id), inline=True)
    await send_log(rule.guild, "automods", embed)


@bot.listen("on_automod_action_execution")
async def logs_automod_action(execution):
    guild = bot.get_guild(execution.guild_id)
    if guild is None:
        return
    embed = log_embed("🚨 Action AutoMod déclenchée", discord.Color.red())
    embed.description = f"Une règle AutoMod a été déclenchée pour <@{execution.user_id}>."
    embed.add_field(name="Utilisateur", value=f"<@{execution.user_id}> (`{execution.user_id}`)", inline=False)
    if execution.channel_id:
        embed.add_field(name="Salon", value=f"<#{execution.channel_id}>", inline=True)
    await send_log(guild, "automods", embed)


# ============================================================
# INITIALISATION DES BOUTONS PERSISTANTS
# ============================================================

@bot.event
async def setup_hook():

    # Panel persistant de configuration des logs
    bot.add_view(LogsConfigView())

    # Bouton "ENVOYER LES PREUVES"
    bot.add_view(ProofPanelView())

    # Boutons VALIDER / REFUSER
    bot.add_view(ProofReviewView())


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            f"❌ Commande inconnue : `{ctx.message.content}`\n"
            f"Commandes disponibles : `+liste`"
        )
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu n'as pas les permissions nécessaires.")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"❌ Argument manquant : `{error.param.name}`"
        )
        return

    print(f"ERREUR COMMANDE : {repr(error)}")



# ============================================================
# SYSTÈME DE VALIDATION DES PREUVES
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif"
}


# ============================================================
# PANNEAU PRINCIPAL
# ============================================================

class ProofPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # ========================================================
    # BOUTON ENVOYER LES PREUVES
    # ========================================================

    @discord.ui.button(
        label="ENVOYER LES PREUVES",
        emoji="📸",
        style=discord.ButtonStyle.success,  # 🟢 VERT
        custom_id="proof_send_button"
    )
    async def send_proofs(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            ProofModal()
        )

    # ========================================================
    # BOUTON COPIER
    # ========================================================

    @discord.ui.button(
        label="COPIER",
        emoji="📋",
        style=discord.ButtonStyle.danger,  # 🔴 ROUGE
        custom_id="proof_copy_button"
    )
    async def copy_command(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        embed = discord.Embed(
            title="📋 COMMANDE À COPIER",
            description=(
                "```text\n"
                "/stgfr pour du contenue exclusif !"
                "\n```"
                "\n➡️ Copie cette commande puis utilise-la."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# ============================================================
# MODAL D'UPLOAD
# ============================================================

class ProofModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            title="Envoyer les preuves",
            custom_id="proof_modal"
        )

        self.images = discord.ui.FileUpload(
            custom_id="proof_images",
            min_values=10,
            max_values=10,
            required=True
        )

        self.add_item(
            discord.ui.Label(
                text="Tes 10 preuves",
                description="Sélectionne exactement 10 images.",
                component=self.images
            )
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        files = list(self.images.values)

        # ----------------------------------------------------
        # Vérification du nombre d'images
        # ----------------------------------------------------

        if len(files) != 10:

            await interaction.response.send_message(
                "❌ Tu dois envoyer exactement **10 images**.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # Vérification des types de fichiers
        # ----------------------------------------------------

        for file in files:

            if file.content_type not in ALLOWED_IMAGE_TYPES:

                await interaction.response.send_message(
                    f"❌ `{file.filename}` n'est pas une image valide.",
                    ephemeral=True
                )

                return

        # ----------------------------------------------------
        # Récupération du salon de vérification
        # ----------------------------------------------------

        review_channel = interaction.guild.get_channel(
            PROOF_REVIEW_CHANNEL_ID
        )

        if review_channel is None:

            await interaction.response.send_message(
                "❌ Le salon de vérification n'existe pas.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        # ----------------------------------------------------
        # Téléchargement des 10 images
        # ----------------------------------------------------

        discord_files = []

        for attachment in files:

            try:

                data = await attachment.read()

                discord_files.append(
                    discord.File(
                        fp=__import__("io").BytesIO(data),
                        filename=attachment.filename
                    )
                )

            except Exception as e:

                print(
                    f"Erreur avec {attachment.filename}: {e}"
                )

        # ----------------------------------------------------
        # Embed de la demande
        # ----------------------------------------------------

        embed = discord.Embed(
            title="📥 NOUVELLE DEMANDE",
            description=(
                f"👤 **Utilisateur :** {interaction.user.mention}\n"
                f"🆔 **ID :** `{interaction.user.id}`\n\n"
                f"📸 **Preuves reçues :** `10/10`\n\n"
                "Vérifiez les 10 images ci-dessous puis "
                "choisissez une action."
            ),
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.set_footer(
            text=f"Demande envoyée par {interaction.user}"
        )

        # ----------------------------------------------------
        # Envoi au salon staff
        # ----------------------------------------------------

        await review_channel.send(
            embed=embed,
            files=discord_files,
            view=ProofReviewView()
        )

        # ----------------------------------------------------
        # Confirmation à l'utilisateur
        # ----------------------------------------------------

        await interaction.followup.send(
            "✅ **Tes 10 preuves ont bien été envoyées !**\n\n"
            "Elles vont maintenant être vérifiées par le staff.",
            ephemeral=True
        )


# ============================================================
# PANNEAU STAFF
# ============================================================

class ProofReviewView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # ========================================================
    # VALIDER
    # ========================================================

    @discord.ui.button(
        label="VALIDER",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="proof_validate"
    )
    async def validate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # Vérification permission
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission de traiter cette demande.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Récupérer l'utilisateur depuis l'embed
        # ----------------------------------------------------

        if not interaction.message.embeds:
            await interaction.response.send_message(
                "❌ Impossible de trouver l'utilisateur.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]
        user_id = None

        if embed.description:
            for line in embed.description.split("\n"):
                if "ID :" in line:
                    try:
                        user_id = int(line.split("`")[1])
                    except (ValueError, IndexError):
                        pass

        if user_id is None:
            await interaction.response.send_message(
                "❌ ID utilisateur introuvable.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Récupération du membre
        # ----------------------------------------------------

        member = interaction.guild.get_member(user_id)

        if member is None:
            try:
                member = await interaction.guild.fetch_member(user_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ L'utilisateur n'est plus sur le serveur.",
                    ephemeral=True
                )
                return

        # ----------------------------------------------------
        # Récupération du rôle
        # ----------------------------------------------------

        role = interaction.guild.get_role(PROOF_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ Le rôle configuré est introuvable.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Vérification hiérarchie
        # ----------------------------------------------------

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ Je ne peux pas donner ce rôle.\n\n"
                "Place le rôle de mon bot **au-dessus** "
                "du rôle que je dois attribuer.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Attribution du rôle
        # ----------------------------------------------------

        try:
            await member.add_roles(
                role,
                reason=f"Demande de preuves validée par {interaction.user}"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Discord m'empêche de donner ce rôle.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Message dans le salon des validations
        # ----------------------------------------------------

        success_channel = interaction.guild.get_channel(
            PROOF_SUCCESS_CHANNEL_ID
        )

        if success_channel:
            await success_channel.send(
                f"✓ {member.mention} Tu as bien reçu l'accès "
                f"à la zone exclusif! "
            )

        # ----------------------------------------------------
        # Désactiver les boutons
        # ----------------------------------------------------

        for child in self.children:
            child.disabled = True

        # ----------------------------------------------------
        # Modifier l'embed
        # ----------------------------------------------------

        embed.color = discord.Color.green()

        embed.add_field(
            name="📋 DÉCISION",
            value=(
                "✅ **DEMANDE VALIDÉE**\n"
                f"👮 Validée par : {interaction.user.mention}\n"
                f"🎖️ Rôle donné : {role.mention}"
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # ----------------------------------------------------
        # Message privé
        # ----------------------------------------------------

        try:
            await member.send(
                f"🎉 **Ta demande a été validée !**\n\n"
                f"Tu as reçu le rôle **{role.name}** "
                f"sur **{interaction.guild.name}**."
            )

        except discord.Forbidden:
            pass

        # ========================================================
    # REFUSER
    # ========================================================

    @discord.ui.button(
        label="REFUSER",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="proof_reject"
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # ----------------------------------------------------
        # Vérification permission staff
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission de traiter cette demande.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # Récupérer l'utilisateur depuis l'embed
        # ----------------------------------------------------

        user_id = None

        if interaction.message.embeds:
            embed = interaction.message.embeds[0]

            if embed.description:
                for line in embed.description.split("\n"):
                    if "ID :" in line:
                        try:
                            user_id = int(line.split("`")[1])
                        except (ValueError, IndexError):
                            pass

        # ----------------------------------------------------
        # Désactiver les boutons
        # ----------------------------------------------------

        for child in self.children:
            child.disabled = True

        # ----------------------------------------------------
        # Modifier l'embed
        # ----------------------------------------------------

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()

        embed.add_field(
            name="📋 DÉCISION",
            value=(
                "❌ **DEMANDE REFUSÉE**\n"
                f"👮 Refusée par : {interaction.user.mention}"
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # ----------------------------------------------------
        # Envoyer un message privé à la personne refusée
        # ----------------------------------------------------

        if user_id:

            member = interaction.guild.get_member(user_id)

            if member is None:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                except discord.NotFound:
                    member = None

            if member:

                try:
                    await member.send(
                        f"❌ **Ta demande a été refusée.**\n\n"
                        f"Ta demande d'accès aux contenus exclusifs sur "
                        f"**{interaction.guild.name}** n'a pas été validée "
                        f"par le staff.\n\n"
                        f"📸 Vérifie que tes **10 preuves** sont correctes "
                        f"et correspondent bien aux consignes avant de "
                        f"faire une nouvelle demande.\n\n"
                        f"💡 Si tu penses qu'il s'agit d'une erreur, "
                        f"contacte le staff."
                    )

                except discord.Forbidden:
                    # Les MP de l'utilisateur sont probablement fermés
                    print(
                        f"⚠️ Impossible d'envoyer un MP à {member} "
                        f"(ID: {member.id})"
                    )



# ============================================================
# GHOST PING AUTOMATIQUE - /setghostping
# ============================================================
GHOSTPING_CONFIG_FILE = Path(__file__).parent / "ghostping_config.json"
GHOSTPING_INTERVALS = {"2h": 2, "5h": 5, "10h": 10, "24h": 24}


def load_ghostping_config():
    try:
        if GHOSTPING_CONFIG_FILE.exists():
            raw = json.loads(GHOSTPING_CONFIG_FILE.read_text(encoding="utf-8"))
            return {str(gid): cfg for gid, cfg in raw.items() if isinstance(cfg, dict)}
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"⚠️ Configuration ghost ping non chargée : {error}")
    return {}


ghostping_config = load_ghostping_config()


def save_ghostping_config():
    try:
        GHOSTPING_CONFIG_FILE.write_text(
            json.dumps(ghostping_config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except OSError as error:
        print(f"⚠️ Configuration ghost ping non enregistrée : {error}")



# ============================================================
# +stats - PANNEAU STATISTIQUES (Components V2)
# ============================================================

# Record vocal conservé en mémoire depuis le démarrage du bot.
# Il est mis à jour à chaque connexion/déconnexion/déplacement vocal.
voice_peak_by_guild = {}


def current_voice_members(guild: discord.Guild) -> int:
    """Nombre de membres actuellement connectés dans un salon vocal."""
    return sum(len(channel.members) for channel in guild.voice_channels)


def refresh_voice_peak(guild: discord.Guild) -> int:
    current = current_voice_members(guild)
    previous = voice_peak_by_guild.get(guild.id, 0)
    voice_peak_by_guild[guild.id] = max(previous, current)
    return voice_peak_by_guild[guild.id]


@bot.listen("on_voice_state_update")
async def stats_voice_peak_listener(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    refresh_voice_peak(member.guild)


def build_stats_layout(guild: discord.Guild):
    """Construit le panneau +stats en Components V2."""
    members = guild.member_count or len(guild.members)
    bots = sum(1 for member in guild.members if member.bot)

    # Requiert l'intent Presence dans le Developer Portal.
    online = sum(
        1 for member in guild.members
        if not member.bot and getattr(member, "status", discord.Status.offline) != discord.Status.offline
    )

    voice_now = current_voice_members(guild)
    voice_peak = refresh_voice_peak(guild)
    active_channels = len(guild.text_channels) + len(guild.voice_channels)

    container = ui.Container(accent_colour=discord.Colour.from_str("#333333"))

    title = f"## {guild.name} 🏆 📈 Statistiques"
    voice_text = (
        f"# 🔊 {voice_peak:,}".replace(",", " ")
        + "\n"
        + f"record vocal depuis le démarrage • actuellement : **{voice_now:,}**".replace(",", " ")
    )

    if guild.icon:
        container.add_item(
            ui.Section(
                ui.TextDisplay(title),
                ui.TextDisplay(voice_text),
                accessory=ui.Thumbnail(guild.icon.url),
            )
        )
    else:
        container.add_item(ui.TextDisplay(title + "\n" + voice_text))

    container.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

    stats_text = (
        f"*Membres :* **{members:,}**\n"
        f"*En ligne :* **{online:,}**\n"
        f"*En vocal :* **{voice_now:,}**\n"
        f"*Salons actifs :* **{active_channels:,}**\n"
        f"*Boosts :* **{guild.premium_subscription_count:,}**"
    ).replace(",", " ")
    container.add_item(ui.TextDisplay(stats_text))

    view = ui.LayoutView(timeout=180)
    view.add_item(container)
    return view


@bot.command(name="stats")
async def stats(ctx):
    """Affiche les statistiques du serveur dans un panneau Components V2."""
    if ctx.guild is None:
        await ctx.send("❌ Cette commande doit être utilisée dans un serveur.")
        return

    await ctx.send(view=build_stats_layout(ctx.guild))

    # Comme sur l'exemple : on laisse uniquement le panneau si possible.
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass


# ============================================================
# AUTO PING À L'ARRIVÉE - +autoping (Components V2)
# ============================================================

AUTOPING_CONFIG_FILE = Path(__file__).parent / "autoping_config.json"


def load_autoping_config():
    try:
        if AUTOPING_CONFIG_FILE.exists():
            raw = json.loads(AUTOPING_CONFIG_FILE.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"⚠️ Configuration autoping non chargée : {error}")
    return {}


autoping_config = load_autoping_config()


def save_autoping_config():
    try:
        AUTOPING_CONFIG_FILE.write_text(
            json.dumps(autoping_config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except OSError as error:
        print(f"⚠️ Configuration autoping non enregistrée : {error}")


def get_autoping_guild_config(guild_id: int):
    return autoping_config.setdefault(str(guild_id), {"enabled": True, "channels": {}})


def render_autoping_message(template: str, member: discord.Member):
    replacements = {
        "{mention}": member.mention,
        "{member}": member.display_name,
        "{user}": member.name,
        "{server}": member.guild.name,
        "{count}": str(member.guild.member_count or len(member.guild.members)),
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result[:2000]


class AutoPingMessageModal(discord.ui.Modal, title="Configurer l'AutoPing"):
    message_text = discord.ui.TextInput(
        label="Message envoyé à l'arrivée",
        style=discord.TextStyle.paragraph,
        placeholder="Bienvenue {mention} sur {server} !",
        max_length=1900,
        required=True
    )
    delete_delay = discord.ui.TextInput(
        label="Suppression après combien de secondes ?",
        placeholder="Exemple : 10 (0 = ne pas supprimer)",
        max_length=5,
        required=True
    )

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        cfg = get_autoping_guild_config(panel.guild.id)
        existing = cfg.get("channels", {}).get(str(panel.selected_channel_id), {})
        self.message_text.default = existing.get("message", "Bienvenue {mention} sur **{server}** !")
        self.delete_delay.default = str(existing.get("delete_delay", 10))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé à l'administrateur qui a ouvert ce panel.", ephemeral=True)
            return
        try:
            delay = int(str(self.delete_delay.value).strip())
        except ValueError:
            await interaction.response.send_message("❌ Le délai doit être un nombre de secondes.", ephemeral=True)
            return
        if delay < 0 or delay > 86400:
            await interaction.response.send_message("❌ Choisis un délai entre **0 et 86400 secondes**.", ephemeral=True)
            return

        cfg = get_autoping_guild_config(interaction.guild.id)
        cfg["enabled"] = True
        cfg.setdefault("channels", {})[str(self.panel.selected_channel_id)] = {
            "message": str(self.message_text.value),
            "delete_delay": delay,
            "enabled": True,
        }
        save_autoping_config()
        await interaction.response.send_message(
            f"✅ AutoPing enregistré pour <#{self.panel.selected_channel_id}>. Délai : **{delay}s**.",
            ephemeral=True
        )


class AutoPingChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(
            placeholder="📢 Choisir un salon à configurer",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            custom_id="autoping:channel"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return
        self.panel.selected_channel_id = self.values[0].id
        await interaction.response.edit_message(view=self.panel.rebuild())


class AutoPingConfigureButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(label="Configurer le message", emoji="✏️", style=discord.ButtonStyle.primary, custom_id="autoping:configure")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return
        if not self.panel.selected_channel_id:
            await interaction.response.send_message("❌ Sélectionne d'abord un salon.", ephemeral=True)
            return
        await interaction.response.send_modal(AutoPingMessageModal(self.panel))


class AutoPingToggleButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        enabled = get_autoping_guild_config(panel.guild.id).get("enabled", True)
        super().__init__(
            label="Désactiver tout" if enabled else "Activer tout",
            emoji="⛔" if enabled else "✅",
            style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success,
            custom_id="autoping:toggle"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return
        cfg = get_autoping_guild_config(interaction.guild.id)
        cfg["enabled"] = not cfg.get("enabled", True)
        save_autoping_config()
        await interaction.response.edit_message(view=self.panel.rebuild())


class AutoPingRemoveButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(label="Retirer ce salon", emoji="🗑️", style=discord.ButtonStyle.secondary, custom_id="autoping:remove")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return
        if not self.panel.selected_channel_id:
            await interaction.response.send_message("❌ Sélectionne d'abord un salon.", ephemeral=True)
            return
        cfg = get_autoping_guild_config(interaction.guild.id)
        removed = cfg.setdefault("channels", {}).pop(str(self.panel.selected_channel_id), None)
        save_autoping_config()
        notice = "🗑️ **Configuration retirée de ce salon.**" if removed else "ℹ️ **Ce salon n'était pas configuré.**"
        await interaction.response.edit_message(view=self.panel.rebuild(notice=notice))


class AutoPingTestButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(label="Tester", emoji="🧪", style=discord.ButtonStyle.secondary, custom_id="autoping:test")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return
        if not self.panel.selected_channel_id:
            await interaction.response.send_message("❌ Sélectionne d'abord un salon.", ephemeral=True)
            return
        cfg = get_autoping_guild_config(interaction.guild.id).get("channels", {}).get(str(self.panel.selected_channel_id))
        channel = interaction.guild.get_channel(self.panel.selected_channel_id)
        if not cfg or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Configure d'abord ce salon.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await channel.send(
                render_autoping_message(cfg["message"], interaction.user),
                delete_after=cfg.get("delete_delay") or None,
                allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=True)
            )
            await interaction.followup.send("✅ Message de test envoyé.", ephemeral=True)
        except (discord.Forbidden, discord.HTTPException) as error:
            await interaction.followup.send(f"❌ Envoi impossible : `{error}`", ephemeral=True)


class AutoPingPanel(discord.ui.LayoutView):
    def __init__(self, owner_id: int, guild: discord.Guild, selected_channel_id=None, notice=None):
        super().__init__(timeout=900)
        self.owner_id = owner_id
        self.guild = guild
        self.selected_channel_id = selected_channel_id
        self.notice = notice
        self._build()

    def _build(self):
        cfg = get_autoping_guild_config(self.guild.id)
        channels_cfg = cfg.get("channels", {})
        enabled = cfg.get("enabled", True)
        configured_lines = []
        for channel_id, data in channels_cfg.items():
            channel = self.guild.get_channel(int(channel_id))
            if channel:
                delay = data.get("delete_delay", 0)
                preview = str(data.get("message", "")).replace("\n", " ")
                if len(preview) > 55:
                    preview = preview[:52] + "..."
                configured_lines.append(f"• {channel.mention} • `{delay}s` • {preview}")
        configured_text = "\n".join(configured_lines[:12]) or "*Aucun salon configuré pour le moment.*"
        selected = f"<#{self.selected_channel_id}>" if self.selected_channel_id else "*Aucun salon sélectionné*"

        c = discord.ui.Container(accent_color=0xED4245)
        c.add_item(discord.ui.TextDisplay(
            "# 🔔 AUTO PING • ARRIVÉE MEMBRE\n"
            "Envoie automatiquement un message dans **un ou plusieurs salons** dès qu'un membre rejoint le serveur."
        ))
        c.add_item(discord.ui.Separator())
        c.add_item(discord.ui.TextDisplay(
            f"### 🛡️ État\n{'🟢 **Activé**' if enabled else '🔴 **Désactivé**'}\n\n"
            f"### 🎯 Salon en cours\n{selected}\n\n"
            f"### 📋 Salons configurés\n{configured_text}"
        ))
        if self.notice:
            c.add_item(discord.ui.Separator())
            c.add_item(discord.ui.TextDisplay(self.notice))
        c.add_item(discord.ui.Separator())
        c.add_item(discord.ui.TextDisplay(
            "### 1️⃣ Choisis un salon\n"
            "Chaque salon peut avoir **son propre message** et **son propre délai de suppression**."
        ))
        c.add_item(discord.ui.ActionRow(AutoPingChannelSelect(self)))
        c.add_item(discord.ui.TextDisplay(
            "### 2️⃣ Configure le message\n"
            "Variables : `{mention}` • `{member}` • `{user}` • `{server}` • `{count}`"
        ))
        c.add_item(discord.ui.ActionRow(
            AutoPingConfigureButton(self),
            AutoPingTestButton(self),
            AutoPingRemoveButton(self)
        ))
        c.add_item(discord.ui.Separator())
        c.add_item(discord.ui.ActionRow(AutoPingToggleButton(self)))
        c.add_item(discord.ui.TextDisplay(
            "-# Le délai est en secondes. Mets 0 pour garder le message. Les réglages sont sauvegardés dans autoping_config.json."
        ))
        self.add_item(c)

    def rebuild(self, notice=None):
        return AutoPingPanel(self.owner_id, self.guild, self.selected_channel_id, notice)


@bot.command(name="autoping")
@commands.has_permissions(administrator=True)
async def autoping(ctx):
    """Ouvre le panel Components V2 de configuration des messages automatiques à l'arrivée."""
    if ctx.guild is None:
        return
    await ctx.send(view=AutoPingPanel(ctx.author.id, ctx.guild))


@bot.listen("on_member_join")
async def autoping_member_join(member: discord.Member):
    if member.bot:
        return
    cfg = autoping_config.get(str(member.guild.id), {})
    if not cfg.get("enabled", True):
        return

    for channel_id, data in list(cfg.get("channels", {}).items()):
        if not data.get("enabled", True):
            continue
        try:
            channel = member.guild.get_channel(int(channel_id))
        except (TypeError, ValueError):
            continue
        if not isinstance(channel, discord.TextChannel):
            continue

        message_text = render_autoping_message(str(data.get("message", "Bienvenue {mention} !")), member)
        delay = data.get("delete_delay", 10)
        try:
            delay = int(delay)
        except (TypeError, ValueError):
            delay = 10
        try:
            await channel.send(
                message_text,
                delete_after=delay if delay > 0 else None,
                allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=True)
            )
        except (discord.Forbidden, discord.HTTPException) as error:
            print(f"⚠️ AutoPing impossible dans {channel.name} : {error}")


# ============================================================
# PANEL COMPONENTS V2 - +ghostping
# ============================================================

class GhostPingChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(
            placeholder="📢 Dans quel salon ghost ping ?",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            custom_id="ghostping:channel"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return

        self.panel.selected_channel_id = self.values[0].id
        await interaction.response.edit_message(view=self.panel.rebuild())


class GhostPingIntervalSelect(discord.ui.Select):
    def __init__(self, panel):
        self.panel = panel
        options = [
            discord.SelectOption(label="Toutes les 2 heures", value="2h", emoji="⏱️"),
            discord.SelectOption(label="Toutes les 5 heures", value="5h", emoji="🕔"),
            discord.SelectOption(label="Toutes les 10 heures", value="10h", emoji="🕙"),
            discord.SelectOption(label="Toutes les 24 heures", value="24h", emoji="📅"),
        ]
        super().__init__(
            placeholder="⏰ Tous les combien de temps ?",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ghostping:interval"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return

        self.panel.selected_interval = self.values[0]
        await interaction.response.edit_message(view=self.panel.rebuild())


class GhostPingActivateButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(
            label="Activer le ghost ping",
            emoji="✅",
            style=discord.ButtonStyle.success,
            custom_id="ghostping:activate"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return

        if not self.panel.selected_channel_id or not self.panel.selected_interval:
            await interaction.response.send_message(
                "❌ Choisis d'abord **le salon** et **la fréquence**.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(self.panel.selected_channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Le salon sélectionné est introuvable.", ephemeral=True)
            return

        interval = self.panel.selected_interval
        hours = GHOSTPING_INTERVALS[interval]
        ghostping_config[str(interaction.guild.id)] = {
            "channel_id": channel.id,
            "interval": interval,
            "interval_hours": hours,
            "next_run": (discord.utils.utcnow() + timedelta(hours=hours)).timestamp()
        }
        save_ghostping_config()

        await interaction.response.edit_message(view=self.panel.rebuild(saved=True))


class GhostPingDisableButton(discord.ui.Button):
    def __init__(self, panel):
        self.panel = panel
        super().__init__(
            label="Désactiver",
            emoji="⛔",
            style=discord.ButtonStyle.danger,
            custom_id="ghostping:disable"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.panel.owner_id:
            await interaction.response.send_message("❌ Ce panel ne t'appartient pas.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return

        ghostping_config.pop(str(interaction.guild.id), None)
        save_ghostping_config()
        await interaction.response.edit_message(view=self.panel.rebuild(disabled=True))


class GhostPingPanel(discord.ui.LayoutView):
    def __init__(self, owner_id, guild, selected_channel_id=None, selected_interval=None, notice=None):
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.guild = guild
        self.selected_channel_id = selected_channel_id
        self.selected_interval = selected_interval
        self.notice = notice
        self._build()

    def _status_text(self):
        cfg = ghostping_config.get(str(self.guild.id))
        if not cfg:
            return "🔴 **Désactivé**"
        channel_id = cfg.get("channel_id")
        hours = cfg.get("interval_hours")
        return f"🟢 **Activé** • <#{channel_id}> • toutes les **{hours}h**"

    def _build(self):
        channel_text = f"<#{self.selected_channel_id}>" if self.selected_channel_id else "*Aucun salon sélectionné*"
        interval_text = f"Toutes les **{GHOSTPING_INTERVALS[self.selected_interval]} heures**" if self.selected_interval else "*Aucune fréquence sélectionnée*"

        container = discord.ui.Container(accent_color=0xED4245)
        container.add_item(discord.ui.TextDisplay(
            "# 👻 CONFIGURATION GHOST PING\n"
            "Configure l'envoi automatique de `@everyone`. Le message est supprimé immédiatement après son envoi."
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"### 📢 Salon sélectionné\n{channel_text}\n\n"
            f"### ⏰ Fréquence\n{interval_text}\n\n"
            f"### 🛡️ État actuel\n{self._status_text()}"
        ))
        if self.notice:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(self.notice))

        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay("### 1️⃣ Dans quel salon ghost ping ?"))
        container.add_item(discord.ui.ActionRow(GhostPingChannelSelect(self)))
        container.add_item(discord.ui.TextDisplay("### 2️⃣ Tous les combien de temps ?"))
        container.add_item(discord.ui.ActionRow(GhostPingIntervalSelect(self)))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(
            GhostPingActivateButton(self),
            GhostPingDisableButton(self)
        ))
        container.add_item(discord.ui.TextDisplay(
            "-# 🔔 Le bot doit avoir la permission de mentionner @everyone et d'envoyer des messages dans le salon choisi."
        ))
        self.add_item(container)

    def rebuild(self, saved=False, disabled=False):
        notice = None
        if saved:
            notice = "✅ **Configuration enregistrée.** Le ghost ping automatique est maintenant actif."
        elif disabled:
            notice = "⛔ **Ghost ping désactivé** sur ce serveur."
        return GhostPingPanel(
            owner_id=self.owner_id,
            guild=self.guild,
            selected_channel_id=self.selected_channel_id,
            selected_interval=self.selected_interval,
            notice=notice
        )


@bot.command(name="ghostping")
@commands.has_permissions(administrator=True)
async def ghostping(ctx):
    """Ouvre le panel Components V2 de configuration du ghost ping."""
    if ctx.guild is None:
        return

    cfg = ghostping_config.get(str(ctx.guild.id), {})
    selected_channel_id = cfg.get("channel_id")
    selected_interval = cfg.get("interval")

    panel = GhostPingPanel(
        owner_id=ctx.author.id,
        guild=ctx.guild,
        selected_channel_id=selected_channel_id,
        selected_interval=selected_interval
    )
    await ctx.send(view=panel)


@bot.tree.command(name="setghostping", description="Configure le ghost ping automatique @everyone")
@discord.app_commands.describe(
    salon="Salon dans lequel envoyer le ghost ping",
    duree="Fréquence du ghost ping",
    activer="Active ou désactive le ghost ping"
)
@discord.app_commands.choices(duree=[
    discord.app_commands.Choice(name="Toutes les 2 heures", value="2h"),
    discord.app_commands.Choice(name="Toutes les 5 heures", value="5h"),
    discord.app_commands.Choice(name="Toutes les 10 heures", value="10h"),
    discord.app_commands.Choice(name="Toutes les 24 heures", value="24h"),
])
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.guild_only()
async def setghostping(
    interaction: discord.Interaction,
    salon: discord.TextChannel,
    duree: discord.app_commands.Choice[str],
    activer: bool
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)

    if not activer:
        ghostping_config.pop(guild_id, None)
        save_ghostping_config()
        await interaction.response.send_message(
            "⛔ Ghost ping désactivé sur ce serveur.",
            ephemeral=True
        )
        return

    hours = GHOSTPING_INTERVALS[duree.value]
    ghostping_config[guild_id] = {
        "channel_id": salon.id,
        "interval": duree.value,
        "interval_hours": hours,
        "next_run": (discord.utils.utcnow() + timedelta(hours=hours)).timestamp()
    }
    save_ghostping_config()

    await interaction.response.send_message(
        f"✅ Ghost ping activé dans {salon.mention}.\n"
        f"⏱️ Fréquence : **toutes les {hours}h**.\n"
        "Le bot enverra `@everyone` puis supprimera immédiatement le message.",
        ephemeral=True
    )


@tasks.loop(minutes=1)
async def ghostping_scheduler():
    now = discord.utils.utcnow().timestamp()
    changed = False

    for guild_id, cfg in list(ghostping_config.items()):
        try:
            next_run = float(cfg.get("next_run", 0))
            if now < next_run:
                continue

            guild = bot.get_guild(int(guild_id))
            channel = guild.get_channel(int(cfg.get("channel_id", 0))) if guild else None
            hours = int(cfg.get("interval_hours", 0))

            if guild is None or not isinstance(channel, discord.TextChannel) or hours not in (2, 5, 10, 24):
                continue

            try:
                message = await channel.send(
                    "@everyone",
                    allowed_mentions=discord.AllowedMentions(everyone=True, roles=False, users=False)
                )
                await message.delete()
            except (discord.Forbidden, discord.HTTPException) as error:
                print(f"⚠️ Ghost ping impossible dans {guild.name}: {error}")

            cfg["next_run"] = (discord.utils.utcnow() + timedelta(hours=hours)).timestamp()
            changed = True
        except (TypeError, ValueError):
            continue

    if changed:
        save_ghostping_config()


@ghostping_scheduler.before_loop
async def before_ghostping_scheduler():
    await bot.wait_until_ready()





@bot.event
async def on_ready():
    if not ghostping_scheduler.is_running():
        ghostping_scheduler.start()

    if not getattr(bot, "_slash_commands_synced", False):
        try:
            synced = await bot.tree.sync()
            bot._slash_commands_synced = True
            print(f"✅ Commandes slash synchronisées : {len(synced)}")
        except Exception as error:
            print(f"⚠️ Synchronisation slash impossible : {error}")

    print("================================")
    print(f"✅ Bot connecté : {bot.user}")
    print(f"🆔 ID : {bot.user.id}")
    print(f"🌐 Serveurs : {len(bot.guilds)}")
    print("================================")

print("SETUP VIP ACCESS PRESENT :", bot.get_command("setup_vip_access") is not None)
print("ANTILINK COMMAND PRESENT :", bot.get_command("antilink") is not None)
print("COMMANDES CHARGEES :")
for command in bot.commands:
    print(f"- +{command.name}")

print("🚀 Tentative de connexion à Discord...")

try:
    bot.run(TOKEN)
except BaseException as e:
    print("❌ ERREUR BOT :", repr(e))

print("🏁 bot.run() est terminé")
