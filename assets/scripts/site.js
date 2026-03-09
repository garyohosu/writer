const STORY_INDEX_PATH = "data/stories_index.json";
const DEFAULT_EMPTY_COPY = {
  title: "最初の物語を準備中です",
  summary:
    "パイプラインが公開作品を生成すると、この場所に毎日の短編がガラスカードとして並びます。",
};

function qs(selector, root = document) {
  return root.querySelector(selector);
}

function qsa(selector, root = document) {
  return [...root.querySelectorAll(selector)];
}

function formatDate(dateString) {
  const date = new Date(`${dateString}T00:00:00+09:00`);
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

function storyFilename(entry) {
  const prefix = `${entry.date}-`;
  const basename = entry.slug.startsWith(prefix) ? entry.slug : `${entry.date}-${entry.slug}`;
  return `stories/${entry.date.slice(0, 4)}/${basename}.md`;
}

async function fetchStoriesIndex() {
  try {
    const response = await fetch(STORY_INDEX_PATH, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    return [];
  }
}

function createTagPill(tag) {
  const span = document.createElement("span");
  span.className = "tag-pill";
  span.textContent = `#${tag}`;
  return span;
}

function createStoryCard(entry, options = {}) {
  const article = document.createElement("article");
  article.className = "story-card tilt-card";
  article.dataset.aos = "fade-up";
  if (options.delay) {
    article.dataset.aosDelay = `${options.delay}`;
  }

  const tags = Array.isArray(entry.tags) ? entry.tags.slice(0, 3) : [];
  article.innerHTML = `
    <div class="story-card-header">
      <div class="story-card-date">${formatDate(entry.date)}</div>
      <div class="story-card-score">Score ${entry.review_score ?? "--"}</div>
    </div>
    <div>
      <h3>${entry.title}</h3>
      <p>${entry.summary ?? ""}</p>
    </div>
    <div class="card-meta">
      <span><i class="fa-regular fa-clock"></i> ${entry.reading_time_min ?? "-"} min</span>
      <span><i class="fa-regular fa-file-lines"></i> ${entry.character_count ?? "-"} chars</span>
    </div>
    <div class="tag-row"></div>
    <div class="story-card-footer">
      <a class="story-link" href="story.html?slug=${encodeURIComponent(entry.slug)}">
        読む <i class="fa-solid fa-arrow-right"></i>
      </a>
      <span class="story-card-date">${entry.slug}</span>
    </div>
  `;

  const tagRow = qs(".tag-row", article);
  tags.forEach((tag) => tagRow.appendChild(createTagPill(tag)));
  return article;
}

function createEmptyCard() {
  const article = document.createElement("article");
  article.className = "empty-card glass-panel";
  article.dataset.aos = "fade-up";
  article.innerHTML = `
    <span class="eyebrow">Coming Soon</span>
    <h3>${DEFAULT_EMPTY_COPY.title}</h3>
    <p>${DEFAULT_EMPTY_COPY.summary}</p>
    <div class="tag-row">
      <span class="tag-pill">#Daily</span>
      <span class="tag-pill">#Plot</span>
      <span class="tag-pill">#Review</span>
    </div>
  `;
  return article;
}

function splitHeroTitle() {
  const title = qs("#hero-title");
  if (!title || !window.gsap) {
    return;
  }
  const letters = [...title.textContent];
  title.innerHTML = letters
    .map((char) =>
      char === " "
        ? '<span class="hero-letter">&nbsp;</span>'
        : `<span class="hero-letter">${char}</span>`
    )
    .join("");

  window.gsap.from(".hero-letter", {
    y: 50,
    opacity: 0,
    duration: 0.8,
    stagger: 0.035,
    ease: "power3.out",
    delay: 0.2,
  });
}

function initAOS() {
  if (window.AOS) {
    window.AOS.init({
      duration: 850,
      once: true,
      offset: 40,
      easing: "ease-out-cubic",
    });
  }
}

function refreshAOS() {
  if (window.AOS) {
    window.AOS.refreshHard();
  }
}

function initTilt() {
  if (window.VanillaTilt) {
    window.VanillaTilt.init(qsa(".tilt-card"), {
      max: 10,
      speed: 500,
      glare: true,
      "max-glare": 0.15,
      scale: 1.01,
    });
  }
}

function pushAds() {
  qsa(".adsbygoogle").forEach((node) => {
    if (node.dataset.adInitialized === "true") {
      return;
    }
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      node.dataset.adInitialized = "true";
    } catch (error) {
      node.dataset.adInitialized = "true";
    }
  });
}

function updateThemeIcon(button) {
  const icon = qs("i", button);
  if (!icon) {
    return;
  }
  icon.className = document.body.classList.contains("light-mode")
    ? "fa-solid fa-sun"
    : "fa-solid fa-moon";
}

function createThemeRipple(x, y) {
  const ripple = document.createElement("span");
  ripple.style.position = "fixed";
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
  ripple.style.width = "12px";
  ripple.style.height = "12px";
  ripple.style.borderRadius = "999px";
  ripple.style.pointerEvents = "none";
  ripple.style.background = "rgba(255, 179, 71, 0.35)";
  ripple.style.transform = "translate(-50%, -50%) scale(1)";
  ripple.style.transition = "transform 0.7s ease, opacity 0.7s ease";
  ripple.style.zIndex = "999";
  document.body.appendChild(ripple);
  requestAnimationFrame(() => {
    ripple.style.transform = "translate(-50%, -50%) scale(42)";
    ripple.style.opacity = "0";
  });
  window.setTimeout(() => ripple.remove(), 750);
}

function initThemeToggle() {
  const button = qs(".theme-toggle");
  if (!button) {
    return;
  }
  const key = "daily-story-theme";
  const stored = window.localStorage.getItem(key);
  if (stored === "light") {
    document.body.classList.add("light-mode");
  }
  updateThemeIcon(button);

  button.addEventListener("click", (event) => {
    document.body.classList.toggle("light-mode");
    window.localStorage.setItem(
      key,
      document.body.classList.contains("light-mode") ? "light" : "dark"
    );
    updateThemeIcon(button);
    createThemeRipple(event.clientX, event.clientY);
  });
}

function initStoryNavHide() {
  if (document.body.dataset.page !== "story") {
    return;
  }
  const nav = qs(".story-nav");
  if (!nav) {
    return;
  }
  let lastY = window.scrollY;
  window.addEventListener("scroll", () => {
    const current = window.scrollY;
    if (current > 140 && current > lastY + 8) {
      nav.classList.add("nav-hidden");
    } else {
      nav.classList.remove("nav-hidden");
    }
    lastY = current;
  });
}

function updateReadingProgress() {
  const progress = qs("#reading-progress");
  const storyContent = qs("#story-content");
  if (!progress || !storyContent) {
    return;
  }
  const total = storyContent.offsetHeight - window.innerHeight;
  const current = window.scrollY - (storyContent.offsetTop - 120);
  const ratio = total <= 0 ? 0 : Math.min(1, Math.max(0, current / total));
  progress.style.width = `${ratio * 100}%`;

  if (ratio > 0.98 && !document.body.dataset.confettiShown) {
    document.body.dataset.confettiShown = "true";
    if (typeof window.confetti === "function") {
      window.confetti({
        particleCount: 70,
        spread: 70,
        origin: { y: 0.7 },
        colors: ["#ffb347", "#ffe4a4", "#7b92ff"],
      });
    }
  }
}

async function renderHome(stories) {
  const grid = qs("#featured-grid");
  const cta = qs("#hero-primary");
  if (!grid) {
    return;
  }
  if (!stories.length) {
    grid.appendChild(createEmptyCard());
    if (cta) {
      cta.setAttribute("href", "archive.html");
      cta.textContent = "公開準備中の棚を見る";
    }
    initTilt();
    refreshAOS();
    return;
  }

  stories.slice(0, 6).forEach((story, index) => {
    grid.appendChild(createStoryCard(story, { delay: 100 + index * 100 }));
  });
  if (cta) {
    cta.setAttribute("href", `story.html?slug=${encodeURIComponent(stories[0].slug)}`);
  }
  initTilt();
  refreshAOS();
}

async function renderArchive(stories) {
  const grid = qs("#archive-grid");
  if (!grid) {
    return;
  }
  if (!stories.length) {
    grid.appendChild(createEmptyCard());
    return;
  }
  stories.forEach((story, index) => {
    grid.appendChild(createStoryCard(story, { delay: 80 + index * 60 }));
  });
  initTilt();
  refreshAOS();
}

function renderTags(stories) {
  const cloud = qs("#tag-cloud");
  const results = qs("#tag-results");
  if (!cloud || !results) {
    return;
  }

  const tagMap = new Map();
  stories.forEach((story) => {
    (story.tags || []).forEach((tag) => {
      tagMap.set(tag, (tagMap.get(tag) || 0) + 1);
    });
  });

  if (!tagMap.size) {
    results.appendChild(createEmptyCard());
    return;
  }

  const allButton = document.createElement("button");
  allButton.className = "active";
  allButton.type = "button";
  allButton.textContent = "All";
  cloud.appendChild(allButton);

  [...tagMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .forEach(([tag, count]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `${tag} (${count})`;
      button.dataset.tag = tag;
      cloud.appendChild(button);
    });

  const draw = (selectedTag = null) => {
    results.innerHTML = "";
    const filtered = selectedTag
      ? stories.filter((story) => (story.tags || []).includes(selectedTag))
      : stories;
    filtered.forEach((story, index) => {
      results.appendChild(createStoryCard(story, { delay: 80 + index * 80 }));
    });
    initTilt();
    refreshAOS();
  };

  cloud.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }
    qsa("button", cloud).forEach((node) => node.classList.remove("active"));
    button.classList.add("active");
    draw(button.dataset.tag || null);
  });

  draw();
}

function parseStoryMarkdown(markdown) {
  const normalized = markdown.replace(/\r\n/g, "\n");
  if (!normalized.startsWith("---\n")) {
    return { frontMatter: {}, body: normalized };
  }
  const parts = normalized.split("\n---\n");
  if (parts.length < 2) {
    return { frontMatter: {}, body: normalized };
  }
  const frontMatter = window.jsyaml ? window.jsyaml.load(parts[0].replace(/^---\n/, "")) : {};
  return {
    frontMatter: frontMatter || {},
    body: parts.slice(1).join("\n---\n").trim(),
  };
}

function enrichStoryParagraphs(container) {
  qsa("p", container).forEach((paragraph, index) => {
    paragraph.dataset.aos = "fade-up";
    paragraph.dataset.aosDelay = `${80 + index * 40}`;
  });
}

async function renderStory(stories) {
  const slug = new URLSearchParams(window.location.search).get("slug");
  const content = qs("#story-content");
  const title = qs("#story-title");
  const summary = qs("#story-summary");
  const meta = qs("#story-meta");
  const tags = qs("#story-tags");
  const related = qs("#related-grid");
  if (!slug || !content || !title || !summary || !meta || !tags || !related) {
    return;
  }

  const story = stories.find((entry) => entry.slug === slug);
  if (!story) {
    title.textContent = "作品が見つかりません";
    summary.textContent = "指定された slug の作品はまだ公開されていません。";
    content.innerHTML = "<p>公開後に再度お試しください。</p>";
    return;
  }

  title.textContent = story.title;
  summary.textContent = story.summary || "";
  meta.innerHTML = `
    <span><i class="fa-regular fa-calendar"></i> ${formatDate(story.date)}</span>
    <span><i class="fa-regular fa-clock"></i> ${story.reading_time_min ?? "-"} min</span>
    <span><i class="fa-regular fa-file-lines"></i> ${story.character_count ?? "-"} chars</span>
    <span><i class="fa-regular fa-star"></i> Score ${story.review_score ?? "--"}</span>
  `;
  (story.tags || []).forEach((tag) => tags.appendChild(createTagPill(tag)));

  try {
    const response = await fetch(storyFilename(story), { cache: "no-store" });
    if (!response.ok) {
      throw new Error("story not found");
    }
    const markdown = await response.text();
    const parsed = parseStoryMarkdown(markdown);
    const rawHtml = window.marked ? window.marked.parse(parsed.body) : `<p>${parsed.body}</p>`;
    content.innerHTML = rawHtml;
    enrichStoryParagraphs(content);
    refreshAOS();
    document.title = `${story.title} | Daily Short Story`;
  } catch (error) {
    content.innerHTML = "<p>本文の取得に失敗しました。しばらくしてから再度お試しください。</p>";
  }

  stories
    .filter((entry) => entry.slug !== slug)
    .slice(0, 3)
    .forEach((entry, index) => {
      related.appendChild(createStoryCard(entry, { delay: 90 + index * 90 }));
    });
  if (!related.children.length) {
    related.appendChild(createEmptyCard());
  }

  initTilt();
  window.addEventListener("scroll", updateReadingProgress, { passive: true });
  updateReadingProgress();
}

async function initPage() {
  initThemeToggle();
  initAOS();
  splitHeroTitle();
  initStoryNavHide();

  const stories = await fetchStoriesIndex();
  const page = document.body.dataset.page;

  if (page === "home") {
    await renderHome(stories);
  } else if (page === "archive") {
    await renderArchive(stories);
  } else if (page === "tags") {
    renderTags(stories);
  } else if (page === "story") {
    await renderStory(stories);
  }

  pushAds();
}

document.addEventListener("DOMContentLoaded", initPage);
