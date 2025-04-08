document.addEventListener("DOMContentLoaded", function () {
    const dropdown = document.getElementById("SortByDropDown");

    function sortby() {
        const selected = dropdown.value;
        if (selected === "blank") return;

        const [field, direction] = selected.split("-");
        const queryParams = new URLSearchParams(window.location.search);
        queryParams.set("sort", field);      // e.g., "name"
        queryParams.set("order", direction); // e.g., "asc" or "desc"

        fetch(`/courses/sort/?${queryParams.toString()}`, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
        .then(response => response.text())
        .then(html => {
            document.getElementById("All-Course-Container").innerHTML = html;
            initializeListeners(); // rebind dropdown
            reinitializePagination();
        })
        .catch(error => console.error("Sorting error:", error));
    }

    function initializeListeners() {
        dropdown.removeEventListener("change", sortby);
        dropdown.addEventListener("change", sortby);
    }

    initializeListeners();
});
