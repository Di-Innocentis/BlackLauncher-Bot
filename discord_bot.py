import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
from github import Github
import json
import os
from keep_alive import keep_alive

# ==================== CONFIGURACIÓN ====================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "Di-Innocentis/instancias_black_launcher"
INSTANCE_NAME_TO_UPDATE = "Pitcharcity Magic Adventure"
# =======================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- CLASE 1: EL FORMULARIO (MODAL) ---
class WhitelistModal(Modal, title="Solicitud de Acceso"):
    name_input = TextInput(
        label="Tu Nickname de Minecraft",
        placeholder="Escribe aquí tu nombre exacto...",
        min_length=3,
        max_length=16,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        nickname = self.name_input.value
        user_id = str(interaction.user.id) # Guardamos el ID de Discord
        
        # Avisamos que estamos procesando (mensaje efímero, solo lo ve el usuario)
        await interaction.response.send_message(f"🔄 **Procesando solicitud para:** `{nickname}`...", ephemeral=True)

        try:
            # 1. Conexión a GitHub
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            contents = repo.get_contents("instances.json")
            json_content = contents.decoded_content.decode("utf-8")
            data = json.loads(json_content)

            found = False
            
            # 2. Lógica de búsqueda y validación
            for instance in data.get("instances", []):
                if instance.get("name") == INSTANCE_NAME_TO_UPDATE:
                    found = True
                    
                    # Asegurar que existan las listas
                    if "whitelist" not in instance: instance["whitelist"] = []
                    if "claimed_discord_ids" not in instance: instance["claimed_discord_ids"] = []

                    # REGLA: ¿Este usuario de Discord ya pidió whitelist?
                    if user_id in instance["claimed_discord_ids"]:
                        await interaction.edit_original_response(content="❌ **Error:** Ya has registrado un usuario anteriormente. Solo se permite una cuenta por persona.")
                        return

                    # REGLA: ¿El nick ya está ocupado?
                    if nickname in instance["whitelist"]:
                        await interaction.edit_original_response(content=f"⚠️ El usuario **{nickname}** ya está en la lista.")
                        return

                    # SI PASA LAS REGLAS: AGREGAR
                    instance["whitelist"].append(nickname)
                    instance["claimed_discord_ids"].append(user_id) # Registramos que este Discord ID ya usó su turno
                    break
            
            if not found:
                await interaction.edit_original_response(content=f"❌ Error interno: No encontré la instancia '{INSTANCE_NAME_TO_UPDATE}'.")
                return

            # 3. Subir a GitHub
            new_json_content = json.dumps(data, indent=4)
            repo.update_file(
                path=contents.path, 
                message=f"Bot: Whitelist {nickname} (Discord: {interaction.user.name})", 
                content=new_json_content, 
                sha=contents.sha
            )
            
            await interaction.edit_original_response(content=f"✅ **¡Listo!** Agregado a la whitelist: **{nickname}**\nℹ️ *Reinicia el launcher para entrar.*")

        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Ocurrió un error: {str(e)}")

# --- CLASE 2: EL BOTÓN (VIEW) ---
class WhitelistView(View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None para que el botón no deje de funcionar

    @discord.ui.button(label="🔓 Solicitar Whitelist", style=discord.ButtonStyle.green, custom_id="whitelist_btn_v1")
    async def whitelist_button(self, interaction: discord.Interaction, button: Button):
        # Al presionar el botón, mostramos el Modal
        await interaction.response.send_modal(WhitelistModal())

# --- EVENTOS DEL BOT ---
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como: {bot.user.name}')
    # Esto hace que el botón siga funcionando si el bot se reinicia
    bot.add_view(WhitelistView()) 
    print('--- Sistema de Whitelist Visual Activo ---')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Comando para crear el panel (Solo admins)"""
    # Borramos el mensaje del comando para limpieza
    await ctx.message.delete()
    
    embed = discord.Embed(
        title="🛡️ Acceso al Servidor: Pitcharcity Magic Adventure",
        description=(
            "Para ingresar al servidor, necesitas registrar tu nickname de Minecraft.\n\n"
            "**Instrucciones:**\n"
            "1. Presiona el botón de abajo.\n"
            "2. Escribe tu nombre de usuario **exacto** en el recuadro.\n"
            "3. Espera la confirmación.\n\n"
            "⚠️ **Nota:** Solo puedes registrar una cuenta por usuario de Discord no se vale tener dos cuentas de discord escucho litersh, escucho Wolfsito xddd."
        ),
        color=0x00ff00
    )
    embed.set_thumbnail(url="https://i.imgur.com/TuImagen.png") # Opcional: Pon aquí un link a tu logo
    
    view = WhitelistView()
    await ctx.send(embed=embed, view=view)

# --- ARRANQUE ---
keep_alive()
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)


