const sgInitialTheme = localStorage.getItem("theme") === "light" ? "light" : "dark"
document.documentElement.setAttribute("data-theme", sgInitialTheme)
document.querySelector("#theme-color-meta")?.setAttribute("content", sgInitialTheme === "light" ? "#f4f4f5" : "#18181b")
