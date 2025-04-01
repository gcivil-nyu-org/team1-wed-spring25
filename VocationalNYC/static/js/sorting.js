const dropdown = document.getElementById('SortByDropDown')
                                    dropdown.addEventListener('change',sortby);
                                    document.querySelector('.toggle-container').addEventListener('click', toggleArrow);
                                    function toggleArrow() {
                                        const arrow = document.querySelector('.arrow');
                                        // Check if the arrow has the 'up' class
                                        if (arrow.classList.contains('arrow-up')) {
                                            // Arrow is currently pointing up, toggle it to down
                                            arrow.classList.remove('arrow-up');
                                            arrow.classList.add('arrow-down');
                                            sortby();
                                        } else {
                                            // Arrow is currently pointing down, toggle it to up
                                            arrow.classList.remove('arrow-down');
                                            arrow.classList.add('arrow-up');
                                            sortby();

                                        }

                                    }
                                    function sortby(){
                                        const sort = document.getElementById("SortByDropDown").value;
                                        const arrow = document.querySelector('.arrow')
                                        const order = arrow.classList.contains('arrow-up') ? "asc" : "desc";
                                        const currentUrl = new URL(window.location.href);
                                        const queryParams = new URLSearchParams(window.location.search);
                                        queryParams.set("order", order);
                                        queryParams.set("sort", sort);
                                        console.log(`Search by ${queryParams.toString()}`);
                                        fetch(`/courses/sort/?${queryParams.toString()}`, {
                                            method: 'GET',
                                            headers: {
                                                "X-Requested-With": "XMLHttpRequest", // Required for Django to recognize AJAX requests
                                            },
                                        })
                                            .then(response => response.text()) // Parse response as text (HTML)
                                            .then(html => {
                                                document.getElementById("All-Course-Container").innerHTML = html;
                                                initializeListeners(); // Reinitialize event listeners after update
                                            })
                                            .catch(error => console.error('Error:', error)); // Handle errors
                                    }
                                    function initializeListeners() {
                                        document.querySelector('.toggle-container').addEventListener('click', toggleArrow);
                                        const dropdown = document.getElementById("SortByDropDown");
                                        dropdown.addEventListener("change", sortby);
                                    }
                                    document.addEventListener("DOMContentLoaded", initializeListeners);