import discord
from discord.ext import commands
from github import Github
import json
import os
from keep_alive import keep_alive  # <--- IMPORTANTE

# ================= CONFIGURACIÓN =================
# AHORA LEEMOS DESDE EL SISTEMA (RENDER), NO DEL ARCHIVO
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
INSTANCE_NAME_TO_UPDATE = "Survival 2026" # Este sí puede ir fijo si quieres
# =================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como: {bot.user.name}')
    print('--- Esperando comando !whitelist ---')

@bot.command()
async def whitelist(ctx, nickname):
    """
    Comando: !whitelist TuNick
    Agrega el nick al archivo JSON en GitHub.
    """
    
    print(f"📩 Solicitud recibida: {nickname} (por {ctx.author.name})")
    
    # Mensaje de carga
    aviso = await ctx.send(f"🔄 **Procesando...** Conectando a la base de datos para agregar a `{nickname}`...")
    
    try:
        # 1. Conexión a GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Busca el archivo en la raíz del repo
        # IMPORTANTE: El archivo debe llamarse 'instances.json' en tu GitHub
        contents = repo.get_contents("instances.json")
        
        # 2. Descargar y leer JSON actual
        json_content = contents.decoded_content.decode("utf-8")
        data = json.loads(json_content)
        
        found = False
        already_in_list = False
        
        # 3. Buscar la instancia correcta y editar la lista
        for instance in data.get("instances", []):
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
            await aviso.edit(content=f"❌ Error: No encontré una instancia llamada **'{INSTANCE_NAME_TO_UPDATE}'** en tu JSON. Revisa el nombre en el script.")
            return

        if already_in_list:
            await aviso.edit(content=f"⚠️ El usuario **{nickname}** ya estaba en la lista de acceso.")
            return

        # 4. Subir los cambios a GitHub (Commit automático)
        new_json_content = json.dumps(data, indent=4)
        repo.update_file(
            path=contents.path, 
            message=f"Bot: Whitelist {nickname}", 
            content=new_json_content, 
            sha=contents.sha
        )
        
        # Confirmación final
        await aviso.edit(content=f"✅ **{nickname}** ha sido autorizado correctamente.\nℹ️ *El launcher detectará el cambio en 1-2 minutos.*")
        print(f"✅ {nickname} agregado a GitHub con éxito.")

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await aviso.edit(content=f"❌ Error 404: No encuentro el repositorio **'{REPO_NAME}'** o el archivo **'instances.json'**.")
        elif "401" in error_msg or "Bad credentials" in error_msg:
            await aviso.edit(content="❌ Error 401: El token de GitHub no es válido o expiró.")
        else:
            await aviso.edit(content=f"❌ Error interno: {error_msg}")
        
        print(f"❌ Error crítico: {e}")

# Arrancar el bot
if __name__ == "__main__":
    try:
        keep_alive
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")
        input("Presiona ENTER para salir...")