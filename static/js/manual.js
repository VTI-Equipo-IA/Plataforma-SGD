// static/js/manual.js
// JS mínimo: genera TOC desde headings y resalta sección activa.

(function () {
  function slugify(text) {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s\-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/\-+/g, "-");
  }

  const content = document.querySelector(".manual-content");
  const toc = document.querySelector("#manual-toc");

  if (!content || !toc) return;

  const headings = Array.from(content.querySelectorAll("h2, h3, h4"));
  const used = new Map();

  const items = headings
    .map((h) => {
      const level = parseInt(h.tagName.replace("H", ""), 10);
      const raw = (h.textContent || "").trim();
      if (!raw) return null;

      let id = h.getAttribute("id") || slugify(raw);
      const prev = used.get(id) || 0;
      used.set(id, prev + 1);
      if (prev > 0) id = `${id}-${prev + 1}`;

      h.setAttribute("id", id);

      return { id, text: raw, level };
    })
    .filter(Boolean);

  toc.innerHTML = "";

  for (const it of items) {
    const a = document.createElement("a");
    a.href = `#${it.id}`;
    a.className = `level-${it.level}`;
    a.textContent = it.text;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const el = document.getElementById(it.id);
      if (!el) return;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", `#${it.id}`);
    });
    toc.appendChild(a);
  }

  // Resaltar sección activa con IntersectionObserver
  const links = Array.from(toc.querySelectorAll("a"));
  const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));

  function setActive(id) {
    for (const a of links) a.classList.remove("active");
    const active = byId.get(id);
    if (active) active.classList.add("active");
  }

  const observer = new IntersectionObserver(
    (entries) => {
      // Elegir el heading más visible y cercano al top
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => (a.boundingClientRect.top > b.boundingClientRect.top ? 1 : -1));

      if (visible.length > 0) {
        setActive(visible[0].target.id);
      }
    },
    { root: null, threshold: [0.2, 0.4, 0.6], rootMargin: "-10% 0px -70% 0px" }
  );

  for (const h of headings) observer.observe(h);

  // Si hay hash inicial, marcarlo
  if (location.hash) setActive(location.hash.slice(1));
})();
