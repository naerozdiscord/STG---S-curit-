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
    print("================================")
    print(f"✅ Bot connecté : {bot.user}")
    print(f"🆔 ID : {bot.user.id}")
    print(f"🌐 Serveurs : {len(bot.guilds)}")
    print("================================")

print("SETUP TICKET PRESENT :", bot.get_command("setup_ticket") is not None)
print("SETUP VIP ACCESS PRESENT :", bot.get_command("setup_vip_access") is not None)
print("COMMANDES CHARGEES :")
for command in bot.commands:
    print(f"- +{command.name}")

print("🚀 Tentative de connexion à Discord...")

try:
    bot.run(TOKEN)
except BaseException as e:
    print("❌ ERREUR BOT :", repr(e))

print("🏁 bot.run() est terminé")
