

    document.addEventListener("DOMContentLoaded", function () {
        const listItem = document.querySelector(".action-buttons .push.primary");
        const dropdownMenu = document.querySelector("ui-pane");

        if (!listItem || !dropdownMenu) return; // Prevent errors if elements are missing

        // Set initial state: Default (hidden dropdown, green text, transparent background)
        listItem.dataset.state = "List-Default";
        listItem.style.color = getComputedStyle(document.documentElement).getPropertyValue('--theme-color-gray3').trim();
        listItem.style.backgroundColor = "transparent";
        dropdownMenu.style.visibility = "hidden";
        dropdownMenu.style.opacity = "0";
        dropdownMenu.style.display = "none";

        // Hover Effect: Background changes but state does not change
        listItem.addEventListener("mouseenter", function () {
            if (listItem.dataset.state === "List-Default") {
                listItem.style.backgroundColor = "hsl(240, 5.7%, 82.9%)"; // Apply the background color

            }
        });

        listItem.addEventListener("mouseleave", function () {
            if (listItem.dataset.state === "List-Default") {
                listItem.style.backgroundColor = "transparent";
            }
        });

        // Click Event: Toggle between List-Default and List-Open
        listItem.addEventListener("click", function () {
            if (listItem.dataset.state === "List-Default") {
                // Switch to Open State
                listItem.dataset.state = "List-Open";
                listItem.style.color = "white";
                listItem.style.backgroundColor = "hsl(240, 4.7%, 79.0%)";
                dropdownMenu.style.display = "block";
                setTimeout(() => {
                    dropdownMenu.style.visibility = "visible";
                    dropdownMenu.style.opacity = "1";
                }, 10);
            } else {
                // Switch back to Default State
                listItem.dataset.state = "List-Default";
                listItem.style.color = getComputedStyle(document.documentElement).getPropertyValue('--theme-color-gray3').trim();
                listItem.style.backgroundColor = "transparent";
                dropdownMenu.style.visibility = "hidden";
                dropdownMenu.style.opacity = "0";
                dropdownMenu.style.display = "none";
            }
        });
    });



