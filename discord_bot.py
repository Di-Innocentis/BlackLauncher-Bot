import discord
from discord.ext import commands
from github import Github
import json
import asyncio
import os
from keep_alive import keep_alive  # Importamos el servidor web para Render

# ==================== CONFIGURACIÓN ====================

# 1. TOKENS (Se leen desde las Variables de Entorno de Render por seguridad)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 2. TU REPOSITORIO
REPO_NAME = "Di-Innocentis/instancias_black_launcher"

# 3. NOMBRE EXACTO DE LA INSTANCIA (Corregido)
INSTANCE_NAME_TO_UPDATE = "Pitcharcity Revolution Vol 4"

# =======================================================

# Configuración de permisos de Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como: {bot.user.name}')
    print(f'📂 Conectado al repo: {REPO_NAME}')
    print(f'🎯 Buscando instancia: {INSTANCE_NAME_TO_UPDATE}')
    print('--- Listo para recibir comandos ---')

@bot.command()
async def whitelist(ctx, nickname):
    """
    Comando: !whitelist TuNick
    Agrega el nick al archivo JSON en GitHub.
    """
    
    print(f"📩 Solicitud recibida: {nickname} (por {ctx.author.name})")
    
    # Mensaje de carga
    aviso = await ctx.send(f"🔄 **Procesando...** Verificando acceso para `{nickname}`...")
    
    try:
        # 1. Conexión a GitHub
        if not GITHUB_TOKEN:
            await aviso.edit(content="❌ Error fatal: No se encontró el GITHUB_TOKEN en Render.")
            return

        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Busca el archivo en la raíz del repo
        contents = repo.get_contents("instances.json")
        
        # 2. Descargar y leer JSON actual
        json_content = contents.decoded_content.decode("utf-8")
        data = json.loads(json_content)
        
        found = False
        already_in_list = False
        
        # 3. Buscar la instancia correcta y editar la lista
        for instance in data.get("instances", []):
            # Compara el nombre de la instancia
            if instance.get("name") == INSTANCE_NAME_TO_UPDATE:
                found = True
                
                # Crear la lista whitelist si no existe
                if "whitelist" not in instance:
                    instance["whitelist"] = []
                
                # Verificar si el usuario ya está
                if nickname in instance["whitelist"]:
                    already_in_list = True
                else:
                    # AGREGAR EL NOMBRE A LA LISTA
                    instance["whitelist"].append(nickname)
                break
        
        # Manejo de errores lógicos
        if not found:
            await aviso.edit(content=f"❌ Error: No encontré la instancia **'{INSTANCE_NAME_TO_UPDATE}'** en tu JSON de GitHub.\nRevisa que el nombre en `instances.json` sea idéntico.")
            return

        if already_in_list:
            await aviso.edit(content=f"⚠️ El usuario **{nickname}** ya estaba en la lista de acceso.")
            return

        # 4. Subir los cambios a GitHub (Commit automático)
        new_json_content = json.dumps(data, indent=4)
        repo.update_file(
            path=contents.path, 
            message=f"Bot: Whitelist {nickname} (por {ctx.author.name})", 
            content=new_json_content, 
            sha=contents.sha
        )
        
        # Confirmación final
        await aviso.edit(content=f"✅ **{nickname}** ha sido autorizado correctamente en **{INSTANCE_NAME_TO_UPDATE}**.\nℹ️ *Reinicia el launcher para entrar.*")
        print(f"✅ {nickname} agregado a GitHub con éxito.")

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await aviso.edit(content=f"❌ Error 404: No encuentro el archivo **'instances.json'** en el repositorio.")
        elif "401" in error_msg or "Bad credentials" in error_msg:
            await aviso.edit(content="❌ Error 401: El token de GitHub en Render no es válido.")
        else:
            await aviso.edit(content=f"❌ Error interno: {error_msg}")
        
        print(f"❌ Error crítico: {e}")

# --- MANTENER VIVO EN RENDER ---
keep_alive()

# Arrancar el bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ Error: No se encontró el DISCORD_TOKEN en las variables de entorno.")
