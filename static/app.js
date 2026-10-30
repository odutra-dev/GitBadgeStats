/**
 * Git Badge Stats - Interactive Badge Generator & Preview
 */

(function () {
  "use strict";

  // Constants
  const PRODUCTION_BASE_URL = "https://git-badge-stats.vercel.app";

  const CARD_ROUTES = {
    stats: "/api/stats",
    streak: "/api/streak",
    languages: "/api/top-langs",
    profile: '/api/profile',
  };

  const CARD_TITLES = {
    stats: "GitHub Stats",
    streak: "GitHub Streak",
    languages: "Top Languages",
    profile: 'GitHub Profile',
  };

  const CARD_ENDPOINTS = {
    stats: "GET /api/stats",
    streak: "GET /api/streak",
    languages: "GET /api/top-langs",
    profile: 'GET /api/profile',
  };

  // State
  let activeCard = "stats";
  let activeFormat = "markdown";
  let debounceTimeout = null;

  // DOM Elements
  const cardTabBtns = document.querySelectorAll(".card-tab-btn");
  const formatTabBtns = document.querySelectorAll(".format-tab-btn");
  const toggleProductionUrl = document.getElementById("toggle-production-url");

  const activeBadgeEndpoint = document.getElementById("active-badge-endpoint");

  // Preview elements
  const previewWrapper = document.getElementById("preview-wrapper");
  const previewLoading = document.getElementById("preview-loading");
  const previewPlaceholder = document.getElementById("preview-placeholder");
  const previewImg = document.getElementById("preview-img");
  const btnRefreshPreview = document.getElementById("btn-refresh-preview");
  const linkOpenRaw = document.getElementById("link-open-raw");

  // Code output & copy elements
  const codeOutput = document.getElementById("code-output");
  const btnCopyCode = document.getElementById("btn-copy-code");
  const copyText = document.getElementById("copy-text");

  // Form elements
  const cardForm = document.getElementById("card-form");
  const inputUsername = document.getElementById("input-username");
  const usernameError = document.getElementById("username-error");
  const selectTheme = document.getElementById("select-theme");
  const btnResetForm = document.getElementById("btn-reset-form");

  // Card specific sections
  const sectionStatsOptions = document.getElementById("section-stats-options");
  const sectionStreakOptions = document.getElementById(
    "section-streak-options",
  );
  const sectionLanguagesOptions = document.getElementById(
    "section-languages-options",
  );
  const sectionProfileOptions = document.getElementById(
    "section-profile-options",
  );
  const rowIconColor = document.getElementById("row-icon-color");

  // Stats inputs
  const selectStatsLocale = document.getElementById("select-stats-locale");
  const inputHideRank = document.getElementById("input-hide-rank");

  // Streak inputs
  const selectLocale = document.getElementById("select-locale");
  const inputTimezone = document.getElementById("input-timezone");
  const inputHideDays = document.getElementById("input-hide-days");

  // Languages inputs
  const selectLangsLocale = document.getElementById("select-langs-locale");
  const inputCardTitle = document.getElementById("input-card-title");
  const inputHideLangs = document.getElementById("input-hide-langs");
  const inputExcludeRepos = document.getElementById("input-exclude-repos");

  // Profile inputs
  const selectProfileLocale = document.getElementById("select-profile-locale");
  const inputProfileTitle = document.getElementById("input-profile-title");

  // Colors accordion & inputs
  const btnToggleColors = document.getElementById("btn-toggle-colors");
  const containerColors = document.getElementById("container-colors");
  const iconColorsArrow = document.getElementById("icon-colors-arrow");

  const inputTitleColor = document.getElementById("input-title-color");
  const pickerTitleColor = document.getElementById("picker-title-color");
  const inputTextColor = document.getElementById("input-text-color");
  const pickerTextColor = document.getElementById("picker-text-color");
  const inputIconColor = document.getElementById("input-icon-color");
  const pickerIconColor = document.getElementById("picker-icon-color");
  const inputBgColor = document.getElementById("input-bg-color");
  const pickerBgColor = document.getElementById("picker-bg-color");
  const inputBorderColor = document.getElementById("input-border-color");
  const pickerBorderColor = document.getElementById("picker-border-color");

  /**
   * Load available themes from API
   */
  async function loadThemes() {
    try {
      const res = await fetch("/api/themes");

      if (res.ok) {
        const data = await res.json();

        if (data.themes && Array.isArray(data.themes)) {
          populateThemesDropdown(data.themes);
          return;
        }
      }
    } catch (e) {
      console.warn(
        "Could not load themes from /api/themes, using fallback list",
        e,
      );
    }

    const fallbackThemes = [
      "default",
      "dark",
      "dracula",
      "tokyonight",
      "radical",
      "onedark",
      "gruvbox",
      "catppuccin_mocha",
      "catppuccin_latte",
      "nord",
      "cobalt",
      "synthwave",
      "highcontrast",
      "ambient_gradient",
      "sunset",
      "ocean_dark",
      "github_dark",
    ].sort();

    populateThemesDropdown(fallbackThemes);
  }

  function populateThemesDropdown(themesList) {
    selectTheme.innerHTML = "";

    themesList.forEach((theme) => {
      const option = document.createElement("option");
      option.value = theme;
      option.textContent = theme;

      if (theme === "default") {
        option.selected = true;
      }

      selectTheme.appendChild(option);
    });
  }

  /**
   * Clean hex string
   */
  function cleanHex(value) {
    if (!value) return "";
    return value.trim().replace(/^#/, "");
  }

  /**
   * Get base URLs
   */
  function getBaseUrls() {
    const isFile = window.location.protocol === "file:";
    const localOrigin = isFile ? PRODUCTION_BASE_URL : window.location.origin;

    const exportOrigin = toggleProductionUrl.checked
      ? PRODUCTION_BASE_URL
      : localOrigin;

    return { localOrigin, exportOrigin };
  }

  /**
   * Build query parameters based on active card and current inputs
   */
  function buildQueryParams(usernameVal) {
    const params = new URLSearchParams();

    // Username
    const username = (
      usernameVal !== undefined ? usernameVal : inputUsername.value
    ).trim();

    if (username) {
      params.set("username", username);
    }

    // Theme
    const theme = selectTheme.value;

    if (theme && theme !== "default") {
      params.set("theme", theme);
    }

    // Card Specific
    if (activeCard === "stats") {
      const statsLocale = selectStatsLocale ? selectStatsLocale.value : "en";

      if (statsLocale && statsLocale !== "en") {
        params.set("locale", statsLocale);
      }

      if (inputHideRank.checked) {
        params.set("hide_rank", "true");
      }
    } else if (activeCard === "streak") {
      const locale = selectLocale.value;

      if (locale && locale !== "en") {
        params.set("locale", locale);
      }

      const timezone = inputTimezone.value.trim();

      if (timezone && timezone !== "UTC") {
        params.set("timezone", timezone);
      }

      if (inputHideDays.checked) {
        params.set("hide_days", "true");
      }
    } else if (activeCard === "languages") {
      const langsLocale = selectLangsLocale ? selectLangsLocale.value : "en";

      if (langsLocale && langsLocale !== "en") {
        params.set("locale", langsLocale);
      }

      const cardTitle = inputCardTitle.value.trim();

      if (cardTitle) {
        params.set("card_title", cardTitle);
      }

      const hideLangs = inputHideLangs.value.trim();

      if (hideLangs) {
        params.set("hide", hideLangs);
      }

      const excludeRepos = inputExcludeRepos.value.trim();

      if (excludeRepos) {
        params.set("exclude_repo", excludeRepos);
      }
    } else if (activeCard === "profile") {
      const profileLocale = selectProfileLocale.value;

      if (profileLocale && profileLocale !== "en") {
        params.set('locale', profileLocale);
      }

      const profileTitle = inputProfileTitle.value.trim();

      if (profileTitle) {
        params.set('card_title', profileTitle);
      }
    }

    // Color overrides
    const titleColor = cleanHex(inputTitleColor.value);

    if (titleColor) {
      params.set("title_color", titleColor);
    }

    const textColor = cleanHex(inputTextColor.value);

    if (textColor) {
      params.set("text_color", textColor);
    }

    if (activeCard !== 'languages') {
      const iconColor = cleanHex(inputIconColor.value);

      if (iconColor) {
        params.set('icon_color', iconColor);
      }
    }

    const bgColor = cleanHex(inputBgColor.value);

    if (bgColor) {
      params.set("bg_color", bgColor);
    }

    const borderColor = cleanHex(inputBorderColor.value);

    if (borderColor) {
      params.set("border_color", borderColor);
    }

    return params;
  }

  /**
   * Generate badge URLs
   */
  function generateUrls() {
    const { localOrigin, exportOrigin } = getBaseUrls();
    const route = CARD_ROUTES[activeCard] || "/api/stats";
    const params = buildQueryParams();

    // Export query string (if username empty, show placeholder)
    let exportQs = params.toString();

    if (!inputUsername.value.trim()) {
      const dummyParams = buildQueryParams("your-username");
      exportQs = dummyParams.toString();
    }

    const exportUrl = `${exportOrigin}${route}${
      exportQs ? "?" + exportQs : ""
    }`;

    const previewUrl = `${localOrigin}${route}${
      params.toString() ? "?" + params.toString() : ""
    }`;

    return { exportUrl, previewUrl };
  }

  /**
   * Render code snippet
   */
  function renderCodeSnippet() {
    const { exportUrl } = generateUrls();
    const title = CARD_TITLES[activeCard] || "GitHub Stats";

    let code = "";

    if (activeFormat === "markdown") {
      code = `![${title}](${exportUrl})`;
    } else if (activeFormat === "html") {
      code = `<img src="${exportUrl}" alt="${title}" />`;
    } else {
      code = exportUrl;
    }

    codeOutput.textContent = code;
  }

  /**
   * Update badge preview image
   */
  function updatePreview() {
    const username = inputUsername.value.trim();

    if (!username) {
      previewPlaceholder.classList.remove("hidden");
      previewImg.classList.add("hidden");
      previewLoading.classList.add("hidden");
      linkOpenRaw.href = "#";
      linkOpenRaw.classList.add("pointer-events-none", "opacity-40");
      return;
    }

    usernameError.classList.add("hidden");
    linkOpenRaw.classList.remove("pointer-events-none", "opacity-40");

    const { previewUrl } = generateUrls();
    linkOpenRaw.href = previewUrl;

    // Show loading spinner
    previewLoading.classList.remove("hidden");

    const tempImg = new Image();

    tempImg.onload = function () {
      previewImg.src = previewUrl;
      previewPlaceholder.classList.add("hidden");
      previewImg.classList.remove("hidden");
      previewLoading.classList.add("hidden");
    };

    tempImg.onerror = function () {
      previewImg.src = previewUrl;
      previewPlaceholder.classList.add("hidden");
      previewImg.classList.remove("hidden");
      previewLoading.classList.add("hidden");
    };

    tempImg.src = previewUrl;
  }

  /**
   * Debounced input handler
   */
  function handleInputDebounced() {
    renderCodeSnippet();
    clearTimeout(debounceTimeout);

    debounceTimeout = setTimeout(() => {
      updatePreview();
    }, 600);
  }

  /**
   * Immediate change handler
   */
  function handleImmediateChange() {
    renderCodeSnippet();
    updatePreview();
  }

  /**
   * Switch Active Card
   */
  function switchCard(cardType) {
    if (activeCard === cardType) return;

    activeCard = cardType;

    // Update active badge header
    if (activeBadgeEndpoint) {
      activeBadgeEndpoint.textContent = CARD_ENDPOINTS[cardType] || "";
    }

    // Update tab button styles
    cardTabBtns.forEach((btn) => {
      const isCurrent = btn.dataset.card === cardType;

      if (isCurrent) {
        btn.classList.add(
          "border-purple-500",
          "bg-purple-500/10",
          "text-white",
        );

        btn.classList.remove(
          "border-zinc-800",
          "bg-zinc-900/40",
          "text-zinc-400",
        );
      } else {
        btn.classList.remove(
          "border-purple-500",
          "bg-purple-500/10",
          "text-white",
        );

        btn.classList.add("border-zinc-800", "bg-zinc-900/40", "text-zinc-400");
      }
    });

    // Toggle specific options sections
    sectionStatsOptions.classList.toggle("hidden", cardType !== "stats");
    sectionStreakOptions.classList.toggle("hidden", cardType !== "streak");
    sectionLanguagesOptions.classList.toggle(
      "hidden",
      cardType !== "languages",
    );
    sectionProfileOptions.classList.toggle('hidden', cardType !== 'profile');

    // icon_color visibility
    if (cardType === "languages") {
      rowIconColor.classList.add("hidden");
    } else {
      rowIconColor.classList.remove("hidden");
    }

    handleImmediateChange();
  }

  /**
   * Switch Export Format
   */
  function switchFormat(format) {
    activeFormat = format;

    formatTabBtns.forEach((btn) => {
      const isCurrent = btn.dataset.format === format;

      if (isCurrent) {
        btn.classList.add("bg-purple-600", "text-white", "shadow-sm");

        btn.classList.remove("text-zinc-400", "hover:text-zinc-200");
      } else {
        btn.classList.remove("bg-purple-600", "text-white", "shadow-sm");

        btn.classList.add("text-zinc-400", "hover:text-zinc-200");
      }
    });

    renderCodeSnippet();
  }

  /**
   * Copy snippet to clipboard
   */
  async function copyToClipboard() {
    const text = codeOutput.textContent;

    if (!text) return;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");

        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";

        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      copyText.textContent = "Copied!";

      btnCopyCode.classList.remove(
        "bg-zinc-100",
        "hover:bg-white",
        "text-zinc-950",
      );

      btnCopyCode.classList.add("bg-emerald-600", "text-white");

      setTimeout(() => {
        copyText.textContent = "Copy";

        btnCopyCode.classList.remove("bg-emerald-600", "text-white");

        btnCopyCode.classList.add(
          "bg-zinc-100",
          "hover:bg-white",
          "text-zinc-950",
        );
      }, 2000);
    } catch (err) {
      console.error("Failed to copy", err);
    }
  }

  /**
   * Connect color picker and text input
   */
  function bindColorPair(picker, textInput) {
    picker.addEventListener("input", () => {
      textInput.value = picker.value.replace("#", "");
      handleInputDebounced();
    });

    textInput.addEventListener("input", () => {
      const val = cleanHex(textInput.value);

      if (/^[0-9A-Fa-f]{6}$/.test(val)) {
        picker.value = "#" + val;
      }

      handleInputDebounced();
    });
  }

  /**
   * Reset form fields
   */
  function resetForm() {
    selectTheme.value = "default";

    // Stats
    if (selectStatsLocale) selectStatsLocale.value = "en";
    inputHideRank.checked = false;

    // Streak
    selectLocale.value = "en";
    inputTimezone.value = "";
    inputHideDays.checked = false;

    // Languages
    if (selectLangsLocale) selectLangsLocale.value = "en";
    inputCardTitle.value = "";
    inputHideLangs.value = "";
    inputExcludeRepos.value = "";

    // Profile
    selectProfileLocale.value = 'en';
    inputProfileTitle.value = '';

    // Colors
    inputTitleColor.value = "";
    inputTextColor.value = "";
    inputIconColor.value = "";
    inputBgColor.value = "";
    inputBorderColor.value = "";

    handleImmediateChange();
  }

  // EVENT LISTENERS

  // Card tab buttons
  cardTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => switchCard(btn.dataset.card));
  });

  // Format tab buttons
  formatTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => switchFormat(btn.dataset.format));
  });

  // URL toggle
  toggleProductionUrl.addEventListener("change", () => {
    renderCodeSnippet();
  });

  // Refresh preview button
  btnRefreshPreview.addEventListener("click", () => {
    if (!inputUsername.value.trim()) {
      usernameError.classList.remove("hidden");
      inputUsername.focus();
      return;
    }

    updatePreview();
  });

  // Copy code button
  btnCopyCode.addEventListener("click", copyToClipboard);

  // Form Reset button
  btnResetForm.addEventListener("click", resetForm);

  // Accordion for Colors
  btnToggleColors.addEventListener("click", () => {
    const isHidden = containerColors.classList.contains("hidden");

    containerColors.classList.toggle("hidden", !isHidden);

    iconColorsArrow.style.transform = isHidden
      ? "rotate(180deg)"
      : "rotate(0deg)";
  });

  // Form input listeners
  inputUsername.addEventListener("input", () => {
    if (inputUsername.value.trim()) {
      usernameError.classList.add("hidden");
    }

    handleInputDebounced();
  });

  selectTheme.addEventListener("change", handleImmediateChange);
  if (selectStatsLocale) {
    selectStatsLocale.addEventListener("change", handleImmediateChange);
  }
  selectLocale.addEventListener("change", handleImmediateChange);
  if (selectLangsLocale) {
    selectLangsLocale.addEventListener("change", handleImmediateChange);
  }
  selectProfileLocale.addEventListener('change', handleImmediateChange);

  inputHideRank.addEventListener("change", handleImmediateChange);
  inputHideDays.addEventListener("change", handleImmediateChange);

  inputTimezone.addEventListener("input", handleInputDebounced);
  inputCardTitle.addEventListener("input", handleInputDebounced);
  inputHideLangs.addEventListener("input", handleInputDebounced);
  inputExcludeRepos.addEventListener("input", handleInputDebounced);
  inputProfileTitle.addEventListener('input', handleInputDebounced);

  // Bind color pairs
  bindColorPair(pickerTitleColor, inputTitleColor);
  bindColorPair(pickerTextColor, inputTextColor);
  bindColorPair(pickerIconColor, inputIconColor);
  bindColorPair(pickerBgColor, inputBgColor);
  bindColorPair(pickerBorderColor, inputBorderColor);

  // Initial setup
  loadThemes();
  renderCodeSnippet();
})();
