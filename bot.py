import discord
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from discord.ext import commands
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
PROOF_PANEL_CHANNEL_ID = 1551714705306034226

# Salon privé/staff dans lequel les demandes seront envoyées
PROOF_REVIEW_CHANNEL_ID = 1554932194298953819

# Rôle donné automatiquement lorsque la demande est validée
PROOF_ROLE_ID = 1551072338567499909

# Salon où seront annoncées les validations
PROOF_SUCCESS_CHANNEL_ID = 1551731497537376396

# ============================================================
# CONFIGURATION DU SYSTÈME DE TICKETS VIP
# ============================================================

# Catégorie dans laquelle les tickets seront créés
TICKET_CATEGORY_ID = 1550556817526882464

# Rôle staff qui sera autorisé à voir les tickets et pingé à leur ouverture
TICKET_STAFF_ROLE_ID = 1550544412499771504


# Préfixe pour les commandes
intents = discord.Intents.default()
intents.members = True  # Pour gérer les membres
intents.message_content = True  # Pour pouvoir lire les messages

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print("================================")
    print("✅ ON_READY APPELÉ")
    print(f"🤖 Bot : {bot.user}")
    print(f"🆔 ID : {bot.user.id}")
    print(f"🌐 Serveurs : {len(bot.guilds)}")
    print("================================")



    


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
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    
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

    # Catégorie : 🎟️ Commandes Tickets
    embed.add_field(
        name="🎟️ Commandes Tickets",
        value=(
            "`+setup_ticket` → Installe le panneau pour ouvrir un ticket VIP.\n"
            "🛒 Le bouton crée automatiquement un salon privé dans la catégorie tickets.\n"
            "👮 Le rôle staff est pingé à l'ouverture du ticket.\n"
            "🔒 Un bouton permet de fermer le ticket."
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
            "`+server_info` → Affiche les informations du serveur.\n"
            "`+server_emojis` → Liste les emojis du serveur.\n"
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
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
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
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
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
# SYSTÈME DE TICKETS VIP
# ============================================================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fermer le ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "❌ Ce salon n'est pas un ticket.",
                ephemeral=True
            )
            return

        # Seul le membre ayant ouvert le ticket ou le staff peut le fermer.
        staff_role = interaction.guild.get_role(TICKET_STAFF_ROLE_ID)
        is_staff = staff_role in interaction.user.roles if staff_role else False
        owner_id = None

        try:
            owner_id = int(interaction.channel.name.split("ticket-", 1)[1])
        except (ValueError, IndexError):
            pass

        if interaction.user.id != owner_id and not is_staff and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission de fermer ce ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Le ticket va être fermé...",
            ephemeral=True
        )
        await asyncio.sleep(2)

        try:
            await interaction.channel.delete(
                reason=f"Ticket fermé par {interaction.user}"
            )
        except discord.Forbidden:
            pass


class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Acheter l'accès (1€)",
        emoji="🔥",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_buy_access"
    )
    async def buy_access(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild
        member = interaction.user

        if guild is None:
            return

        # Empêche un utilisateur d'avoir plusieurs tickets ouverts.
        existing_ticket = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{member.id}"
        )

        if existing_ticket:
            await interaction.response.send_message(
                f"❌ Tu as déjà un ticket ouvert : {existing_ticket.mention}",
                ephemeral=True
            )
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "❌ La catégorie des tickets est introuvable ou invalide.",
                ephemeral=True
            )
            return

        staff_role = guild.get_role(TICKET_STAFF_ROLE_ID)
        if staff_role is None:
            await interaction.response.send_message(
                "❌ Le rôle staff est introuvable.",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                manage_messages=True
            ),
        }

        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            )

        try:
            ticket = await guild.create_text_channel(
                name=f"ticket-{member.id}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket VIP ouvert par {member}"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas les permissions nécessaires pour créer le ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"🎟️ Ton ticket a été créé : {ticket.mention}",
            ephemeral=True
        )

        embed = discord.Embed(
            title="🔓 DÉBLOQUE LE CONTENUS",
            description=(
                "💳 **Ton ticket est ouvert !**\\n\\n"
                f"👤 **Client :** {member.mention}\\n"
                f"🎟️ **Ticket :** {ticket.mention}\\n\\n"
                "💰 **Accès VIP : 1€**\\n\\n"
                "📩 Un membre du staff va venir prendre en charge ta demande.\\n\\n"
                "⚠️ **Ne ferme pas le ticket avant d'avoir terminé ta demande.**"
            ),
            color=0xE60000
        )
        embed.set_footer(text="VIP Access • Ticket privé")

        await ticket.send(
            content=(
                f"🔔 {staff_role.mention}\\n\\n"
                f"💳 **DÉBLOQUE LE CONTENUS** 🔐\\n"
                f"📨 Ton ticket est ouvert : {ticket.mention}\\n\\n"
                f"👁️ **Only you can see this** • {member.mention}"
            ),
            embed=embed,
            view=CloseTicketView(),
            allowed_mentions=discord.AllowedMentions(roles=True, users=True)
        )


# ============================================================
# COMMANDE POUR INSTALLER LE PANNEAU
# ============================================================




@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    """Installe le panneau d'achat VIP et son bouton de création de ticket."""

    embed = discord.Embed(
        title="🏆 ACHAT VIP",
        description=(
            "🎟️ **Clique sur le bouton ci-dessous pour ouvrir un ticket**\n"
            "et obtenir ton accès VIP !\n\n"
            "💰 **Accès VIP : 1€**\n\n"
            "📩 Un ticket privé sera créé automatiquement dans la catégorie prévue.\n"
            "👮 Le staff sera prévenu dès l'ouverture."
        ),
        color=discord.Color.from_str("#333333")
    )

    embed.set_footer(text="VIP Access • 1€")

    await ctx.send(
        embed=embed,
        view=TicketView()
    )

    await ctx.send(
        f"<:point:1554955936609865778> **Panneau tickets installé dans {ctx.channel.mention}.**"
    )

# ============================================================
# INITIALISATION DES BOUTONS PERSISTANTS
# ============================================================

@bot.event
async def setup_hook():

    # Bouton "ENVOYER LES PREUVES"
    bot.add_view(
        ProofPanelView()
    )

    # Boutons VALIDER / REFUSER
    bot.add_view(
        ProofReviewView()
    )

    # Bouton d'achat VIP
    bot.add_view(
        TicketView()
    )

    # Bouton de fermeture des tickets
    bot.add_view(
        CloseTicketView()
    )


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





@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")

print("COMMANDES CHARGEES :")
for command in bot.commands:
    print(f"- +{command.name}")

print("🚀 Tentative de connexion à Discord...")

try:
    bot.run(TOKEN)
except BaseException as e:
    print("❌ ERREUR BOT :", repr(e))

print("🏁 bot.run() est terminé")
