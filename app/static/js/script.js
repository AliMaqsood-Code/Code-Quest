document.addEventListener("DOMContentLoaded", function () {

    // Theme management
    const themeButton = document.getElementById("theme");
    const html = document.documentElement;

    const savedTheme = localStorage.getItem("cq-theme") || "light";

    html.setAttribute("data-bs-theme", savedTheme);

    function updateThemeIcon() {
        if (themeButton) {
            themeButton.textContent =
                html.getAttribute("data-bs-theme") === "dark" ? "☀" : "☾";
        }
    }

    updateThemeIcon();

    if (themeButton) {
        themeButton.addEventListener("click", function () {

            const currentTheme = html.getAttribute("data-bs-theme");

            const newTheme = currentTheme === "dark" ? "light" : "dark";

            html.setAttribute("data-bs-theme", newTheme);

            localStorage.setItem("cq-theme", newTheme);

            updateThemeIcon();
        });
    }


    // Mobile sidebar
    const menuButton = document.getElementById("menu");
    const sidebar = document.getElementById("side");

    if (menuButton && sidebar) {

        menuButton.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", function (event) {

            if (
                !sidebar.contains(event.target) &&
                !menuButton.contains(event.target)
            ) {
                sidebar.classList.remove("open");
            }

        });

    }


    // Active sidebar link
    const currentPath = window.location.pathname;

    const sidebarLinks = document.querySelectorAll("#links a");

    sidebarLinks.forEach(function (link) {

        const linkPath = new URL(link.href).pathname;

        if (
            linkPath === currentPath ||
            (linkPath !== "/" && currentPath.startsWith(linkPath))
        ) {
            link.classList.add("active");
        }

    });


    // Global search - basic Enter handling
    const searchInput = document.getElementById("global-search");

    if (searchInput) {

        searchInput.addEventListener("keydown", function (event) {

            if (event.key === "Enter") {

                const query = searchInput.value.trim();

                if (query) {
                    window.location.href =
                        "/problems/?search=" + encodeURIComponent(query);
                }

            }

        });

    }

});