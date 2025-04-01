
    document.addEventListener('DOMContentLoaded', () => {
        const courses = Array.from(document.querySelectorAll('.Course-Card-Outer-Container'));
        const itemsPerPage = document.getElementById('itemsPerPage');
        const prevPageBtn = document.getElementById('prevPage');
        const nextPageBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');

        let currentPage = 1;
        let maxItemsPerPage = parseInt(itemsPerPage.value);

        // Function to render courses for the current page
        function renderCourses() {
            const start = (currentPage - 1) * maxItemsPerPage;
            const end = start + maxItemsPerPage;

            // Hide all courses first
            courses.forEach(course => course.style.display = 'none');

            // Display only the relevant courses
            courses.slice(start, end).forEach(course => course.style.display = 'block');

            // Update pagination info
            pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(courses.length / maxItemsPerPage)}`;
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === Math.ceil(courses.length / maxItemsPerPage);
        }

        // Event Listeners for Pagination
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderCourses();
            }
        });

        nextPageBtn.addEventListener('click', () => {
            if (currentPage < Math.ceil(courses.length / maxItemsPerPage)) {
                currentPage++;
                renderCourses();
            }
        });

        // Event Listener for changing number of items per page
        itemsPerPage.addEventListener('change', (e) => {
            maxItemsPerPage = parseInt(e.target.value);
            currentPage = 1; // Reset to first page
            renderCourses();
        });

        // Initial render
        renderCourses();
    });
