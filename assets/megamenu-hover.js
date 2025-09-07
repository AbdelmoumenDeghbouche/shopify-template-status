document.addEventListener("DOMContentLoaded", function () {
  const menuItems = document.querySelectorAll(".header__inline-menu > ul > li");
  let activeMenuItem = null;

  menuItems.forEach((item) => {
    const detailsElement = item.querySelector("details");
    if (!detailsElement) return;

    item.addEventListener("mouseenter", () => {
      if (activeMenuItem && activeMenuItem !== item) {
        const previousDetailsElement = activeMenuItem.querySelector("details");
        if (previousDetailsElement) {
          previousDetailsElement.removeAttribute("open");
        }
      }
      detailsElement.setAttribute("open", true);
      activeMenuItem = item;
    });

    item.addEventListener("mouseleave", () => {
      setTimeout(() => {
        if (!item.matches(":hover")) {
          detailsElement.removeAttribute("open");
          if (activeMenuItem === item) activeMenuItem = null;
        }
      }, 500); // Adjust delay as needed
    });
  });
});
