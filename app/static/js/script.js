document.addEventListener("DOMContentLoaded", function () {

    // Theme management (the saved theme is applied in <head> to avoid a flash)
    const themeButton = document.getElementById("theme");
    const html = document.documentElement;

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

        // "/" and "/dashboard" must match exactly; other sections match by prefix
        const exactOnly = linkPath === "/" || linkPath === "/dashboard";

        const isActive = exactOnly
            ? linkPath === currentPath
            : currentPath.startsWith(linkPath);

        if (isActive) {
            link.classList.add("active");
        }

    });


    // Auto-dismiss success / info flash messages after 5 seconds
    document
        .querySelectorAll(".flash-messages .alert-success, .flash-messages .alert-info")
        .forEach(function (alertEl) {
            setTimeout(function () {
                bootstrap.Alert.getOrCreateInstance(alertEl).close();
            }, 5000);
        });

});