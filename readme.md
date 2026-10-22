<div align="center">
  <h1 style="font-size: 28px; margin: 10px 0;">Git Badge Stats</h1>
  <p>Dynamically generated GitHub stats badges and Duolingo-style Streak Cards for your profile READMEs!</p>
</div>

<p align="center">
  <a href="https://github.com/odutra-dev/GitBadgeStats/graphs/contributors">
    <img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/odutra-dev/GitBadgeStats" />
  </a>
  <a href="https://github.com/odutra-dev/GitBadgeStats/issues">
    <img alt="Issues" src="https://img.shields.io/github/issues/odutra-dev/GitBadgeStats?color=0088ff" />
  </a>
  <a href="https://github.com/odutra-dev/GitBadgeStats/pulls">
    <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/odutra-dev/GitBadgeStats?color=0088ff" />
  </a>
  <a href="https://github.com/odutra-dev/GitBadgeStats/actions">
    <img alt="CI Tests" src="https://img.shields.io/github/actions/workflow/status/odutra-dev/GitBadgeStats/tests.yml?branch=main&label=tests" />
  </a>
</p>

---

## 1. 🔥 Duolingo-Style Streak Card

Inspired by Duolingo streaks, this card monitors your daily GitHub commit consistency and motivates you to keep coding every day:

- **Lit Flame (Painted):** When you commit today, the hero flame and today's weekly tracker flame burst into a vibrant fiery gradient (`#FF9600` to `#FF3838`) with a warm glow filter.
- **Unlit Flame:** If you haven't committed yet today, the flame appears unlit (desaturated grey) with a reminder pill to commit.
- **Streak Reset Rule:** If you miss a full day without any commits (yesterday = 0 commits), your streak resets to 0!
- **7-Day Weekly Tracker:** Displays the last 7 days with mini flames lit for active days and commit counts below.
- **Compact Mode:** Hide the weekly tracker with `hide_days=true` for a sleek, minimal card.

### Quick Usage

```markdown
![GitHub Streak](https://git-badge-stats.vercel.app/api/streak?username=YOUR_USERNAME&theme=dracula)
```

Or in HTML:

```html
<img src="https://git-badge-stats.vercel.app/api/streak?username=YOUR_USERNAME&theme=dracula" alt="GitHub Streak" />
```

### Streak Card Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `username` | `string` | **Required** | GitHub username |
| `theme` | `string` | `default` | Visual theme name (over 70 themes available) |
| `timezone` | `string` | `UTC` | Timezone for accurate day calculation (e.g., `America/Sao_Paulo`, `America/New_York`) |
| `locale` | `string` | `en` | Display language (`en` for English, `pt` for Portuguese) |
| `hide_days` | `boolean` | `false` | When `true`, hides the 7-day weekly tracker for a compact card |
| `title_color` | `string` | - | Custom hex color for titles (without `#`, e.g., `ff5555`) |
| `text_color` | `string` | - | Custom hex color for labels and body text |
| `icon_color` | `string` | - | Custom hex color for metric icons |
| `bg_color` | `string` | - | Custom hex color or angle gradient (e.g., `35,4158d0,c850c0,ffcc70`) |
| `border_color`| `string` | - | Custom hex color for card border |

---

## 2. 📊 GitHub Stats Card

A classic GitHub statistics card featuring dynamic rank computation (S, A+, A, A-, B+, B, B-, C+, C):

```markdown
![GitHub Stats](https://git-badge-stats.vercel.app/api?username=YOUR_USERNAME&theme=tokyonight)
```

Or using the explicit route:

```markdown
![GitHub Stats](https://git-badge-stats.vercel.app/api/stats?username=YOUR_USERNAME&theme=tokyonight)
```

### Stats Card Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `username` | `string` | **Required** | GitHub username |
| `theme` | `string` | `default` | Visual theme name |
| `hide_rank` | `boolean` | `false` | When `true`, hides the circular dynamic rank gauge |
| `title_color` | `string` | - | Custom hex color for card title |
| `text_color` | `string` | - | Custom hex color for stats text |
| `icon_color` | `string` | - | Custom hex color for category icons |
| `bg_color` | `string` | - | Custom hex color or gradient for background |
| `border_color`| `string` | - | Custom hex color for card border |

---

## 🎨 Available Themes

Git Badge Stats comes with over 70 built-in themes out of the box, including:

- `default`, `dark`, `dracula`, `tokyonight`, `radical`, `onedark`, `gruvbox`
- `catppuccin_mocha`, `catppuccin_latte`, `nord`, `cobalt`, `synthwave`, `highcontrast`
- `ambient_gradient`, `sunset`, `ocean_dark`, `github_dark`, etc.

Explore the full list of themes in [`src/themes.py`](src/themes.py).

---

## ⚡ Built-in Caching & Performance

- **In-Memory TTL Cache:** Requests are cached for 10 minutes to prevent hitting GitHub API rate limits and to deliver instantaneous SVG badge responses.
- **HTTP Cache Headers:** Badges return `Cache-Control` headers with stale-while-revalidate for CDN efficiency.

---

## 🚀 Running Locally

### 1. Clone Repository

```bash
git clone https://github.com/odutra-dev/GitBadgeStats.git
cd GitBadgeStats
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and configure your GitHub Personal Access Token:

```env
GITHUB_TOKEN=ghp_your_personal_access_token
```

### 4. Start Development Server

```bash
uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`. You can also explore interactive API documentation at `http://localhost:8000/docs`.

### 5. Run Automated Tests

```bash
pytest
```

---

## 📄 License & Credits

Distributed under the MIT License. See `LICENSE` for more information.

Inspired by [Anurag Hazra's](https://github.com/anuraghazra) [github-readme-stats](https://github.com/anuraghazra/github-readme-stats).
