// Compact — a page plugin for the hub (EXTENDING.md, API 1.1).
// A redesign layer over the hub page: density comes from spacing and structure, never from smaller type.
// Everything is scoped under html.cx, so removing the class (or the plugin) restores the stock page.
// The plugin changes no hub state and no DOM the hub or other plugins own; it only restyles.

export default function register(hub) {
  const root = document.documentElement;
  root.style.setProperty("--cx-agent", `url("${hub.url("icons/agent.svg")}")`);
  root.style.setProperty("--cx-menu", `url("${hub.url("icons/menu.svg")}")`);
  hub.addStyle("compact.css");
  root.classList.add("cx");
}
