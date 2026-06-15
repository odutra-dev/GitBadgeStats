from fastapi import FastAPI, Response
from dotenv import load_dotenv

from src.github import fetch_github_stats
from src.render import generate_svg

load_dotenv()

app = FastAPI(title="Custom GitHub Stats")


@app.get("/api")
async def get_repo_stats(username: str, theme: str = "default"):
    # 1. Busca os dados do GitHub
    stats = await fetch_github_stats(username)
    
    # 2. Gera o SVG aplicando o tema recebido na URL
    svg_content = generate_svg(stats, theme_name=theme)
    
    # 3. Retorna o SVG
    return Response(content=svg_content, media_type="image/svg+xml")